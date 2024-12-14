# from transformers import LEDForConditionalGeneration, LEDTokenizer
import google.generativeai as genai
import os
from pathlib import Path
import pandas as pd
from pdf_reader import PdfReader
import json
from dotenv import load_dotenv
import numpy as np


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model=genai.GenerativeModel("models/gemini-1.5-flash-latest")


DATA_FOLDER = Path(__file__).parents[1] / "fine_tunning/data/sedici" 
PDF_FOLDER = DATA_FOLDER / "pdfs3"
csv_metadata = DATA_FOLDER / "sedici_filtered_2018_2024.csv"



df = pd.read_csv(csv_metadata)   
reader = PdfReader()




prompt = """
You are an expert in metadata validation and text analysis. Your task is to process a given text and a JSON object containing metadata. Follow these steps precisely:

1. Analyze the provided text and metadata object.

2. For each key-value pair in the metadata:
    - Search the text for the metadata value (or a variation of it, such as differences in case, abbreviations, punctuation, or word order).
    - If the value exists in the text but is written differently, update the metadata value to match the exact appearance in the text.
    - If the value does not appear in the text, remove that key from the metadata.

3. Ensure all metadata values in the JSON object match their exact appearance in the text.

4. Return **only** the corrected JSON object. Do not include explanations, comments, the original text, or the original metadata.

Input example:
- Text: "This paper was written by Juan M. Pérez in 2024."
- Metadata: {"author": "Perez, Juan Manuel", "year": "2024", "journal": "Journal of AI Research"}

Output example:
{"author": "Juan M. Pérez", "year": "2024"}

Input example:
- Text: "Dr. María García collaborated with John O'Connor to publish this work in 2023."
- Metadata: {"author1": "Garcia, Maria", "author2": "OConnor, John", "year": "2023", "publisher": "AI Press"}

Output example:
{"author1": "Dr. María García", "author2": "John O'Connor", "year": "2023"}
"""


for index,row in df.head(1).iterrows():
    dict_metadata = row.to_dict()
    metadata = {
    k: v for k, v in dict_metadata.items() 
    if not (isinstance(v, float) and pd.isna(v)) and (k != "dc.description.abstract")  # Elimina solo los NaN
    }
    id = row["id"]
    filename =  f"{id}.pdf" 
    extracted_text = reader.extract_text_with_xml_tags(PDF_FOLDER / filename)
    input = f"{prompt}  Text: {extracted_text} metadata: {metadata}"
    input = input[:9000]
    response = model.generate_content(input)
    if response._error:
        print(response._error)
        continue
    print(response.text)

    print("--------------------------------------")
    print(metadata)

