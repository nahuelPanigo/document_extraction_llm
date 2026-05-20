import json
from pathlib import Path

import requests


def make_requests_xml_text(file_path: str, token: str, normalization: bool=True, host_url: str = None, ocr: bool=False) -> str:
    base_url = host_url if host_url else "http://localhost:8001"
    url = f"{base_url}/extract-with-tags"

    print(file_path)
    extension = file_path.suffix.lstrip(".")
    header_Extension = {".pdf": "application/pdf", ".docx": "application/msword"}
    file_type = header_Extension.get(extension) 

    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, file_type)
        }
        data = {
            "normalization": normalization,
            "ocr": ocr
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(url, files=files, data=data, headers=headers)
        return response.text




def make_requests_only_text(file_path: str, token: str, normalization: bool=True, host_url: str = None, ocr: bool=False) -> str:
    base_url = host_url if host_url else "http://localhost:8001"
    url = f"{base_url}/extract"

    extension = file_path.suffix.lstrip(".")
    header_Extension = {".pdf": "application/pdf", ".docx": "application/msword"}
    file_type = header_Extension.get(extension)
    print(f"making request id {file_path}")
    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, file_type)
        }
        data = {
            "normalization": normalization,
            "ocr": ocr
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(url, files=files, data=data, headers=headers)
        return response.text


if __name__ == "__main__":
    FILENAME = "/home/nahuel/Documents/document_extraction_llm/data/sedici/pdfs/10915-148285.pdf"
    TOKEN = "f85b060e12171336480486d98b694bcb0b6c1c826938c7e6916277d6676bae8c"

    result = make_requests_only_text(
        file_path=Path(FILENAME),
        token=TOKEN,
        normalization=True,
        ocr=False,
    )
    print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))

