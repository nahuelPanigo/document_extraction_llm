from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[0]

MODEL_PARAMETERS = {
    "LOCATION" : ROOT_DIR / "fine-tuned-model",
#    "NAME" :"vgaraujov/led-base-16384-spanish",
#    "NAME" :"allenai/led-large-16384",
    "NAME" : "allenai/led-base-16384",
    "MAX_TOKENS_INPUT" : 2048,
    "MAX_TOKENS_OUTPUT" : 512 
}


FILETYPES = [".pdf", ".docx"]


HEADER_PROMPT = """ Extract the metadata from the text and provide it in JSON format:
You have to extract the metadata:
language, title, subtitle, creator, subject, rights, rightsurl, date, originPlaceInfo,isrelatedwith"""

#dc.uri, sedici.uri,

MIDDLE_PROMPT = """Here is a JSON Example format:"""

END_PROMPT = """Now, extract the information from the following text and provide it in the specified JSON format:"""


SCHEMA_GENERAL = """ {
        "language": "",
        "keywords": "",
        "creator": "",
        "title": "",
        "subtitle": "",
        "subject": "",
        "rights": "",
        "rightsurl" : "",
        "date": "",
        "originPlaceInfo.": "",
        "isRelatedWith": ""
}"""

        # "dc.uri": "",
        # "sedici.uri": "",

JSON_GENERAL = {
  "language": "es",
#  "keywords": "['Energía eólica', 'modelos analíticos de estelas', 'eficiencia del parque', 'validación de modelos']",
  "title": "SIMULACIÓN MEDIANTE MODELOS ANALÍTICOS DE ESTELA EN PARQUES EÓLICOS Y VALIDACIÓN CON MEDICIONES DEL PARQUE EÓLICO RAWSON",
  "subtitle": "Estadisticas y Desempeño de los Modelos Analíticos de Estelas",
  "creator": "['Lazzari, Florencia', 'Otero, Alejandro']",
  "subject": "Otras ingenierías y tecnologías",
  "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
  "rightsurl" : "http://creativecommons.org/licenses/by-nc-sa/4.0/",
#  "dc.uri": "http://sedici.unlp.edu.ar/handle/10915/108413",
#  "sedici.uri": "http://portalderevistas.unsa.edu.ar/index.php/averma/article/view/1213",
  "date": "2018-01-01",
  "originPlaceInfo": "ASADES",
  "isRelatedWith": "http://sedici.unlp.edu.ar/handle/10915/128795",
}

PROMPT_GENERAL = f"""{HEADER_PROMPT}{MIDDLE_PROMPT}{JSON_GENERAL}{END_PROMPT}"""


SCHEMA_TESIS = """ {
        "language": "",
        "keywords": "",
        "creator": "",
        "title": "",
        "subtitle": "",
        "subject": "",
        "rights": "",
        "rightsurl" : "",
        "date": "",
        "originPlaceInfo.": "",
        "isRelatedWith": "",
        "codirector": "",
        "director": "",
        "degree.grantor": "",
        "degree.name": ""
}"""

        # "dc.uri": "",
        # "sedici.uri": "",

JSON_TESIS = {
        "language": "es",
#        "keywords": "['Sistemas silvopastoriles', 'Eucalyptus', 'Pastizal natural', 'Sistema Nelder modificado', 'Pampa deprimida']",
        "title": "¿Es compatible la producción forestal con la producción forrajera en plantaciones de Eucalyptus híbrido?",
        "subtitle": "Una experiencia para la provincia de Buenos Aires",
        "creator": "Siccardi, Bárbara",
        "subject": "Agricultura,silvicultura y pesca",
        "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
        "rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
#        "dc.uri": "http://sedici.unlp.edu.ar/handle/10915/159750",
        "date": "2023-01-01",
        "originPlaceInfo": "Facultad de Ciencias Agrarias y Forestales",
        "isRelatedWith": "http://sedici.unlp.edu.ar/handle/10915/118764",
        "codirector": "Ing. Agr. Bárbara Heguy",
        "director": "Dra. Carolina Pérez",
        "degree.grantor": "Universidad Nacional de La Plata",
        "degree.name": "Ingeniero Forestal",
   },


