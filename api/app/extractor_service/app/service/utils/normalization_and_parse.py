import re


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


def fix_unicode_escapes(text):
    # Converts literal \uXXXX escape sequences to real Unicode characters.
    # Safe alternative to bytes().decode("unicode_escape") — only touches \uXXXX
    # patterns and leaves real Unicode chars already in the string untouched.
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


# NOTE: normalice_latin_char is defined here but not called in this service.
# It IS used in llm_service/app/services/utils.py inside parse_json().
# It works there because LLM output is pure ASCII + \uXXXX escapes, so the
# bytes().decode("unicode_escape") is safe in that specific context.
def normalice_latin_char(text):
        text = text.replace("\\r\\n", " ")
        text = re.sub(r'\\[Rp/c]', '', text)  # Si hay más casos, agrégalos aquí
    # 2️⃣ Si quedan secuencias válidas (\uXXXX o \n, \r, etc.), aplicar unicode_escape
        if re.search(r'\\u[0-9A-Fa-f]{4}|\\[nr]', text):  
            text = bytes(text, "utf-8").decode("unicode_escape")
        text = re.sub(r'"\[(.*?)\]"', r'[\1]', text) 
        text = text.replace("\�", "¿")
        return text


