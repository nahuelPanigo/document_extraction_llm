import requests
from utils.text_extraction.read_and_write_files import read_data_json
from constants import PDF_FOLDER, PDF_URL
from utils.colors.colors_terminal import Bcolors
from utils.download.pdf_downloader import download_batch
import time


def get_ids_not_downloaded(ids):
    print("paso por aca",len(ids))
    to_download = [id for id in ids if not (PDF_FOLDER / f"{id}.pdf").exists()]
    print(f"{Bcolors.OKGREEN}  pdfs to download {len(to_download)} {Bcolors.ENDC}")
    print(f"{Bcolors.OKGREEN}  ids of dataset {len(ids)} {Bcolors.ENDC}")
    return to_download

def download_files(ids):
    col_ids = get_ids_not_downloaded(ids)
    download_batch(col_ids, PDF_FOLDER)
