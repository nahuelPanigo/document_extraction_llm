import requests


def consume_llm(input_text: str,token: str) -> str:
    url = "http://localhost:8002/consume-llm"
    data = {
        "text": input_text
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, data=data, headers=headers)

    try:
        return response.json()
    except ValueError:
        return {}