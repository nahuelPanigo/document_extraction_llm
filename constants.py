from pathlib import Path
from  pandas import Timestamp


ROOT_DIR = Path(__file__).resolve().parents[0]  
DATA_FOLDER = ROOT_DIR / "data/sedici"
PDF_FOLDER = DATA_FOLDER / "pdfs/"
JSON_FOLDER = DATA_FOLDER / "jsons/"
TXT_FOLDER = DATA_FOLDER / "texts/"
CSV_FOLDER = DATA_FOLDER / "csv/"
RESULT_FOLDER_VALIDATION = ROOT_DIR / "validation/result/"


URL_SERVICES_EXTRACTION = "http://localhost:8000/upload"
DATASET_SEDICI_URL_BASE = "https://sedici.unlp.edu.ar/oai/openaire?verb=ListRecords&resumptionToken=oai_dc////"
DOWNLOAD_URL = "https://sedici.unlp.edu.ar"
PDF_URL = DOWNLOAD_URL + "/bitstream/handle/"
GROBID_URL = "http://localhost:8070/api/processFulltextDocument"


DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED = "sedici_finetunnig_metadata.json"
DATASET_WITH_METADATA = "metadata_sedici.json"
DATASET_WITH_METADATA_AND_TEXT_DOC = "metadata_sedici_and_text.json"
DATASET_TYPE = "dataset_type.json"
CSV_SEDICI = "sedici.csv"
CSV_SEDICI_FILTERED = "sedici_filtered_2019_2024.csv"


LENGTH_DATASET = 2000
SAMPLES_PER_TYPE = 500  # For balanced dataset: 500 per type × 4 types = 2000 total
PERCENTAGE_DATASET_FOR_STEPS = {"training":0.8,"validation":0.1,"test":0.1}

CANT_TOKENS = 14000
TOKENS_LENGTH = 4
VALID_ACCENTS = "áéíóúüñÁÉÍÓÚÜÑ"


APROX_TOK_PER_SOL = 2500

VALID_TYPES = ["Libro", "Tesis", "Articulo","Objeto de conferencia"]

COLUMNS_TYPES = {
    #general
    'id' : {"type": str,"rename": "id",'cant' : "unique","DCMIID":"id","rename": "id"},
    'dc.type' : {'type':str,'cant' : "unique","DCMIID":"dc.type","rename": "dc.type"},
    #'dc.description.abstract' : {'type':str,'cant' : "many","DCMIID":"dc.description","rename": "abstract"},
    'dc.language' : {'type':str,'cant' : "unique","DCMIID":"dc.language","rename": "language"},
    'sedici.subject.materias' : {'type':str,'cant' : "unique","DCMIID":"dc.subject","rename": "subject"},
    'dc.title' : {'type':str,'cant' : "unique","DCMIID":"dc.title","rename": "title"},
    'sedici.creator.person' : {'type':str,'cant' : "unique","DCMIID":"dc.creator","rename": "creator"},
    'dc.subject' : {'type':str,'cant' : "unique","DCMIID":"dc.subject","rename": "keywords"},
    'sedici.rights.license' : {'type':str,'cant' : "unique","DCMIID":"dc.rights","rename": "rights"},
    'sedici.rights.uri' : {'type':str,'cant' : "unique","DCMIID":"dc.rights","rename": "rightsurl"},
    'sedici.identifier.uri' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier","rename": "sedici.uri"},
    'dc.identifier.uri' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier","rename": "dc.uri"},
    'dc.date.issued' : {'type': "str",'cant' : "unique","DCMIID":"dc.date","rename": "date"},
    'mods.originInfo.place' : {'type':str,'cant' : "unique","DCMIID":"mods.originInfo.place","rename": "originPlaceInfo"},
    'sedici.relation.isRelatedWith' : {'type':str,'cant' : "unique","DCMIID":"dc.relation","rename": "isrelatedwith"},
    #general except article    
    'sedici.contributor.colaborator' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor","rename": "colaborator"},
    #thesis
    'sedici.contributor.codirector' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor","rename": "codirector"},
    'sedici.contributor.director' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor","rename": "director"},
    'thesis.degree.grantor' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor.degree.grantor","rename": "degree.grantor"},
    'thesis.degree.name' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor.degree.name","rename": "degree.name"},
    'sedici.institucionDesarrollo' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor","rename": "institucionDesarrollo"},
    #books
    'dc.publisher' : {'type':str,'cant' : "unique","DCMIID":"dc.publisher","rename": "publisher"},
    'sedici.identifier.isbn' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier","rename": "isbn"},
    'sedici.contributor.compiler' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor","rename": "compiler"},
    'sedici.contributor.editor' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor","rename": "editor"},
    #article
    'sedici.relation.journalTitle' : {'type':str,'cant' : "unique","DCMIID":"dc.title","rename": "journalTitle"},
    'sedici.relation.journalVolumeAndIssue' : {'type':str,'cant' : "unique","DCMIID":"dc.relation.journalVolumeAndIssue","rename": "journalVolumeAndIssue"},
    'sedici.identifier.issn' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier","rename": "issn"},    
    'sedici.relation.event' : {'type':str,'cant' : "unique","DCMIID":"dc.relation","rename": "event"},
    #'dc.coverage.spatial' : {'type':str,'cant' : "unique","DCMIID":"dc.coverage","rename": ""},
    #'dc.coverage.temporal' : {'type':str,'cant' : "unique","DCMIID":"dc.coverage","rename": ""},
    #'dc.description.filiation' : {'type':str,'cant' : "unique","DCMIID":"dc.description.filiation","rename": ""},
    #'dc.subject.ford' : {'type':str,'cant' : "unique","DCMIID":"dc.subject","rename": "subject"}
}



