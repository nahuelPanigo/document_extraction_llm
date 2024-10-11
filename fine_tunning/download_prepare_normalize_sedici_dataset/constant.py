import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_FOLDER = Path(os.getenv("DATA_FOLDER", ROOT_DIR / "fine_tunning" / "data" / "sedici"))
JSON_FOLDER = DATA_FOLDER / "jsons/"
PDF_FOLDER = DATA_FOLDER / "pdfs/"
TXT_FOLDER = DATA_FOLDER / "texts/"
XML_FOLDER = DATA_FOLDER / "xmls/"
CSV_FOLDER = DATA_FOLDER / "csv/"
DATASET_SEDICI_URL_BASE = "https://sedici.unlp.edu.ar/oai/openaire?verb=ListRecords&resumptionToken=oai_dc////"
DOWNLOAD_URL = "https://sedici.unlp.edu.ar"
PDF_URL = DOWNLOAD_URL + "/bitstream/handle/"
GROBID_URL = "http://localhost:8070/api/processFulltextDocument"
DATASET_FILENAME = "metadata_sedici_files.json"
DATASET_WITH_METADATA_CHECKED = "final_metadata_Chekced.json"
DATASET_WITH_TEXT_DOC = "metadata_and_text.json"
DATASET_WITH_TEXT_DOC2 = "metadata_and_text2.json"
CANT_TOKENS = 14000
TOKENS_LENGTH = 4
VALID_ACCENTS = "áéíóúüñÁÉÍÓÚÜÑ"