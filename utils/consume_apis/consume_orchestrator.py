import argparse
import json
from pathlib import Path

import json
from pathlib import Path

import requests


def upload_file(file_path: str,token: str, normalization: bool=True, type: str="None", deepanalyze: bool=False, host_url: str = None, ocr: bool=False) -> dict:
    url = host_url if host_url else "http://localhost:8000" # type: ignore

    url = f"{url}/upload"
    extension = file_path.suffix.lstrip(".")
    header_Extension = {"pdf": "application/pdf", "docx": "application/msword"}
    file_type = header_Extension.get(extension)
    print(f"🔍 File extension: {extension}, File type: {file_type}") 
    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, file_type)
        }
        data = {
            "normalization": normalization,
            "type": type,
            "deepanalyze": deepanalyze,
            "ocr": ocr
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(url, files=files, data=data, headers=headers)

    # Debug: print status code and response
    print(f"🔍 Status code: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Error response: {response.text[:500]}")

    try:
        return response.json()
    except ValueError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"❌ Response text: {response.text[:500]}")
        return {}


if __name__ == "__main__":
    FILENAME = "/home/nahuel/Documents/document_extraction_llm/data/sedici/pdfs/10915-148285.pdf"
    TOKEN = "397e50621c2cbc17bc9cf132e95d644ce1bebed3a5bf98786a4325bc7cdb0abf"

    result = upload_file(
        file_path=Path(FILENAME),
        token=TOKEN,
        normalization=True,
        type="None",
        deepanalyze=False,
        host_url=None,
        ocr=False,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
