import re
import unicodedata


def remove_accents(text):
    # Normaliza el texto para descomponer los caracteres acentuados
    text = unicodedata.normalize('NFD', text)
    # Elimina los caracteres diacríticos (acentos)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Normaliza el texto nuevamente a la forma compuesta
    text = unicodedata.normalize('NFC', text)
    return text

def normalize_text(text):
    # Convertir a minúsculas
    text = text.lower()
    # Reemplazar saltos de línea y tabulaciones con espacios
    text = re.sub(r'[\n\t]', ' ', text)
    # Reemplazar múltiples espacios con un solo espacio
    text = re.sub(r'\s+', ' ', text).strip()
    text = remove_accents(text)
    return text



def build_pattern_issn(issn):
    issn_pattern = re.search(r'(\d{4})\D*(\d{4})', issn)
    first_part, second_part = issn_pattern.groups()
    pattern = re.compile(rf'{first_part}.*{second_part}')
    return pattern

def build_pattern_license(license):
    number_license = re.search(r'(\d.\d)', license)
    if number_license:
        return re.compile(rf"(?i)"  # Hacer el patrón insensible a mayúsculas
                    rf"(Creative\s*Commons.*{number_license[0]})|"  # Cualquier cosa que empiece con Creative Commons seguido por el número
                    rf"(Atribuci[oó]n.*{number_license[0]})|"  # Variante en español que empiece con Atribución seguido por el número
                    rf"(Atribucion.*{number_license[0]})"  # Otra variante sin acento en "Atribución"
                    )
    return ""

def build_pattern_volume(volume):
    # Extraer los números del volumen y del número usando expresiones regulares
    volume_number_match = re.search(r'vol[.\s]*(\d+)', volume, re.IGNORECASE)
    number_number_match = re.search(r'(?:no|nro|nr|n|N°|No°)\s*[.\s]*(\d+)', volume, re.IGNORECASE)
    
    volume_number = volume_number_match.group(1) if volume_number_match else ''
    number_number = number_number_match.group(1) if number_number_match else ''
    
    # Define los patrones para volumen y número
    volume_abbreviations = ['vol', 'volumen', 'vols']
    number_abbreviations = ['nro', 'nr', 'n', 'no','n°','no°']
    
    volume_patterns = [f'{abbr}[.]?\\s*' for abbr in volume_abbreviations]
    number_patterns = [f'{abbr}[.]?\\s*' for abbr in number_abbreviations]
    
    combined_volume_patterns = '|'.join(volume_patterns)
    combined_number_patterns = '|'.join(number_patterns)

    # Construir los patrones para volumen y número
    volume_pattern = rf'\b({combined_volume_patterns})\s*{re.escape(volume_number)}\b'
    number_pattern = rf'\b({combined_number_patterns})\s*{re.escape(number_number)}\b'
    final_pattern = rf'({volume_pattern}|{number_pattern})'
    return final_pattern
