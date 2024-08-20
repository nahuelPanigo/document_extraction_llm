import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from difflib import SequenceMatcher
import os
from constant import PDF_FOLDER
import re

#download tesseract.exe and put the exe if not in path
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'


# Extracción con PyMuPDF
def extract_text_with_fitz(file_path):
    doc = fitz.open(file_path)
    text = []
    for page in doc:
        text.append(page.get_text())
    return text

# Extracción con pdfplumber
def extract_text_with_pdfplumber(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = []
        for page in pdf.pages:
            text.append(page.extract_text())
    return text


def ocr_from_pdf(file_path):
    # Convertir PDF a imágenes
    images = convert_from_path(file_path,poppler_path= r'C:/Program Files/poppler-24.07.0/Library/bin')
    
    # Extraer texto de cada imagen usando pytesseract
    texts = []
    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image)
        texts.append(text)
    
    return texts

def is_legible(text):
    """Verifica si el texto contiene palabras legibles"""
    # Elimina caracteres no alfabéticos y divide en palabras
    words = re.findall(r'\b\w+\b', text)
    return len(words) > 5  # Ajusta el umbral según tus necesidades


def compare_texts(texts):
    """Compara una lista de textos y devuelve el más significativo"""
    # Filtrar textos legibles
    legible_texts = [text for text in texts if is_legible(text)]
    
    if len(legible_texts) == 0:
        # Si no hay textos legibles, simplemente devolvemos el texto más largo
        return max(texts, key=len)
    
    if len(legible_texts) == 1:
        # Si solo hay un texto legible, devuélvelo
        return legible_texts[0]
    
    # Comparar textos legibles usando SequenceMatcher
    best_text = legible_texts[0]
    for text in legible_texts[1:]:
        if SequenceMatcher(None, best_text, text).ratio() > SequenceMatcher(None, best_text, text).ratio():
            best_text = text
    
    return best_text

def compare_best_text(texts):
    """Compara textos extraídos con varias herramientas y selecciona el mejor"""
    best_texts = ""
    for page_texts in zip(*texts):
        best_text = compare_texts(page_texts)
        best_texts +=best_text
    
    return best_texts

key = "ARG-UNLP-TPG-0000001062"
# Utiliza funciones para extraer texto
pdf_path = os.path.join(PDF_FOLDER, f"{key}.pdf")
text_fitz = extract_text_with_fitz(pdf_path)
text_pdfplumber = extract_text_with_pdfplumber(pdf_path)
text_ocr = ocr_from_pdf(pdf_path)
texts = [text_fitz, text_pdfplumber, text_ocr]
best_texts = compare_best_text(texts)

print(best_texts)
print("******************************************************************************")
print("******************************************************************************")
#print(texts)
print(len(text_fitz))
print(len(text_pdfplumber))
print(text_ocr)
