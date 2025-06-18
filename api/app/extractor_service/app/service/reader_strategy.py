
from app.service.utils.normalization_and_parse import has_permit_extension,get_ext,normalice_text
from app.constants.constant import FILETYPES
from app.errors.error import INPUT_ERRORS as IN_E
import tempfile
from app.service.strategies.pdf_reader_strategy import PdfReader
from app.service.strategies.word_reader_strategy import DocxReader
from app.logging_config import logging
from typing import Any,Callable
import shutil


class Reader:
    def __init__(self, file: Any):
        self.file = file
        self.error = self._permit_extension(file)
        self.ext = get_ext(file.filename)
        self.strategy = self._select_strategy(file)


    @staticmethod
    def _permit_extension(file):
        if not has_permit_extension(file.filename, FILETYPES):
            return {
                "error": IN_E["ERROR_FORMAT_EXTENSION"],
                "code": IN_E["CODE_ERROR_FORMAT_EXTENSION"]
            }
        return None

    @staticmethod
    def _select_strategy(file):
        ext = get_ext(file.filename).lower()
        if ext == "pdf":
            return PdfReader()
        elif ext == "docx":
            return DocxReader()
        else:
            raise ValueError(f"No strategy for extension: {ext}")

    
    def extract(self, strategy_method: Callable[[str], str], normalization: bool = True):
        if self.error:
            return {
                "success": False,
                "error": {"message": self.error["error"],"code": self.error["code"]}
            }

        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{self.ext}') as temp_file:
            shutil.copyfileobj(self.file.file, temp_file)
            temp_file_path = temp_file.name

        try:
            logging.info(f"Extracting text using {strategy_method.__name__} from {temp_file_path}")
            text = strategy_method(temp_file_path)
            if normalization:
                text = normalice_text(text)
            return {
                "success": True,
                "data": {
                    "text": text
                }
            }
        except Exception as e:
            logging.error("Error extracting text: %s", e)
            return {
                "success": False,
                "error": {"message": IN_E["ERROR_EXTARCTING_TEXT"],"code": IN_E["CODE_ERROR_EXTARCTING_TEXT"]}}
          

    def get_text(self, normalization: bool = True):
        return self.extract(self.strategy.extract_text, normalization)

    def get_text_with_tags(self, normalization: bool = True):
        return self.extract(self.strategy.extract_text_with_xml_tags, normalization)