FORD_SEDICI_MATERIAS = {"Geofísica":"Ciencias físicas","Administración":"Economía y negocios","Agrimensura":"Ciencias de la tierra y ciencias ambientales relacionadas","Antropología":"Otras humanidades","Arqueología":"Historia y arqueología","Arquitectura":"Ingeniería civil","Artes Audiovisuales":"Artes","Artes Plásticas":"Artes","Artes y Humanidades":"Artes","Astronomía":"Ciencias físicas","Bellas Artes":"Artes","Bibliotecología y ciencia de la información":"Geografía social y económica","Bibliotecología":"Geografía social y económica","Biología":"Ciencias biológicas","Bioquímica":"Ciencias biológicas","Botánica":"Ciencias biológicas","Ciencias Agrarias":"Agricultura,silvicultura y pesca","Ciencias Astronómicas":"Ciencias físicas","Ciencias de la Educación":"Educación","Ciencias Económicas":"Economía y negocios","Ciencias Exactas":"Ciencias físicas","Ciencias Informáticas":"Ciencias de la computación e información","Ciencias Jurídicas":"Derecho","Ciencias Médicas":"Medicina básica","Ciencias Naturales":"Ciencias biológicas","Ciencias Sociales":"Sociología","Ciencias Veterinarias":"Ciencia veterinaria","Comunicación Social":"Geografía social y económica","Comunicación Visual":"Geografía social y económica","Comunicación":"Geografía social y económica","Contabilidad":"Economía y negocios","Cooperativismo":"Economía y negocios","Cs de la Computación":"Ciencias de la computación e información","Cs. Agrícolas y Biológicas":"Ciencias biológicas","Cs. Ambientales":"Ciencias de la tierra y ciencias ambientales relacionadas","Cs. de la Tierra y Planetarias":"Ciencias de la tierra y ciencias ambientales relacionadas","Cs. de los Materiales":"Ingeniería de los materiales","Cs. Sociales":"Sociología","Derecho":"Derecho","Derechos Humanos":"Derecho","Desarrollo Regional":"Otras ciencias sociales","Diseño Industrial":"Biotecnología industrial","Ecología":"Biotecnología ambiental","Econometría y Finanzas":"Economía y negocios","Economía":"Economía y negocios","Educación Física":"Educación","Educación":"Educación","Electrotecnia":"Ingeniería eléctrica, electrónica e informática","Energía":"Ingenieria ambiental","Farmac.":"Biotecnología médica","Farmacia":"Biotecnología médica","Filosofía":"Filosofía, ética y religión","Física y Astronomía":"Ciencias físicas","Física":"Ciencias físicas","Genética y Biología Molecular":"Ciencias biológicas","Geografía":"Otras ciencias sociales","Geología":"Ciencias de la tierra y ciencias ambientales relacionadas","Gestión y Contabilidad":"Economía y negocios","Historia del Arte":"Artes","Historia":"Historia y arqueología","Humanidades":"Otras humanidades","Información":"Geografía social y económica","Informática":"Ciencias de la computación e información","Ingeniería Aeronáutica":"Ingeniería mecánica","Ingeniería Agronómica":"Agricultura,silvicultura y pesca","Ingeniería Civil":"Ingeniería civil","Ingeniería Electrónica":"Ingeniería eléctrica, electrónica e informática","Ingeniería en Materiales":"Ingeniería de los materiales","Ingeniería Forestal":"Agricultura,silvicultura y pesca","Ingeniería Hidráulica":"Ingeniería civil","Ingeniería Mecánica":"Ingeniería mecánica","Ingeniería Química":"Ingeniería química","Ingeniería":" Otras ingenierías y tecnologías","Inmunología y Microbiología":"Ciencias biológicas","Legislación":"Derecho","Letras":"Lenguas y literatura","Matemática":"Matemáticas","Medicina":"Medicina clínica","Medios de Comunicación":"Geografía social y económica","Multidisciplina":"Otras humanidades","Multimedia":"Geografía social y económica","Música":"Artes","Negocios":"Economía y negocios","Neurociencia":"Psicología y ciencias cognitivas","Odontología":"Medicina clínica","Paleontología":"Ciencias de la tierra y ciencias ambientales relacionadas","Periodismo":"Geografía social y económica","Política":"Ciencia política","Profesiones de la Salud":"Ciencias de la salud","Psicología":"Psicología y ciencias cognitivas","Psiquiatría":"Medicina clínica","Química":"Ciencias químicas","Redes y Seguridad":"Ciencias de la computación e información","Relaciones Internacionales":"Ciencia política","Salud":"Ciencias de la salud","Sociología Jurídica":"Derecho","Sociología":"Sociología","Software":"Ciencias de la computación e información","Toxicología y Farmacia":"Biotecnología médica","Trabajo Social":"Sociología","Turismo":"Medios de comunicación","Urbanismo":"Ingeniería civil","Veterinaria":"Ciencia veterinaria","Zoología":"Ciencias biológicas","Zoonosis":"Ciencia veterinaria"}


