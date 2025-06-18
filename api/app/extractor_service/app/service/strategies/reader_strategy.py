from abc import ABC, abstractmethod
from typing import Any

class ReaderStrategy(ABC):
    @abstractmethod
    def extract_text(self, file: Any) -> str:
        pass

    @abstractmethod
    def extract_text_with_xml_tags(self, file: Any) -> str:
        pass

