import requests
from dotenv import load_dotenv
import os



def get_dataset(datasetname):
    load_dotenv()
    api_token = os.getenv("TOKEN_HUGGING_FACE")
   
    headers = {"Authorization": f"Bearer {api_token}"}
    url = f"https://huggingface.co/datasets/Nahpanigo99/university_docs_with_metadata/resolve/main/{datasetname}"
    response = requests.get(url, headers=headers)
    return response.json()