BASE_MODEL_LED="allenai/led-base-16384"
BASE_MODEL_LED_LARGE="allenai/led-large-16384"
BASE_MODEL_LED_SPANISH="vgaraujov/led-base-16384-spanish"
BASE_MODEL_GEMMA="google/gemma-3-1b-pt"
BASE_MODEL_LLAMA="meta-llama/Llama-3.2-1B"
BASE_MODEL_MISTRAL="mistralai/Mistral-7B-v0.1"
BASE_MODEL_DEEPSEK_QWEN="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
BASE_MODEL_NUEXTRACT="numind/NuExtract-tiny"
BASE_MODEL_T5="google-t5/t5-base"

MAX_TOKENS_INPUT= 2048
MAX_TOKENS_OUTPUT= 512
LOG_DIR = ROOT_DIR /  "log"
FINAL_MODEL_PATH =ROOT_DIR / "fine-tuned-model-With-Objeto-Conferencia"
CHECKPOINT_MODEL_PATH = ROOT_DIR / "results"


PROMPT_CLEANER_METADATA = """
You are an expert in metadata validation and text analysis. Your task is to process a given text and a JSON object containing metadata. Follow these steps precisely:

1. Analyze the provided text and metadata object.

2. For each key-value pair in the metadata:
    - Search the text for the metadata value (or a variation of it, such as differences in case, abbreviations, punctuation, or word order).
    - If the value exists in the text but is written differently, update the metadata value to match the exact appearance in the text.
    - If the value does not appear in the text, remove that key from the metadata.
    - for sedici.uri dc.uri and isrelatedwith must be exactly the same if not match exactly the same just put like null

3. Ensure all metadata values in the JSON object match their exact appearance in the text.

4. Return **only** the corrected JSON schema. Do not include explanations, comments, the original text, or the original metadata. The output first char must be '{' and the last one'}'

Input example:
- Text: "This paper was written by Juan M. Pérez in 2024."
- Metadata: {"creator": "Perez, Juan Manuel", "date": "2024", "journalTitle": "Journal of AI Research"}

Output example:
{"creator": "Juan M. Pérez", "date": "2024"}

Input example:
- Text: "Dr. María García collaborated with John O'Connor to publish this work in 2023."
- Metadata: {"creator":["Garcia, Maria", "OConnor, John"], "date": "2023", "publisher": "AI Press"}

Output example:
{"creator": ["María García", "John O'Connor"], "date": "2023"}

you must pay attention in the json provided after this:
"""


