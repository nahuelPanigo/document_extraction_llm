import requests


def upload_file(file_path: str,token: str, normalization: bool=True, type: str="None", deepanalyze: bool=False) -> str:
    url = "http://localhost:8000/upload"

    extension = file_path.suffix.lstrip(".")
    header_Extension = {".pdf": "application/pdf", ".docx": "application/msword"}
    file_type = header_Extension.get(extension) 
    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, file_type)
        }
        data = {
            "normalization": normalization,
            "type": type,
            "deepanalize": deepanalyze
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(url, files=files, data=data, headers=headers)

    try:
        return response.json()
    except ValueError:
        return {}
    