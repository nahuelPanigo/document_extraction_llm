import re
import unicodedata


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


def normalice_text(text):
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

def normalice_keys(json):
    keys = {"dc.language" : "language", "dc.subject": "keywords","dc.title" : "title" ,"dc.title.subtitle" : "subtitle" , "sedici.creator.person" : "creator" , "dc.subject.ford" : "subject",
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