PROMPT_UPPERFORM_GENERAL = """
Eres un asistente experto en diseño y optimización de prompts para agentes LLM orientados a tareas especializadas. Tu tarea es mejorar prompts existentes para que el agente cumpla con mayor precisión los objetivos definidos.

Vas a recibir un bloque de entrada estructurado con las siguientes secciones:

<INSTRUCTS> Contiene la consigna original que describe el propósito del agente y los objetivos que debe cumplir. 
</INSTRUCTS>

<ACTUAL_PROMPT> Contiene el prompt actual utilizado por el agente, que será objeto de mejora.
</ACTUAL_PROMPT>

<RESULTS_OBTAINED> Contiene una muestra de los resultados reales que está generando el agente al ejecutar ese prompt.
</RESULTS_OBTAINED>

<EXPECTED_RESULTS> Contiene los resultados esperados, es decir, la salida correcta que el agente debería generar si el prompt estuviera bien diseñado.
</EXPECTED_RESULTS>

### TU TAREA

Tu objetivo es mejorar el contenido dentro de `<ACTUAL_PROMPT>` para que el agente, al recibir el mismo tipo de entrada, genere resultados más cercanos o idénticos a los de `<EXPECTED_RESULTS>`, corrigiendo los desvíos observados en `<RESULTS_OBTAINED>`.

Sigue estas instrucciones al pie de la letra:

1. **Analiza la brecha** entre `<RESULTS_OBTAINED>` y `<EXPECTED_RESULTS>`. Identifica omisiones, errores de formato, inferencias erróneas, o falta de precisión en los metadatos extraídos.
2. **Evalúa el prompt actual** dentro de `<ACTUAL_PROMPT>` y detecta si hay ambigüedad, falta de instrucciones, tono incorrecto, o necesidad de ejemplos.
3. **Rediseña completamente el prompt si es necesario**, o edítalo puntualmente si se puede corregir manteniendo su estructura.

"""

PROMPT_UPPERFORM_GENERAL_GUARDIALS = """
Tu salida debe ser únicamente el nuevo prompt mejorado, sin explicaciones adicionales.
Recuerda: el resultado de tu trabajo será usado como el nuevo prompt de producción para este agente. No debes comentar ni justificar tus cambios. Solo devuelve el prompt optimizado final.
"""