PROMPT_TESIS = f"""{HEADER_PROMPT} ,codirector, director,degree.grantor, degree.name
{MIDDLE_PROMPT}{JSON_TESIS}{END_PROMPT}"""


SCHEMA_ARTICULO = """ {
        "language": "",
        "keywords": "",
        "creator": "",
        "title": "",
        "subtitle": "",
        "subject": "",
        "rights": "",
        "rightsurl" : "",
        "date": "",
        "originPlaceInfo.": "",
        "isRelatedWith": "",
        "journalTitle": "",
        "journalVolumeAndIssue": "",
        "issn": "",
        "event": ""
}"""

        # "dc.uri": "",
        # "sedici.uri": "",


JSON_ARTICULO = {
        "language": "en",
#        "keywords": "['stars: activity', 'stars: rotation', 'stars: solar-type']",
        "creator": "['J.I. Soto', 'S.V. Jeffers', 'D.R.G. Schleicher', 'J.A. Rosales']",
        "title": "Exploring the magnetism of stars using TESS data",
        "subtitle": "A new method for the detection of magnetic fields in stars",
        "subject": "Ciencias físicas",
        "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
        "rightsurl" : "http://creativecommons.org/licenses/by-nc-sa/4.0/",
  #      "dc.uri": "http://sedici.unlp.edu.ar/handle/10915/168246",
 #       "sedici.uri": "http://portalderevistas.unsa.edu.ar/index.php/averma/article/view/1213",
        "date": "2022-01-01",
        "originPlaceInfo.": "Asociación Argentina de Astronomía",
        "isRelatedWith": "http://sedici.unlp.edu.ar/handle/10915/118464",
        "journalTitle": "Boletín de la Asociación Argentina de Astronomía",
        "journalVolumeAndIssue": "Vol. 63",
        "issn": "1669-9521",
        "event": "LXIII Reunión Anual de la Asociación Argentina de Astronomía (Córdoba, 25 al 29 de octubre de 2021)",
    },

PROMPT_ARTICULO = f"""{HEADER_PROMPT}, journalTitle, journalVolumeAndIssue, issn, event
{MIDDLE_PROMPT}{JSON_ARTICULO}{END_PROMPT}"""


SCHEMA_LIBRO =  """
{
        "language": "",
        "keywords": "",
        "creator": "",
        "title": "",
        "subtitle": "",
        "subject": "",
        "rights": "",
        "rightsurl" : "",
        "date": "",
        "originPlaceInfo.": "",
        "isRelatedWith": "",
        "publisher": "",
        "isbn": "",
        "compiler": ""
}"""
        # "dc.uri": "",
        # "sedici.uri": "",


JSON_LIBRO =  {
        "language": "es",
#        "keywords": "['Genotoxicología', 'Xenobióticos']",
        "creator": "['Ruiz de Arcaute, Celeste', 'Laborde, Milagros Rosa Raquel', 'Soloneski, Sonia María Elsa', 'Larramendy, Marcelo Luis']",
        "title": "Genotoxicidad y carcinogénesis",
        "subtitle": "Estudios de la genética toxicológica",
        "subject": "Ciencias biológicas",
        "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
        "rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
 #       "dc.uri": "http://sedici.unlp.edu.ar/handle/10915/131176",
#        "sedici.uri": "http://portalderevistas.unsa.edu.ar/index.php/averma/article/view/1213",
        "date": "2021-01-01",
        "originPlaceInfo": "['Facultad de Ciencias Naturales y Museo', 'Facultad de Ciencias Exactas']",
        "isRelatedWith": "http://sedici.unlp.edu.ar/handle/10915/118183",
        "publisher": "Editorial de la Universidad Nacional de La Plata (EDULP)",
        "isbn": "978-950-34-1987-8",
        "compiler": "Pedro Carriquiriborde",
    },

PROMPT_LIBRO = f"""{HEADER_PROMPT}, publisher, isbn, compiler
{MIDDLE_PROMPT}{JSON_LIBRO}{END_PROMPT}"""

