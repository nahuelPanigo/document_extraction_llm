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
        return {"text" : strategyReader.extract_text_with_xml_tags(temp_file_path)},None # None for: no error has occurred
    except Exception as e:
        print("el error es:", e)
        return IN_E["ERROR_EXTARCTING_TEXT"], IN_E["CODE_ERROR_EXTARCTING_TEXT"]  