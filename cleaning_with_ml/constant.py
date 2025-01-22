from pathlib import Path


DATA_FOLDER = Path(__file__).parents[1] / "fine_tunning/data/sedici" 
PDF_FOLDER = DATA_FOLDER / "pdfs3"
CSV_METADATA = DATA_FOLDER / "sedici_filtered_2018_2024.csv"

JSON_FILENAME = "metadata_correjida.json"
JSON_FILENAME2 = "metadata_correjida2.json"
JSON_FILENAME3 = "metadata_correjida5.json"
JSON_FILENAME4 = "metadata_correjida6.json"
JSON_FILENAMEFINAL = "metadata_correjidaFINAL.json"
APROX_TOK_PER_SOL = 2500