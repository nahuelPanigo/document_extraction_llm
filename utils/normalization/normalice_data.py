import re
import unicodedata
import json


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



def remove_accents(text):
    # Normaliza el texto para descomponer los caracteres acentuados
    text = unicodedata.normalize('NFD', text)
    # Elimina los caracteres diacríticos (acentos)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    # Normaliza el texto nuevamente a la forma compuesta
    text = unicodedata.normalize('NFC', text)
    return text


# def normalize_text(text):
#     # Convertir a minúsculas
#     text = text.lower()
#     # Reemplazar saltos de línea y tabulaciones con espacios
#     text = re.sub(r'[\n\t]', ' ', text)
#     # Reemplazar múltiples espacios con un solo espacio
#     text = re.sub(r'\s+', ' ', text).strip()
#     text = remove_accents(text)
#     return text


def fix_unicode_escapes(text):
    # Converts literal \uXXXX escape sequences to real Unicode characters.
    # e.g. the 6-char string "\u00f3" becomes the single char "ó".
    #
    # Why NOT remove_accents(): that strips accents permanently (ó→o), which is
    # destructive for stored metadata and training data.
    #
    # Why NOT bytes().decode("unicode_escape") (normalice_latin_char approach):
    # that is fragile — if the text already contains real non-ASCII chars (like
    # "ó" encoded as 2 UTF-8 bytes), the latin-1 re-decode corrupts them.
    #
    # This regex only replaces \uXXXX patterns and leaves everything else untouched.
    if '\\u' not in text:
        return text
    return re.sub(r'\\u([0-9A-Fa-f]{4})', lambda m: chr(int(m.group(1), 16)), text)


# OCR artifact: acute accent (´ U+00B4) extracted as a standalone character
# adjacent to the vowel it should modify.
# Two patterns:
#   vowel + ´  →  accented vowel   (e.g. "Astrono´mica" → "Astronómica")
#   ´ + vowel  →  accented vowel   (e.g. "Inform´atica"  → "Informática")
# Also handles dotless-i ı (U+0131) which OCR sometimes produces instead of i:
#   "Geof´ısica" → "Geofísica"
_VOWEL_ACUTE_MAP = {
    'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú',
    'A': 'Á', 'E': 'É', 'I': 'Í', 'O': 'Ó', 'U': 'Ú',
    'ı': 'í',  # dotless i U+0131
}
_ACUTE_AFTER_RE  = re.compile(r'([aeiouAEIOUı])\u00b4')  # vowel + ´
_ACUTE_BEFORE_RE = re.compile(r'\u00b4([aeiouAEIOUı])')  # ´ + vowel


def fix_ocr_accents(text: str) -> str:
    """Fix standalone acute accent (´) adjacent to a vowel — common PDF/OCR artifact."""
    if not isinstance(text, str) or '\u00b4' not in text:
        return text
    text = _ACUTE_AFTER_RE.sub(lambda m: _VOWEL_ACUTE_MAP[m.group(1)], text)
    text = _ACUTE_BEFORE_RE.sub(lambda m: _VOWEL_ACUTE_MAP[m.group(1)], text)
    return text


def normalice_text(text):
    text = fix_unicode_escapes(text)
    text = fix_ocr_accents(text)
    text =  re.sub(r"\.{2,}", " ", text)
    text = corregir_numeros_repetidos(text)
    text = re.sub(r"([{}[\]()*\-+?,:;._!@#$%^&])\1{2,}", r"\1", text)
    text = re.sub(r"([{}[\]()*\-+?,:;._!@#$%^&])\1{2,}", r"\1", text)
    return  re.sub(r"([A-Za-zÁÉÍÓÚáéíóúÑñ])\1{2,}", r"\1", text)


def get_correct_type(type):
    types = {"Artículo" : "Articulo", "Articulo": "Articulo","Article": "Articulo","ARTÍCULO" :"Articulo", "Tesis" : "Tesis" ,"Tesina" : "Tesis" , "Libro" : "Libro" ,"Objeto de conferencia" : "Objeto de conferencia" }
    return types.get(type,type)


def get_corrects_keywords(keywords):
    if isinstance(keywords,str):
        return keywords.split("::")[0]
    return [x.split("::")[0] for x in keywords]

def clean_atributes(json):
    atrs = ['sedici.contributor.editor' ,'sedici.contributor.colaborator' ,'sedici.institucionDesarrollo','id']
    for atr in atrs:
        if atr in json: 
            json.pop(atr)
    return json

