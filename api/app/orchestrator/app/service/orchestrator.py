from dotenv import load_dotenv
import os
from fastapi import UploadFile
from app.logging_config import logging
import requests
from app.service.indentifier import TypeIdentifier, SubjectIdentifier
from app.service.strategies.type_strategy import LibroStrategy,TesisStrategy,ArticuloStrategy,ObjectConferenceStrategy,GeneralStrategy
from app.service.pattern_extractors import extract_abstract, extract_keywords_regex, extract_keywords_tfidf, load_vectorizer
import io
from typing import Tuple, Optional, Union
from app.constants.constant import PROMPT_DEEPANALYZE, MAX_WORDS_NO_TAGS, MAX_WORDS_WITH_TAGS
import json
import re

class Orchestrator:
    def __init__(self):
        load_dotenv()
        self.extractor_service_url = os.getenv("EXTRACTOR_URL")
        self.extractor_service_api_key = os.getenv("EXTRACTOR_TOKEN")
        self.llm_deepanalyze_url = os.getenv("LLM_DEEPANALYZE_URL")
        self.llm_deepanalyze_api_key = os.getenv("LLM_DEEPANALYZE_TOKEN")
        self.logger = logging.getLogger(__name__)
        self.type_identifier = TypeIdentifier(
            path_clf=os.getenv("IDENTIFIER_PATH_MODEL"),
            path_vectorizer=os.getenv("IDENTIFIER_PATH_VECTORIZER"),
            path_label_encoder=os.getenv("IDENTIFIER_PATH_LABEL_ENCODER")
        )
        self.subject_identifier = SubjectIdentifier(
            path_classifier=os.getenv("SUBJECT_IDENTIFIER_PATH_CLASSIFIER", "models/svm_classifier.pkl"),
            path_vectorizer=os.getenv("SUBJECT_IDENTIFIER_PATH_VECTORIZER", "models/svm_vectorizer.pkl"),
            path_label_encoder=os.getenv("SUBJECT_IDENTIFIER_PATH_LABEL_ENCODER", "models/svm_label_encoder.pkl")
        )

        vectorizer_path = os.getenv("TFIDF_VECTORIZER_PATH", "app/models/tfidf_vectorizer.pkl")
        self.vectorizer = load_vectorizer(vectorizer_path)
        if self.vectorizer is not None:
            self.logger.info(f"TF-IDF vectorizer loaded from: {vectorizer_path}")
        else:
            self.logger.warning(f"TF-IDF vectorizer not found at: {vectorizer_path} — tfidf keywords disabled")

        self.logger.info("Orchestrator service is up")
        self.logger.info(f"Extractor service url: {self.extractor_service_url}")


    @staticmethod
    def _get_headers(api_key: str) -> dict: 
        return {
            "Authorization": f"Bearer {api_key}"
        }

    @staticmethod
    def _error_response_extractor(error: str, response_extractor: str) -> dict:
                return {
                    "error": error,
                    "detail": response_extractor.text,
                    "code": response_extractor.status_code
                }


    @staticmethod
    def _shorten_text(text):
        return " ".join(text.split()[:500])

    @staticmethod
    def _remove_honorifics(text):
        if not isinstance(text, str):
            return text
        
        # Lista de títulos honoríficos a remover
        honorifics = [
            r'\bdr\.\s*', r'\bdra\.\s*', r'\bdrª\.\s*',
            r'\blic\.\s*', r'\blica\.\s*', r'\blicª\.\s*',
            r'\bing\.\s*', r'\binga\.\s*', r'\bingª\.\s*',
            r'\bmg\.\s*', r'\bmgr\.\s*', r'\bmgs\.\s*', r'\bmgtr\.\s*',
            r'\bmag\.\s*', r'\bmsc\.\s*',
            r'\bphd\.\s*', r'\bph\.d\.\s*',
            r'\bprof\.\s*', r'\bprofa\.\s*', r'\bprofª\.\s*',
            r'\bsr\.\s*', r'\bsra\.\s*', r'\bsrª\.\s*',
            r'\bmr\.\s*', r'\bmrs\.\s*', r'\bms\.\s*',
            r'\bdir\.\s*', r'\bdira\.\s*', r'\bdirª\.\s*',
            r'\bcodir\.\s*', r'\bcodira\.\s*', r'\bcodirª\.\s*',
            r'\bcoord\.\s*',
            r'\bcolab\.\s*',
            r'\bcolaborador\b\s*', r'\bcolaboradora\b\s*',
            r'\bagr\.\s*', r'\bagra\.\s*',
            r'\barq\.\s*', r'\barqa\.\s*',
            r'\besp\.\s*',
            r'\babog\.\s*',
            r'\bcdor\.\s*', r'\bcdora\.\s*', r'\bcra\.\s*',
            r'\bmed\.\s*',
            r'\bvet\.\s*', r'\bmv\.\s*',
            r'\bzoot\.\s*',
            r'\bfarm\.\s*',
            r'\bpsic\.\s*',
            r'\bgeof\.\s*',
            r'\bftal\.\s*',
            r'\bsc\.\s*',
            r'\bec\.\s*',
            r'\btec\.\s*', r'\btéc\.\s*',
            r'\bbio\.\s*', r'\bbiol\.\s*',
            r'\bdoctor\b\s*', r'\bdoctora\b\s*',
            # Parenthesised institutional suffixes, e.g. (FCAyF-UNLP), (COORDINADOR)
            r'\s*\([^)]{1,80}\)\s*',
            # Legacy parenthesised role patterns
            r'\(dir\.\)\s*', r'\(dra\.\)\s*', r'\(drª\.\)\s*',
            r'\(codir\.\)\s*', r'\(codira\.\)\s*', r'\(codirª\.\)\s*',
            r'\(lic\.\)\s*', r'\(lica\.\)\s*', r'\(licª\.\)\s*',
            r'\(ing\.\)\s*', r'\(inga\.\)\s*', r'\(ingª\.\)\s*',
        ]
        
        text_cleaned = text
        for honorific in honorifics:
            text_cleaned = re.sub(honorific, '', text_cleaned, flags=re.IGNORECASE)
        
        # Limpiar espacios extra
        text_cleaned = re.sub(r'\s+', ' ', text_cleaned).strip()
        # Remover punto final suelto (e.g. "Leandro Adrián." → "Leandro Adrián")
        text_cleaned = re.sub(r'\.\s*$', '', text_cleaned).strip()
        return text_cleaned

    def _clean_metadata_honorifics(self, metadata: dict) -> dict:
        """Clean honorific titles from metadata fields that contain names"""
        # Fields that typically contain names and should be cleaned
        name_fields = ['creator', 'director', 'codirector', 'compiler', 'editor']

        for field in name_fields:
            if field in metadata:
                if isinstance(metadata[field], list):
                    # Clean each item in the list
                    metadata[field] = [self._remove_honorifics(item) for item in metadata[field]]
                elif isinstance(metadata[field], str):
                    # Clean the string directly
                    metadata[field] = self._remove_honorifics(metadata[field])

        return metadata

    @staticmethod
    def _deduplicate_field(value):
        """If value is a str, return as-is. If list, return list with duplicates removed (case-insensitive)."""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            seen = set()
            result = []
            for item in value:
                key = item.strip().lower() if isinstance(item, str) else item
                if key not in seen:
                    seen.add(key)
                    result.append(item)
            return result
        return value

    def _deduplicate_person_fields(self, metadata: dict) -> dict:
        for field in ('creator', 'director', 'codirector', 'publisher', 'editor'):
            if field in metadata:
                metadata[field] = self._deduplicate_field(metadata[field])
        return metadata

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize a person name:
        - Remove invalid chars: keep unicode letters, spaces, dots, apostrophes and backticks.
        - Capitalize: first letter of each word uppercase, rest lowercase.
          Special case: pure initials like 'L.' or 'A.B.' keep each letter uppercase.
        """
        if not isinstance(name, str):
            return name

        # Remove invalid characters: keep unicode letters, whitespace, dot, apostrophe, backtick
        cleaned = re.sub(r"[^\w\s.'`]|[\d_]", '', name, flags=re.UNICODE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        def capitalize_token(token: str) -> str:
            # Pure initials: one or more (letter + dot) e.g. "L.", "A.B."
            if re.fullmatch(r'([^\W\d_]\.)+', token, flags=re.UNICODE):
                return re.sub(r'[^\W\d_]', lambda m: m.group().upper(), token, flags=re.UNICODE)
            # Normal word: first letter upper, rest lower; non-letter chars (apostrophe, backtick, dot) kept as-is
            result = []
            first_letter_done = False
            for ch in token:
                if re.match(r'[^\W\d_]', ch, re.UNICODE):
                    result.append(ch.upper() if not first_letter_done else ch.lower())
                    first_letter_done = True
                else:
                    result.append(ch)
            return ''.join(result)

        return ' '.join(capitalize_token(t) for t in cleaned.split(' ') if t)

    def _normalize_person_fields(self, metadata: dict) -> dict:
        for field in ('creator', 'director', 'codirector', 'publisher', 'editor'):
            if field not in metadata:
                continue
            value = metadata[field]
            if isinstance(value, str):
                metadata[field] = self._normalize_name(value)
            elif isinstance(value, list):
                metadata[field] = [self._normalize_name(item) for item in value]
        return metadata

    @staticmethod
    def _validate_field_formats(metadata: dict) -> dict:
        """
        Post-processing validation of field formats.
        If a field value doesn't match its expected format, remove it.
        This guards against hallucinations like issn: '12-11-2020'.
        """
        # ISSN: exactly XXXX-XXXX (4 digits, hyphen, 4 alphanumeric for check digit)
        if "issn" in metadata:
            if not re.fullmatch(r'\d{4}-[\dXx]{4}', str(metadata.get("issn", ""))):
                del metadata["issn"]

        # ISBN: 10 or 13 digits, optionally hyphenated
        if "isbn" in metadata:
            isbn_digits = re.sub(r'[-\s]', '', str(metadata.get("isbn", "")))
            if not re.fullmatch(r'[\dXx]{10}|[\dXx]{13}', isbn_digits):
                del metadata["isbn"]

        # date: YYYY or YYYY/MM or YYYY/MM/DD
        if "date" in metadata:
            date_val = str(metadata.get("date", ""))
            if not re.fullmatch(r'\d{4}|\d{4}/\d{2}|\d{4}/\d{2}/\d{2}', date_val):
                del metadata["date"]

        # Remove fields that should never appear in model output
        for field in ("dc.type", "isRelatedWith", "isrelatedwith", "sedici.uri", "dc.uri"):
            metadata.pop(field, None)

        return metadata

    @staticmethod
    def _validate_identifiers_in_text(metadata: dict, text: str) -> dict:
        """
        Validate that ISSN/ISBN values actually appear in the extracted text.
        If a value is present in metadata but not found in the text, set it to None.
        """
        if not text:
            return metadata

        # ISSN: check if exact value (e.g. "1234-5678") appears in text
        if metadata.get("issn"):
            if str(metadata["issn"]) not in text:
                metadata["issn"] = None

        # ISBN: compare both raw and digit-only forms (handles hyphenation differences)
        if metadata.get("isbn"):
            isbn_raw = str(metadata["isbn"])
            isbn_digits = re.sub(r'[-\s]', '', isbn_raw)
            text_digits = re.sub(r'[-\s]', '', text)
            if isbn_raw not in text and isbn_digits not in text_digits:
                metadata["isbn"] = None

        return metadata

    def _extract_text(self, file_bytes: bytes, filename: str, content_type: str, normalization: bool, ocr: bool = False) -> Tuple[Optional[str], Optional[dict]]:
        self.logger.info("calling extractor service only text")
        stream = io.BytesIO(file_bytes)
        payload = (filename, stream, content_type)

        response_extractor = requests.post(
            self.extractor_service_url + "/extract",
            headers=self._get_headers(api_key=self.extractor_service_api_key),
            files={"file": payload},
            data={"normalization": normalization, "ocr": ocr, "max_words": MAX_WORDS_NO_TAGS}
        )

        extractor_json = response_extractor.json()
        if response_extractor.status_code != 200:
            self.logger.error(f"Extractor error: {extractor_json['error']}")
            error_response = {
                "error": extractor_json["error"]["message"]
            }, extractor_json["error"]["code"]
            return None, error_response

        plain_text = extractor_json["data"].get("text")
        return plain_text, None


    def call_deepanalyze(self, text: str, metadata: dict) -> Tuple[dict, Optional[int]]:
        headers = {
            "Authorization": f"Bearer {self.llm_deepanalyze_api_key}",
            "Content-Type": "application/json"
        }
        self.logger.info(f"calling llm service url: {self.llm_deepanalyze_url}/consume-llm")

        fields_str = "\n".join([f"{key}: {metadata[key]}" for key in metadata])
        input = f"""{PROMPT_DEEPANALYZE}{fields_str}[FIN METADATOS A VALIDAR]```
        [TEXTO]: {text} [FIN TEXTO]"""

        response_llm = requests.post(
            self.llm_deepanalyze_url + "/consume-llm",
            headers=headers,
            json={"text": input}
        )

        response_json = response_llm.json()

        if response_llm.status_code != 200:
            self.logger.error(f"LLM error: {response_json['error']}")
            return response_json, response_json["error"]["code"]

        return response_json["data"], None        

    @staticmethod
    def _get_file_payload(file: UploadFile)  -> Tuple[dict, Optional[int]]:
        file_bytes = file.file.read()
        file_stream = io.BytesIO(file_bytes)
        # seek to the beginning of the stream to allow reading from it again
        file_stream.seek(0)
        return file.filename, file_stream, file.content_type

    def orchestrate(self, file: UploadFile, normalization: bool = True, type: str = None, deepanalyze: bool = False, ocr: bool = False) -> Tuple[dict, Optional[int]]:
        self.logger.info(f"Orchestrating file: {file.filename} with normalization={normalization}, ocr={ocr}")
        try:
            file_bytes = file.file.read()
            filename = file.filename
            content_type = file.content_type

            # step 1: extract text for subject and type prediction
            plain_text, error_response = self._extract_text(file_bytes, filename, content_type, normalization, ocr)
            if error_response is not None:
                return error_response

            # predict subject (always needed)
            self.logger.info("calling predictor subject")
            subject = self.subject_identifier.predecir_subject(plain_text)

            # step 2: detect type if not sent
            if type is None:
                self.logger.info("calling predictor dc type")
                dc_type = self.type_identifier.predecir_tipo_documento(plain_text)
            else:
                dc_type = type

            # step 3: extract with tags
            self.logger.info("calling extractor service with tags")
            stream2 = io.BytesIO(file_bytes)
            payload2 = (filename, stream2, content_type)

            response_extractor_with_tags = requests.post(
                self.extractor_service_url + "/extract-with-tags",
                headers=self._get_headers(api_key=self.extractor_service_api_key),
                files={"file": payload2},
                data={"normalization": normalization, "ocr": ocr, "max_words": MAX_WORDS_WITH_TAGS}
            )

            extractor_with_tags_json = response_extractor_with_tags.json()
            if response_extractor_with_tags.status_code != 200:
                self.logger.error(f"Extractor error: {extractor_with_tags_json['error']}")
                return {
                    "error": extractor_with_tags_json["error"]["message"]  # <- ya es un string
                }, extractor_with_tags_json["error"]["code"]

            extracted_text_with_metadata = extractor_with_tags_json["data"].get("text")

            dc_type = dc_type.lower()
            # step 4: apply strategy by type
            strategies = {
                "libro": LibroStrategy,
                "articulo": ArticuloStrategy,
                "tesis": TesisStrategy,
                "objeto de conferencia": ObjectConferenceStrategy,
                "general": GeneralStrategy,
            }

            strategy_class = strategies.get(dc_type, GeneralStrategy)
            strategy = strategy_class()
            self.logger.info(f"Calling {strategy_class.__name__}")
            metadata, error = strategy.get_metadata(extracted_text_with_metadata)
            metadata["type"] = dc_type
            metadata["subject"] = subject
            if error is None and deepanalyze:
                metadata, error = self.call_deepanalyze(self._shorten_text(extracted_text_with_metadata), metadata)
            
            # Clean honorific titles from name fields before returning
            if error is None:
                metadata = self._clean_metadata_honorifics(metadata)
                metadata = self._deduplicate_person_fields(metadata)
                metadata = self._normalize_person_fields(metadata)
                metadata = self._validate_field_formats(metadata)
                metadata = self._validate_identifiers_in_text(metadata, extracted_text_with_metadata)

                # step 5: pattern-based abstract + keywords on plain text
                if not metadata.get("abstract"):
                    extracted_abstract = extract_abstract(plain_text)
                    if extracted_abstract:
                        metadata["abstract"] = extracted_abstract

                kw_real      = extract_keywords_regex(plain_text)
                kw_suggested = extract_keywords_tfidf(plain_text, self.vectorizer)
                metadata["keywords"] = {"real": kw_real, "suggested": kw_suggested}

            return metadata, error
        
        except Exception as e:
            self.logger.exception("Unexpected error in orchestration")
            return {
                "error": "Unexpected error in orchestration",
                "detail": str(e),
            }, 500
