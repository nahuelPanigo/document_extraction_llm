import requests
from app.constants import URL_GROBID_SERVICES
from bs4 import BeautifulSoup


def get_ner_xml(file):
    files = {'input': ('document.pdf', file.read(), 'application/pdf')}
    headers = {}
    response = requests.post(URL_GROBID_SERVICES, files=files, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        authors = soup.find_all("author")
        for author in authors:
            {}