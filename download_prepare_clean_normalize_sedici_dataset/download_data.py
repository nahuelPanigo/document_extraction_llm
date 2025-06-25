import requests
from utils.text_extraction.read_and_write_files import read_data_json
from constants import PDF_FOLDER,PDF_URL
from utils.colors.colors_terminal import Bcolors
import time



def make_request(url, file_path,key):
    resp = requests.get(url)
    if resp.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(resp.content)
        print(f"{Bcolors.OKGREEN} bajo el pdf {key} {Bcolors.ENDC}")
    elif resp.status_code == 429:
        time.sleep(10)
        print(f"{Bcolors.WARNING} esperando 10 segundos para el pdf {key} {Bcolors.ENDC}")
        make_request(url,file_path,key)
    else:
        print(f"{Bcolors.FAIL} error en el pdf {key} {resp.status_code} {Bcolors.ENDC}")


def download_files(ids):
    for key in ids:
        try:
            id = key.replace("-","/")
            url = PDF_URL+id+"/Documento_completo.pdf?sequence=1&isAllowed=y"
            file_path = PDF_FOLDER / f"{key}.pdf"
            if not file_path.exists():
                make_request(url, file_path,key)
            else:
                print(f"{Bcolors.OKGREEN} ya existe el pdf {key} {Bcolors.ENDC}")
        except:
            print(f"{Bcolors.FAIL} error en el pdf {key} {Bcolors.ENDC}")

