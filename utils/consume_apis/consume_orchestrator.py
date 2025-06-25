import requests


def upload_file(file_path: str,token: str, normalization: bool=True, type: str="None", deepanalize: bool=False) -> str:
    url = "http://localhost:8000/upload"

    with open(file_path, "rb") as f:
        files = {
            "file": (file_path, f, "application/pdf")
        }
        data = {
            "normalization": normalization,
            "type": type,
            "deepanalize": deepanalize
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(url, files=files, data=data, headers=headers)

    try:
        return response.json()
    except ValueError:
        return {}