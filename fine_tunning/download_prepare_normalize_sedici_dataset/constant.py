DATA_FOLDER= "C:/Users/Nahuel/Documents/document_extraction_llm/fine_tunning/data/sedici/"
JSON_FOLDER = DATA_FOLDER + "jsons/"
PDF_FOLDER = DATA_FOLDER + "pdfs/"
TXT_FOLDER = DATA_FOLDER + "texts/"
XML_FOLDER = DATA_FOLDER + "xmls/"
CSV_FOLDER = DATA_FOLDER + "csv/"
DATASET_SEDICI_URL_BASE = "https://sedici.unlp.edu.ar/oai/openaire?verb=ListRecords&resumptionToken=oai_dc////"
DOWNLOAD_URL = "https://sedici.unlp.edu.ar"
PDF_URL = DOWNLOAD_URL + "/bitstream/handle/"
GROBID_URL = "http://localhost:8070/api/processFulltextDocument"
DATASET_SEDICI_URL_BASE = "https://sedici.unlp.edu.ar/oai/openaire?verb=ListRecords&resumptionToken=oai_dc////"
COLUMNS_DATA = ['id', 'title', 'abstract', 'categories','authors']
DATASET_FILENAME = "metadata_sedici_files.json"
DATASET_WITH_METADATA_CHECKED = "final_metadata_Chekced.json"
DATASET_WITH_TEXT_DOC = "metadata_and_text.json"
CANT_TOKENS = 14000
TOKENS_LENGTH = 4
VALID_ACCENTS = "áéíóúüñÁÉÍÓÚÜÑ"