PROMPT_UPPERFORM_METADATA = PROMPT_UPPERFORM_GENERAL + """
4. Asegúrate de que el nuevo prompt:
   - Sea claro y específico para el tipo de documento (tesis, artículo, etc.).
   - Incluya ejemplos si pueden ayudar a guiar mejor al modelo.
   - Incluya instrucciones explícitas sobre el **formato de salida** y los **campos obligatorios de metadatos**.
   - Oriente al modelo a **ignorar contenido irrelevante** (por ejemplo, encabezados institucionales repetitivos, números de página, bibliografía, etc.).

Este agente se aplica en el dominio de extracción de metadatos académicos, por lo tanto:
- Asegúrate de cubrir campos típicos como: título, autor, fecha, resumen, palabras clave, tipo de documento, idioma, universidad, carrera, etc.
- Distingue entre tipos de documentos si corresponde (ej. artículo vs tesis) y adapta la instrucción si es posible.

""" + PROMPT_UPPERFORM_GENERAL_GUARDIALS




PROMPT_UPPERFORM_DATE = """
Eres un experto en diseño de prompts para LLMs orientados a tareas de extracción de metadatos.

Recibirás un conjunto estructurado con:
<INSTRUCTS> Instrucciones de la tarea
<ACTUAL_PROMPT> Prompt actual que está fallando
<RESULTS_OBTAINED> Lo que devuelve el modelo con ese prompt
<EXPECTED_RESULTS> Lo que debería haber devuelto si el prompt fuera correcto

### TU TAREA

Debes rediseñar el prompt dentro de <ACTUAL_PROMPT> para que el modelo LLM:

1. Extraiga **exclusivamente** el valor `date` desde un texto cualquiera.
2. Ignore contenido irrelevante o ambiguo (como encabezados, bibliografía, fechas de eventos o notas al pie).
3. Devuelva el valor `"null"` si no puede identificar con claridad una fecha válida.
4. Cumpla con el formato estricto:
   - `"YYYY-MM-DD"` si día, mes y año están presentes
   - `"YYYY-MM"` si sólo mes y año
   - `"YYYY"` si solo el año
5. **No debe incluir el texto fuente en el prompt**. El prompt debe ser una plantilla que funcione con cualquier texto nuevo.

Incluye ejemplos en el prompt si pueden ayudar al modelo a mejorar la precisión.

🔴 **Devuelve únicamente el nuevo prompt, como string sin envolverlo en comillas, sin formatearlo como código, sin incluir el texto original.**
🔴 **No incluyas codigo python ni explicaciones de tus decisiones.**
🔴 **No intentes extraer la fecha o agregar algun dato del texto que viene en el rasonamiento de `RESULTS_OBTAINED`.**
"""


# HEADER_PROMPT = """Extract the metadata from the text and provide it in JSON format.
# You have to extract the following metadata fields only if you are confident in their accuracy:
# language, cretor, rights, rightsurl, originPlaceInfo, isrelatedwith"""


# JSON_GENERAL = {
#     "language": "es",
#     "creator": "['Lazzari, Florencia', 'Otero, Alejandro']",
#     "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
#     "rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
#     "originPlaceInfo": "Universidad Nacional de La Plata",
#     "isrelatedwith": "http://sedici.unlp.edu.ar/handle/10915/118183",
# }

# PROMPT_GENERAL = f"""{HEADER_PROMPT}
# {MIDDLE_PROMPT}{JSON_GENERAL}{END_PROMPT}"""


# JSON_TESIS = {
#     "language": "es",
#     "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
#     "rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
#     "originPlaceInfo": "Facultad de Ciencias Agrarias y Forestales",
#     "isrelatedwith": "http://sedici.unlp.edu.ar/handle/10915/118764",
#     "director": "Dra. Carolina Pérez",
#     "codirector": "Ing. Agr. Bárbara Heguy",
#     "degree.grantor": "Universidad Nacional de La Plata",
#     "degree.name": "Ingeniero Forestal",
# }

# PROMPT_TESIS = f"""{HEADER_PROMPT}, director, codirector, degree.grantor, degree.name
# {MIDDLE_PROMPT}{JSON_TESIS}{END_PROMPT}"""

