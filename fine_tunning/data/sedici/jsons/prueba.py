import re

def build_pattern_volume(volume):
    # Extraer los números del volumen y del número usando expresiones regulares
    volume_number_match = re.search(r'vol[.\s]*(\d+)', volume, re.IGNORECASE)
    number_number_match = re.search(r'(?:no|nro|nr|n)\s*[.\s]*(\d+)', volume, re.IGNORECASE)
    
    volume_number = volume_number_match.group(1) if volume_number_match else ''
    number_number = number_number_match.group(1) if number_number_match else ''
    
    # Define los patrones para volumen y número
    volume_abbreviations = ['vol', 'volumen', 'vols']
    number_abbreviations = ['nro', 'nr', 'n', 'no']
    
    volume_patterns = [f'{abbr}[.]?\\s*' for abbr in volume_abbreviations]
    number_patterns = [f'{abbr}[.]?\\s*' for abbr in number_abbreviations]
    
    combined_volume_patterns = '|'.join(volume_patterns)
    combined_number_patterns = '|'.join(number_patterns)

    # Construir los patrones para volumen y número
    volume_pattern = rf'\b({combined_volume_patterns})\s*{re.escape(volume_number)}\b'
    number_pattern = rf'\b({combined_number_patterns})\s*{re.escape(number_number)}\b'

    # Combinar ambos patrones en uno solo
    final_pattern = rf'({volume_pattern}|{number_pattern})'

    return final_pattern

# Ejemplo de uso
volume_info = 'vol. 9, no. 1'
pattern = build_pattern_volume(volume_info)

# Prueba del patrón con una cadena de ejemplo
text = 'Vol. 9 No. 1 /'
matches = re.findall(pattern, text, re.IGNORECASE)

if matches:
    print("Se encontraron coincidencias:", matches)
else:
    print("No se encontraron coincidencias.")
