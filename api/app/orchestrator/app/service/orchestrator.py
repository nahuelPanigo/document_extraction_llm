from dotenv import load_dotenv
import os
from fastapi import UploadFile
from app.logging_config import logging
import requests
from app.service.indentifier import TypeIdentifier
from app.service.strategies.type_strategy import LibroStrategy,TesisStrategy,ArticuloStrategy
import io

class Orchestrator:
    def __init__(self):
        load_dotenv()
        self.extractor_service_url = os.getenv("EXTRACTOR_URL")
        self.extractor_service_api_key = os.getenv("EXTRACTOR_TOKEN")
        self.logger = logging.getLogger(__name__)
        self.type_identifier = TypeIdentifier(path_clf =os.getenv("IDENTIFIER_PATH_MODEL"), path_vectorizer=os.getenv("IDENTIFIER_PATH_VECTORIZER"))

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
    def _get_file_payload(file: UploadFile) -> tuple[str, io.BytesIO, str]:
        file_bytes = file.file.read()
        file_stream = io.BytesIO(file_bytes)
        # Después de leer, rebobina el stream al principio para futuras lecturas
        file_stream.seek(0)
        return file.filename, file_stream, file.content_type

    def orchestrate(self, file: UploadFile, normalization: bool = True, type: str = None):
        self.logger.info(f"Orchestrating file: {file.filename} with normalization={normalization}")
        try:
            # Leer el archivo una única vez y reutilizar los bytes
            file_bytes = file.file.read()
            filename = file.filename
            content_type = file.content_type

            if type is None:
                self.logger.info("calling extractor service only text")
                stream1 = io.BytesIO(file_bytes)
                payload1 = (filename, stream1, content_type)

                response_extractor = requests.post(
                    self.extractor_service_url + "/extract",
                    headers=self._get_headers(api_key=self.extractor_service_api_key),
                    files={"file": payload1},
                    params={"normalization": normalization}
                )

                if response_extractor.status_code != 200:
                    self.logger.error(f"Extractor error: {response_extractor.text}")
                    return self._error_response_extractor(
                        error="Error during text extraction text only",
                        response_extractor=response_extractor
                    ), 500

                self.logger.info("calling predictor dc type")
                dc_type = self.type_identifier.predecir_tipo_documento(response_extractor.json().get("text"))
            else:
                dc_type = type

            self.logger.info("calling extractor service with tags")
            stream2 = io.BytesIO(file_bytes)
            payload2 = (filename, stream2, content_type)

            response_extractor_with_tags = requests.post(
                self.extractor_service_url + "/extract-with-tags",
                headers=self._get_headers(api_key=self.extractor_service_api_key),
                files={"file": payload2},
                params={"normalization": normalization}
            )

            if response_extractor_with_tags.status_code != 200:
                self.logger.error(f"Extractor error: {response_extractor_with_tags.text}")
                return self._error_response_extractor(
                    error="Error during text extraction with tags",
                    response_extractor=response_extractor_with_tags
                ), 500

            extracted_text_with_metadata = response_extractor_with_tags.json().get("text")
            self.logger.info("Text extracted successfully")

            # Estrategia por tipo de documento
            strategies = {
                "Libro": LibroStrategy,
                "Articulo": ArticuloStrategy,
                "Tesis": TesisStrategy
            }

            strategy_class = strategies[dc_type]
            strategy = strategy_class()
            self.logger.info(f"Calling {strategy_class.__name__}")
            return strategy.get_metadata(extracted_text_with_metadata), None

        except Exception as e:
            self.logger.exception("Unexpected error in orchestration")
            return {
                "error": "Unexpected error in orchestration",
                "detail": str(e),
            }, 500