# JSON_LIBRO = {
#     "language": "es",
#     "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
#     "rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
#     "originPlaceInfo": "Facultad de Ciencias Naturales y Museo",
#     "isrelatedwith": "http://sedici.unlp.edu.ar/handle/10915/118183",
#     "dc.publisher": "Editorial de la Universidad Nacional de La Plata (EDULP)",
#     "isbn": "978-950-34-1987-8",
#     "compiler": "Pedro Carriquiriborde"
# }

# PROMPT_LIBRO = f"""{HEADER_PROMPT}, dc.publisher, isbn, compiler
# {MIDDLE_PROMPT}{JSON_LIBRO}{END_PROMPT}"""


# JSON_ARTICULO = {
#     "language": "es",
#     "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
#     "rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
#     "originPlaceInfo": "Asociación Argentina de Astronomía",
#     "isrelatedwith": "http://sedici.unlp.edu.ar/handle/10915/118464",
#     "journalTitle": "Boletín de la Asociación Argentina de Astronomía",
#     "journalVolumeAndIssue": "Vol. 63",
#     "issn": "1669-9521",
#     "event": "LXIII Reunión Anual de la Asociación Argentina de Astronomía (Córdoba, 25 al 29 de octubre de 2021)"
# }

# PROMPT_ARTICULO = f"""{HEADER_PROMPT}, journalTitle, journalVolumeAndIssue, issn, event
# {MIDDLE_PROMPT}{JSON_ARTICULO}{END_PROMPT}"""


# HEADER_PROMPT_SEMANTICO = """Extract the following metadata from the text and return them in a JSON format:

# - title
# - abstract
# - keywords
# - subject

# Return only the fields you can infer with high confidence from the text. If you are not sure about a field, leave it out of the JSON.
# """

# JSON_SEMANTICO = {
#     "title": "Estudio sobre los patrones de migración en comunidades indígenas del NEA: Una mirada intercultural desde la antropología urbana",
#     "abstract": "Este trabajo analiza los procesos de desplazamiento urbano de familias Qom...",
#     "keywords": ["migración", "pueblos originarios", "interculturalidad", "antropología urbana"],
#     "subject": "Antropología social"
# }

# PROMPT_SEMANTICO = f"""{HEADER_PROMPT_SEMANTICO}
# {MIDDLE_PROMPT}{JSON_SEMANTICO}{END_PROMPT}"""



# HEADER_PROMPT_DATE = """Extract the publication date from the following text **only if you are completely sure**.

# The date must refer to the official publication or creation of the document.

# If the date is ambiguous, conflicting, or not clearly present, return `"null"`.

# if it presetnt month and day format as: "YYYY-MM-DD", if only present month and year format as: "YYYY-MM", if only present year format as: "YYYY"
# """

# JSON_DATE = {
#     "date": "2018-05-10"
# }

# PROMPT_DATE = f"""{HEADER_PROMPT_DATE}
# {MIDDLE_PROMPT}{JSON_DATE}{END_PROMPT}"""

HEADER_PROMPT = """ Extract the metadata from the text and provide it in JSON format:
You have to extract the metadata:
language, title,  creator, subject, rights, rightsurl, date, originPlaceInfo,isrelatedwith"""

#dc.uri, sedici.uri,subtitle,


MIDDLE_PROMPT = """Here is a JSON Example format:"""

END_PROMPT = """Now, extract the information from the following text and provide it in the specified JSON format:"""


