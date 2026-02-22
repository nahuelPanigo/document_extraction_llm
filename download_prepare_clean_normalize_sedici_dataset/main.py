from download_prepare_clean_normalize_sedici_dataset.cloud_llm_cleaner_consumer.genai_consumer import GenaiConsumer
from download_prepare_clean_normalize_sedici_dataset.cloud_llm_cleaner_consumer.openai_consumer import OpenaiConsumer
from download_prepare_clean_normalize_sedici_dataset.extract_text_make_dataset import extract_and_make_dataset
from download_prepare_clean_normalize_sedici_dataset.download_data import download_files
from download_prepare_clean_normalize_sedici_dataset.extract_data_from_csv_sedici import merge_data,get_ids_from_csv
from download_prepare_clean_normalize_sedici_dataset.exact_match_validator import apply_exact_match_validation
from constants import CSV_FOLDER,PDF_FOLDER,JSON_FOLDER,TXT_FOLDER,CSV_SEDICI,CSV_SEDICI_FILTERED,DATASET_WITH_METADATA_AND_TEXT_DOC,DATASET_WITH_METADATA,DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED,DATASET_WITH_METADATA_AND_TEXT_DOC_CLEANED,CLEAN_PROVIDER_TO_USE
import os
from utils.colors.colors_terminal import Bcolors
from download_prepare_clean_normalize_sedici_dataset.split_dataset_and_normalize_text import normalize_and_split_dataset, normalize_dataset_pre_llm

CLEAN_PROVIDERS = {
    "genai": GenaiConsumer,
    "openai": OpenaiConsumer,
}

if __name__ == "__main__":
    csv_filename = CSV_FOLDER / CSV_SEDICI
    filtered_csv_filename = CSV_FOLDER / CSV_SEDICI_FILTERED
    json_metadata_filename = JSON_FOLDER / DATASET_WITH_METADATA
    json_metadata_and_text_filename = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC
    json_metadata_and_text_cleaned_filename = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CLEANED
    json_metadata_and_text_checked_filename = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED


    #filter data from sedici csv and normalize names and values
    if not (filtered_csv_filename).exists():
        print(f"{Bcolors.OKGREEN}merging csv{Bcolors.ENDC}")
        merge_data(csv_filename,filtered_csv_filename)

    #download pdfs
    if not (PDF_FOLDER).exists():
        print(f"{Bcolors.OKGREEN}creating pdf folder{Bcolors.ENDC}")
        os.makedirs(PDF_FOLDER)
    ids = get_ids_from_csv(filtered_csv_filename)
    if ids:
        print(f"{Bcolors.OKGREEN}downloading pdfs{Bcolors.ENDC}")
        download_files(ids)
    #extract text from pdfs
    if not (json_metadata_and_text_filename).exists():
        if not (JSON_FOLDER).exists():
            print(f"{Bcolors.OKGREEN}creating json folder{Bcolors.ENDC}")
            os.makedirs(JSON_FOLDER)
        if not (TXT_FOLDER).exists():
            print(f"{Bcolors.OKGREEN}creating txt folder{Bcolors.ENDC}")
            os.makedirs(TXT_FOLDER)
        print(f"{Bcolors.OKGREEN}extracting text and making dataset{Bcolors.ENDC}")
        extract_and_make_dataset(json_metadata_filename,json_metadata_and_text_filename,filtered_csv_filename,ids)
    # pre-llm normalization: filter corrupted docs, normalice_text, remove_honorifics
    print(f"{Bcolors.OKGREEN}pre-llm normalization{Bcolors.ENDC}")
    normalize_dataset_pre_llm(json_metadata_and_text_filename, json_metadata_filename)
    # clean metadata
    if not (json_metadata_and_text_checked_filename).exists():
        consumer_class = CLEAN_PROVIDERS[CLEAN_PROVIDER_TO_USE]
        consumer = consumer_class()
        consumer.clean_metadata(json_metadata_and_text_filename,json_metadata_and_text_cleaned_filename)
    # apply exact match validation
    print(f"{Bcolors.OKGREEN}applying exact match validation{Bcolors.ENDC}")
    apply_exact_match_validation(json_metadata_and_text_cleaned_filename, json_metadata_and_text_filename)
    # split dataset and normalize text
    print(f"{Bcolors.OKGREEN}splitting dataset and normalizing text{Bcolors.ENDC}")
    normalize_and_split_dataset(json_metadata_and_text_cleaned_filename,json_metadata_filename,json_metadata_and_text_checked_filename)
   