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


#  PROMPT ="""**Task:** Extract metadata from the given text and provide it in JSON format. Below are the possible metadata fields with their respective DCMI standards. Select valid values for fields with specific sets of possibilities, such as `dc.type` and `dc.subject.ford`.

#  **Metadata Fields and DCMI Standards:**
#  - `'sedici.rights.license'`: `dc.rights`
#  - `'sedici.rights.uri'`: `dc.rights`
#  - `'sedici.relation.isRelatedWith'`: `dc.relation`
#  - `'sedici.identifier.uri'`: `dc.identifier`
#  - `'dc.identifier.uri'`: `dc.identifier`
#  - `'sedici.contributor.editor'`: `dc.contributor`
#  - `'sedici.contributor.compiler'`: `dc.contributor`
#  - `'dc.publisher'`: `dc.publisher`
#  - `'dc.date.issued'`: `dc.date`
#  - `'sedici.contributor.colaborator'`: `dc.contributor`
#  - `'sedici.institucionDesarrollo'`: `dc.contributor`
#  - `'thesis.degree.name'`: `dc.contributor.degree.name`
#  - `'thesis.degree.grantor'`: `dc.contributor.degree.grantor`
#  - `'sedici.relation.event'`: `dc.relation`
#  - `'sedici.identifier.isbn'`: `dc.identifier`
#  - `'sedici.identifier.issn'`: `dc.identifier`
#  - `'dc.title'`: `dc.title`
#  - `'sedici.title.subtitle'`: `dc.title`
#  - `'sedici.creator.person'`: `dc.creator`
#  - `'dc.language'`: `dc.language`
#  - `'dc.subject'`: `dc.subject`
#  - `'sedici.contributor.director'`: `dc.contributor`
#  - `'sedici.contributor.codirector'`: `dc.contributor`
#  - `'dc.type'`: `dc.type` (Possible values: `libro`, `articulo`, `objeto de confferencia`, `tesis`)
#  - `'sedici.relation.journalTitle'`: `dc.title`
#  - `'sedici.relation.journalVolumeAndIssue'`: `dc.relation.journalVolumeAndIssue`
#  - `'mods.originInfo.place'`: `mods.originInfo.place`
#  - `'dc.subject.ford'`: `dc.subject` (Refer to the Fields of Research and Development classification for possible values.)

#  **Example JSON Output:**
#  ```json
#  {
#    "dc.language": "value",
#    "dc.subject": "value",
#    "dc.title": "value",
#    "dc.type": "value",
#    "sedici.creator.person": "value",
#    "dc.subject.ford": "value",
#    "sedici.contributor.director": "value",
#    "sedici.contributor.codirector": "value",
#    "sedici.title.subtitle": "value",
#    "sedici.relation.journalVolumeAndIssue": "value",
#    "sedici.relation.journalTitle": "value",
#    "sedici.identifier.issn": "value"
#  }

#  """

#  PROMPT = """ You’re an advanced data extractor with expertise in structuring and formatting information into JSON format from various texts. You have a keen eye for detail and can recognize essential and optional keys needed for accurate data representation.
#  Your task is to extract specific information from a given text and present it in the required JSON format.

#  Metadata posible Fields:

#  -'sedici.rights.license'
#  -'sedici.rights.uri'
#  -'sedici.relation.isRelatedWith'
#  -'sedici.identifier.uri
#  -'dc.identifier.uri'
#  -'sedici.contributor.editor'
#  -'sedici.contributor.compiler'
#  -'dc.publisher'`
#  -'dc.date.issued'
#  -'sedici.contributor.colaborator'
#  -'sedici.institucionDesarrollo'
#  -'thesis.degree.name'
#  -'thesis.degree.grantor'
#  -'sedici.relation.event'
#  -'sedici.identifier.isbn'
#  -'sedici.identifier.issn'
#  -'dc.title'
#  -'sedici.title.subtitle'
#  -'sedici.creator.person'
#  -'dc.language'
#  -'dc.subject'
#  -'sedici.contributor.director'
#  -'sedici.contributor.codirector'
#  -'dc.type' (Possible values: `Libro`, `Articulo`, `Objeto de confferencia`, `Tesis`)
#  -'sedici.relation.journalTitle'
#  -'sedici.relation.journalVolumeAndIssue'
#  -'mods.originInfo.place'
#  -'dc.subject.ford' (a unique subject Refer to the Fields of Research and Development classification for possible values)

#  **Example JSON Output:**
#  ```json
#  {
#    "dc.language": "es",
#    "dc.subject.ford": "Psicología y ciencias cognitivas",
#    "dc.subject": "['Subjetividad', 'Infancias institucionalizadas', 'Salud mental']",
#    "dc.title": "Infancias institucionalizadas en casas de abrigo",
#    "dc.type": "Articulo",
#    "sedici.creator.person": "['Gastaminza, Florencia', 'Pérez, Edith Alba']",
#    "dc.subject.ford": "Psicología y ciencias cognitivas",
#    "sedici.relation.journalTitle": "Investigación Joven",
#    "sedici.relation.journalVolumeAndIssue": "Vol 6 (especial)",
#    "mods.originInfo.place": "Universidad Nacional de La Plata",
#    "sedici.identifier.issn": "2314-3991",
#    "dc.date.issued": "2019",
#    "sedici.rights.license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
#    "sedici.rights.uri": "http://creativecommons.org/licenses/by/4.0/",
#    "sedici.title.subtitle": "Una propuesta preliminar en el campo de las políticas públicas, la salud mental y el género"
#  }

#  you must extract the metadata in json format of the following document.

#  """

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

