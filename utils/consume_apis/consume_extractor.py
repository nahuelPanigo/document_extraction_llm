import requests



def make_requests_xml_text(file_path: str, token: str, normalization: bool=True) -> str:
    url = "http://localhost:8001/extract-with-tags"

    print(file_path)
    extension = file_path.suffix.lstrip(".")
    header_Extension = {".pdf": "application/pdf", ".docx": "application/msword"}
    file_type = header_Extension.get(extension) 

    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, file_type)
        }
        data = {
            "normalization": normalization
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(url, files=files, data=data, headers=headers)
        return response.text




def make_requests_only_text(file_path: str, token: str, normalization: bool=True) -> str:
    url = "http://localhost:8001/extract"



    extension = file_path.suffix.lstrip(".")
    header_Extension = {".pdf": "application/pdf", ".docx": "application/msword"}
    file_type = header_Extension.get(extension) 
    print(f"making request id {file_path}")
    with open(file_path, "rb") as f:
        files = {
            "file": (file_path.name, f, file_type)
        }
        data = {
            "normalization": normalization
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.post(url, files=files, data=data, headers=headers)
        return response.text

