import pandas as pd
import json
import pdfplumber
import chardet


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result


def read_data_json(json_filename,enc):
    with open(json_filename, 'r', encoding=enc) as file:
        return json.load(file)


def write_to_json(json_filename,data,enc):
  with open(json_filename, 'w', encoding=enc) as jsonfile:
        json.dump(data, jsonfile, indent=4)

def read_data_pdf(pdf_filename):
    text = ""
    with pdfplumber.open(pdf_filename) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text


def read_data_txt(file_path,enc):
    with open(file_path, 'r', encoding=enc) as content_file:
        content_list = content_file.read().strip()
    return content_list

def write_to_text(txt_filename,text):
    with open(txt_filename, "w",  encoding='utf-8') as text_file:
        text_file.write(text)
