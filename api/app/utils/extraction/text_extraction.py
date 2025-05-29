import re
from .pdf_reader import PdfReader       
from .word_reader import WordReader     
from ...errors import INPUT_ERRORS as IN_E  
from ...constants import FILETYPES 
import tempfile
import shutil


def has_permit_extension(filename, permit_extensions):
    # Construct a regular expression pattern to match any of the permitted extensions
    pattern = r"(" + "|".join(re.escape(ext) for ext in permit_extensions) + r")$"
    return bool(re.search(pattern, filename))

def get_ext(file):
    return file.split(".")[-1]

def get_id(file):
    return file.split("."+get_ext(file))[0]


def corregir_numeros_repetidos(texto):
    # Coincide dos números largos separados por cualquier cantidad de guiones/espacios
    patron = re.compile(r'(\d{6,})\s*[-–]{1,}\s*(\d{6,})')

    def limpiar_numero(num):
        # Divide el número en bloques y toma 1 dígito por bloque repetido
        longitud = len(num)
        if longitud % 4 == 0:
            factor = longitud // 4
            return ''.join(num[i] for i in range(0, longitud, factor))
        elif longitud % 2 == 0:
            return ''.join(num[i] for i in range(0, longitud, 2))
        else:
            # Si no es divisible, lo dejamos como está
            return num

    def reemplazo(match):
        num1, num2 = match.groups()
        limpio1 = limpiar_numero(num1)
        limpio2 = limpiar_numero(num2)
        return f"{limpio1}-{limpio2}"

    return patron.sub(reemplazo, texto)


def normalice_text(text):
    text =  re.sub(r"\.{2,}", " ", text)  
    text = corregir_numeros_repetidos(text)
    text = re.sub(r"([{}[\]()*\-+?,:;._!@#$%^&])\1{2,}", r"\1", text)
    text = re.sub(r"([{}[\]()*\-+?,:;._!@#$%^&])\1{2,}", r"\1", text)
    return  re.sub(r"([A-Za-zÁÉÍÓÚáéíóúÑñ])\1{2,}", r"\1", text)


def normalice_latin_char(text):
        text = text.replace("\\r\\n", " ")
        text = re.sub(r'\\[Rp/c]', '', text)  # Si hay más casos, agrégalos aquí
    # 2️⃣ Si quedan secuencias válidas (\uXXXX o \n, \r, etc.), aplicar unicode_escape
        if re.search(r'\\u[0-9A-Fa-f]{4}|\\[nr]', text):  
            text = bytes(text, "utf-8").decode("unicode_escape")
        text = re.sub(r'"\[(.*?)\]"', r'[\1]', text) 
        text = text.replace("\�", "¿")
        return text



def get_text(file):
    if ( not has_permit_extension(file.filename, FILETYPES)):
        return IN_E["ERROR_FORMAT_EXTENSION"],IN_E["CODE_ERROR_FORMAT_EXTENSION"]
    strategyReader = ""
    ext =  get_ext(file.filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_file_path = temp_file.name
    if(ext == "pdf"):
        strategyReader = PdfReader()
    elif (ext == "docx"):
        strategyReader = WordReader()  
    try:
        return {"text" : normalice_text(strategyReader.extract_text_with_xml_tags(temp_file_path))},None # None for: no error has occurred
    except Exception as e:
        print("el error es:", e)
        return IN_E["ERROR_EXTARCTING_TEXT"], IN_E["CODE_ERROR_EXTARCTING_TEXT"]  