def remove_honorifics(text):
    if not isinstance(text, str):
        return text
    
    # Lista de títulos honoríficos a remover
    honorifics = [
        r'\bdr\.\s*', r'\bdra\.\s*', r'\bdrª\.\s*',
        r'\blic\.\s*', r'\blica\.\s*', r'\blicª\.\s*',
        r'\bing\.\s*', r'\binga\.\s*', r'\bingª\.\s*',
        r'\bmg\.\s*', r'\bmgr\.\s*', r'\bmgs\.\s*', r'\bmgtr\.\s*',
        r'\bmag\.\s*', r'\bmsc\.\s*',
        r'\bphd\.\s*', r'\bph\.d\.\s*',
        r'\bprof\.\s*', r'\bprofa\.\s*', r'\bprofª\.\s*',
        r'\bsr\.\s*', r'\bsra\.\s*', r'\bsrª\.\s*',
        r'\bmr\.\s*', r'\bmrs\.\s*', r'\bms\.\s*',
        r'\bdir\.\s*', r'\bdira\.\s*', r'\bdirª\.\s*',
        r'\bcodir\.\s*', r'\bcodira\.\s*', r'\bcodirª\.\s*',
        r'\bcoord\.\s*',
        r'\bcolab\.\s*',
        r'\bcolaborador\b\s*', r'\bcolaboradora\b\s*',
        r'\bagr\.\s*', r'\bagra\.\s*',
        r'\barq\.\s*', r'\barqa\.\s*',
        r'\besp\.\s*',
        r'\babog\.\s*',
        r'\bcdor\.\s*', r'\bcdora\.\s*', r'\bcra\.\s*',
        r'\bmed\.\s*',
        r'\bvet\.\s*', r'\bmv\.\s*',
        r'\bzoot\.\s*',
        r'\bfarm\.\s*',
        r'\bpsic\.\s*',
        r'\bgeof\.\s*',
        r'\bftal\.\s*',
        r'\bsc\.\s*',
        r'\bec\.\s*',
        r'\btec\.\s*', r'\btéc\.\s*',
        r'\bbio\.\s*', r'\bbiol\.\s*',
        # Parenthesised institutional suffixes, e.g. (FCAyF-UNLP), (COORDINADOR)
        r'\s*\([^)]{1,80}\)\s*',
        # Legacy parenthesised role patterns
        r'\(dir\.\)\s*', r'\(dra\.\)\s*', r'\(drª\.\)\s*',
        r'\(codir\.\)\s*', r'\(codira\.\)\s*', r'\(codirª\.\)\s*',
        r'\(lic\.\)\s*', r'\(lica\.\)\s*', r'\(licª\.\)\s*',
        r'\(ing\.\)\s*', r'\(inga\.\)\s*', r'\(ingª\.\)\s*',
    ]
    
    text_cleaned = text
    for honorific in honorifics:
        text_cleaned = re.sub(honorific, '', text_cleaned, flags=re.IGNORECASE)
    
    # Limpiar espacios extra
    text_cleaned = re.sub(r'\s+', ' ', text_cleaned).strip()
    # Remover punto final suelto (e.g. "Leandro Adrián." → "Leandro Adrián")
    text_cleaned = re.sub(r'\.\s*$', '', text_cleaned).strip()
    return text_cleaned


def amend_title_with_subtitle(json_obj):
    if 'title' in json_obj and 'subtitle' in json_obj:
        title = json_obj['title']
        subtitle = json_obj['subtitle']
        
        if subtitle and subtitle.strip():
            json_obj['title'] = f"{title}: {subtitle}"
        
        # Remover el campo subtitle ya que se incorporó al title
        json_obj.pop('subtitle', None)
    
    return json_obj


def normalice_keys(json):
    keys = {"dc.language" : "language", "dc.subject": "keywords","dc.title" : "title" , "sedici.creator.person" : "creator" , "dc.subject.ford" : "subject",
            "sedici.rights.license" : "rights", "sedici.rights.uri" : "rightsurl","dc.identifier.uri": "dc.uri","sedici.identifier.uri":"sedici.uri","dc.date.issued" : "date",
            "mods.originInfo.place" : "originPlaceInfo","sedici.relation.isRelatedWith":"isrelatedwith",
            "sedici.contributor.codirector":"codirector" ,"sedici.contributor.director" :"director" ,"thesis.degree.grantor" :"degree.grantor" ,"thesis.degree.name" :"degree.name",
            "sedici.relation.journalTitle": "journalTitle","sedici.relation.journalVolumeAndIssue": "journalVolumeAndIssue", "sedici.identifier.issn": "issn","sedici.relation.event": "event",
            "sedici.contributor.publisher":"publisher","sedici.identifier.isbn":"isbn","sedici.contributor.compiler":"compiler"
            }
    for elem in keys:
        if elem in json:
            json[keys[elem]] = json.pop(elem)
    return json


from constants import TXT_FOLDER

if __name__ == "__main__":
    filename= "10915-94779"
    file = TXT_FOLDER / f"{filename}.txt"
    with open(file, "r") as f:
        text = f.read()
    
    print(text[:1000])
    print("-------------------------------------------------------")
    print(normalice_text(text[:1000]))
