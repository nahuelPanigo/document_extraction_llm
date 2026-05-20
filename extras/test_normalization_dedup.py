import sys
sys.path.insert(0, "../api/app/extractor_service")

from app.service.utils.normalization_and_parse import normalice_text

cases = [
    ("OCR font artifact",          "TTTTIIIITTTTUUUULLLOOOO PPPAAARRRAAA VER COMO FUNCIONA XIIIKKK"),
    ("Roman numeral XIII",         "siglo XIII"),
    ("Roman numeral XXII",         "XXII"),
    ("Roman numeral VIII",         "VIII"),
    ("Roman numeral III",          "III"),
    ("Non-roman repeated",         "NNNIII"),
    ("Mixed OCR artifact",         "NNNAAALLLL"),
    ("Lowercase repeated",         "haaablar"),
    ("Normal word",                "hola mundo"),
    ("Roman + artifact in sentence", "Capítulo XIIII - TTTEEESSSTTT"),
]

for desc, text in cases:
    result = normalice_text(text)
    print(f"{desc}")
    print(f"  IN:  {text}")
    print(f"  OUT: {result}")
    print()