JSON_GENERAL = {
  "language": "es",
#  "keywords": "['Energía eólica', 'modelos analíticos de estelas', 'eficiencia del parque', 'validación de modelos']",
  "title": "SIMULACIÓN MEDIANTE MODELOS ANALÍTICOS DE ESTELA EN PARQUES EÓLICOS Y VALIDACIÓN CON MEDICIONES DEL PARQUE EÓLICO RAWSON",
#  "subtitle": "Estadisticas y Desempeño de los Modelos Analíticos de Estelas",
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



JSON_TESIS = {
        "language": "es",
#        "keywords": "['Sistemas silvopastoriles', 'Eucalyptus', 'Pastizal natural', 'Sistema Nelder modificado', 'Pampa deprimida']",
        "title": "¿Es compatible la producción forestal con la producción forrajera en plantaciones de Eucalyptus híbrido?",
#        "subtitle": "Una experiencia para la provincia de Buenos Aires",
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


JSON_ARTICULO = {
        "language": "en",
#        "keywords": "['stars: activity', 'stars: rotation', 'stars: solar-type']",
        "creator": "['J.I. Soto', 'S.V. Jeffers', 'D.R.G. Schleicher', 'J.A. Rosales']",
        "title": "Exploring the magnetism of stars using TESS data",
#        "subtitle": "A new method for the detection of magnetic fields in stars",
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


JSON_OBJECTO_CONFERENCIA = {
        "language": "en",
#        "keywords": "['stars: activity', 'stars: rotation', 'stars: solar-type']",
        "creator": "['J.I. Soto', 'S.V. Jeffers', 'D.R.G. Schleicher', 'J.A. Rosales']",
        "title": "Exploring the magnetism of stars using TESS data",
#       "subtitle": "A new method for the detection of magnetic fields in stars",
        "subject": "Ciencias físicas",
        "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
        "rightsurl" : "http://creativecommons.org/licenses/by-nc-sa/4.0/",
  #      "dc.uri": "http://sedici.unlp.edu.ar/handle/10915/168246",
 #       "sedici.uri": "http://portalderevistas.unsa.edu.ar/index.php/averma/article/view/1213",
        "date": "2022-01-01",
        "originPlaceInfo.": "Asociación Argentina de Astronomía",
        "isRelatedWith": "http://sedici.unlp.edu.ar/handle/10915/118464",
        "issn": "1669-9521",
        "event": "LXIII Reunión Anual de la Asociación Argentina de Astronomía (Córdoba, 25 al 29 de octubre de 2021)",
    },

PROMPT_OBJECTO_CONFERENCIA = f"""{HEADER_PROMPT}, issn, event
{MIDDLE_PROMPT}{JSON_OBJECTO_CONFERENCIA}{END_PROMPT}"""


JSON_LIBRO =  {
        "language": "es",
#        "keywords": "['Genotoxicología', 'Xenobióticos']",
        "creator": "['Ruiz de Arcaute, Celeste', 'Laborde, Milagros Rosa Raquel', 'Soloneski, Sonia María Elsa', 'Larramendy, Marcelo Luis']",
        "title": "Genotoxicidad y carcinogénesis",
#        "subtitle": "Estudios de la genética toxicológica",
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


SCHEMA_LIBRO =  """
{
        "language": "",
        "keywords": "",
        "creator": "",
        "title": "",
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


SCHEMA_ARTICULO = """ {
        "language": "",
        "keywords": "",
        "creator": "",
        "title": "",
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

SCHEMA_OBJECTO_CONFERENCIA = """ {
        "language": "",
        "keywords": "",
        "creator": "",
        "title": "",
        "subject": "",
        "rights": "",
        "rightsurl" : "",
        "date": "",
        "originPlaceInfo.": "",
        "isRelatedWith": "",
        "issn": "",
        "event": ""
}"""




        # "dc.uri": "",
        # "sedici.uri": "",


SCHEMA_TESIS = """ {
        "language": "",
        "keywords": "",
        "creator": "",
        "title": "",
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


SCHEMA_GENERAL = """ {
        "language": "",
        "keywords": "",
        "creator": "",
        "title": "",
        "subject": "",
        "rights": "",
        "rightsurl" : "",
        "date": "",
        "originPlaceInfo.": "",
        "isRelatedWith": ""
}"""

        # "dc.uri": "",
        # "sedici.uri": "",
