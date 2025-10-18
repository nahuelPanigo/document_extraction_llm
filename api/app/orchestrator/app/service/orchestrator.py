from dotenv import load_dotenv
import os
from fastapi import UploadFile
from app.logging_config import logging
import requests
from app.service.indentifier import TypeIdentifier, SubjectIdentifier
from app.service.strategies.type_strategy import LibroStrategy,TesisStrategy,ArticuloStrategy,ObjectConferenceStrategy,GeneralStrategy
import io
from typing import Tuple, Optional, Union
from app.constants.constant import PROMPT_DEEPANALYZE
import json

class Orchestrator:
    def __init__(self):
        load_dotenv()
        self.extractor_service_url = os.getenv("EXTRACTOR_URL")
        self.extractor_service_api_key = os.getenv("EXTRACTOR_TOKEN")
        self.llm_deepanalyze_url = os.getenv("LLM_DEEPANALYZE_URL")
        self.llm_deepanalyze_api_key = os.getenv("LLM_DEEPANALYZE_TOKEN")
        self.logger = logging.getLogger(__name__)
        self.type_identifier = TypeIdentifier(path_clf =os.getenv("IDENTIFIER_PATH_MODEL"), path_vectorizer=os.getenv("IDENTIFIER_PATH_VECTORIZER"))
        self.subject_identifier = SubjectIdentifier(
            path_classifier=os.getenv("SUBJECT_IDENTIFIER_PATH_CLASSIFIER", "models/svm_classifier.pkl"),
            path_vectorizer=os.getenv("SUBJECT_IDENTIFIER_PATH_VECTORIZER", "models/svm_vectorizer.pkl"),
            path_label_encoder=os.getenv("SUBJECT_IDENTIFIER_PATH_LABEL_ENCODER", "models/svm_label_encoder.pkl")
        )

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

    def _extract_text(self, file_bytes: bytes, filename: str, content_type: str, normalization: bool) -> Tuple[Optional[str], Optional[dict]]:
        self.logger.info("calling extractor service only text")
        stream = io.BytesIO(file_bytes)
        payload = (filename, stream, content_type)

        response_extractor = requests.post(
            self.extractor_service_url + "/extract",
            headers=self._get_headers(api_key=self.extractor_service_api_key),
            files={"file": payload},
            params={"normalization": normalization}
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

    def orchestrate(self, file: UploadFile, normalization: bool = True, type: str = None, deepanalyze: bool = False) -> Tuple[dict, Optional[int]]:
        self.logger.info(f"Orchestrating file: {file.filename} with normalization={normalization}")
        try:
            file_bytes = file.file.read()
            filename = file.filename
            content_type = file.content_type

            # step 1: extract text for subject and type prediction
            plain_text, error_response = self._extract_text(file_bytes, filename, content_type, normalization)
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
                params={"normalization": normalization}
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
            return metadata, error
        
        except Exception as e:
            self.logger.exception("Unexpected error in orchestration")
            return {
                "error": "Unexpected error in orchestration",
                "detail": str(e),
            }, 500
