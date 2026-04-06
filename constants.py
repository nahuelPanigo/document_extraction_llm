from pathlib import Path
from  pandas import Timestamp


ROOT_DIR = Path(__file__).resolve().parents[0]  
DATA_FOLDER = ROOT_DIR / "data/sedici"
PDF_FOLDER = DATA_FOLDER / "pdfs/"
JSON_FOLDER = DATA_FOLDER / "jsons/"
TXT_FOLDER = DATA_FOLDER / "texts/"
CSV_FOLDER = DATA_FOLDER / "csv/"
CSV_FORD_SUBJECTS = "ford_subjects.csv"  # legacy reference
CSV_SUBJECTS = "subjects.csv"


SUBJECT_MODEL_FOLDER = ROOT_DIR / "fine_tune_subject/models"
SUBJECT_MODEL_FOLDERS = {
    "svm": SUBJECT_MODEL_FOLDER / "svm",
    "svm_linear": SUBJECT_MODEL_FOLDER / "svm_linear",
    "svm_rbf": SUBJECT_MODEL_FOLDER / "svm_rbf",
    "xgboost": SUBJECT_MODEL_FOLDER / "xgboost", 
    "random_forest": SUBJECT_MODEL_FOLDER / "random_forest",
    "embeddings": SUBJECT_MODEL_FOLDER / "embeddings",
    "embeddings_knn": SUBJECT_MODEL_FOLDER / "embeddings_knn",
    "neural": SUBJECT_MODEL_FOLDER / "neural",
    "minilm": SUBJECT_MODEL_FOLDER / "minilm"
}
SUBJECT_MODEL_RESULTS_FOLDER = ROOT_DIR / "fine_tune_subject/model_results"

# Type classification
TXT_NO_TAGS_FOLDER = DATA_FOLDER / "texts_no_tags/"
CSV_TYPES = "types.csv"
TYPE_MODEL_FOLDER = ROOT_DIR / "fine_tune_type/models"
TYPE_MODEL_FOLDERS = {
    "svm_linear": TYPE_MODEL_FOLDER / "svm_linear",
    "svm_rbf": TYPE_MODEL_FOLDER / "svm_rbf",
    "xgboost": TYPE_MODEL_FOLDER / "xgboost",
    "random_forest": TYPE_MODEL_FOLDER / "random_forest",
    "embeddings": TYPE_MODEL_FOLDER / "embeddings",
    "embeddings_knn": TYPE_MODEL_FOLDER / "embeddings_knn",
    "neural": TYPE_MODEL_FOLDER / "neural",
    "minilm": TYPE_MODEL_FOLDER / "minilm",
}
TYPE_MODEL_RESULTS_FOLDER = ROOT_DIR / "fine_tune_type/model_results"

RESULT_FOLDER_VALIDATION = ROOT_DIR / "validation/result/"


CLEAN_PROVIDER_TO_USE = "openai"  # "genai" or "openai"

GENAI_REQUEST_LIMIT = {
    "req_per_day": 1000,
    "req_per_min": 15,
    "tok_per_min": 250000,
}
GENAI_MODEL = "gemini-2.5-flash"

OPENAI_REQUEST_LIMIT = {
    "req_per_day": 10000,
    "req_per_min": 60,
    "tok_per_min": 200000,
}
OPENAI_MODEL = "gpt-5-mini"

URL_SERVICES_EXTRACTION = "http://localhost:8000/upload"
DATASET_SEDICI_URL_BASE = "https://sedici.unlp.edu.ar/oai/openaire?verb=ListRecords&resumptionToken=oai_dc////"
DOWNLOAD_URL = "https://sedici.unlp.edu.ar"
PDF_URL = DOWNLOAD_URL + "/bitstream/handle/"
GROBID_URL = "http://localhost:8070/api/processFulltextDocument"
GROBID_SERVICE = "http://localhost:8070"
GROBID_FOLDER = RESULT_FOLDER_VALIDATION / "GROBID"


# DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED = "sedici_finetunnig_metadata.json" #final dataset
DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED = "sedici_finetunnig_metadata_with_ocr.json" #final dataset with ocr
# DATASET_WITH_METADATA_AND_TEXT_DOC_CLEANED="metadata_sedici_and_text_cleaned.json" #after cleaning with gemini
DATASET_WITH_METADATA_AND_TEXT_DOC_CLEANED="metadata_sedici_and_text_cleaned_with_ocr.json" #after cleaning with gemini with ocr
DATASET_WITH_METADATA = "metadata_sedici.json" #initial dataset from filtered csv
#DATASET_WITH_METADATA_AND_TEXT_DOC = "metadata_sedici_and_text.json" #initial dataset from filtered csv with text
DATASET_WITH_METADATA_AND_TEXT_DOC = "metadata_sedici_and_text_with_ocr.json" #initial dataset from filtered csv with text with ocr
DATASET_TYPE = "dataset_type.json"
CSV_SEDICI = "sedici.csv"
CSV_SEDICI_FILTERED = "sedici_filtered_2019_2024.csv"


# Model management constants for fine_tune_subject
MODEL_FOLDER = ROOT_DIR / "fine_tune_subject/models"
MODEL_NAMES = {
    'svm': 'svm_classifier.pkl',
    'xgboost': 'xgboost_classifier.pkl', 
    'random_forest': 'subject_classifier.pkl',
    'embeddings': 'embedding_classifier.pkl',
    'neural_torch': 'neural_torch_classifier.pth'
}
VECTORIZER_NAMES = {
    'svm': 'svm_vectorizer.pkl',
    'xgboost': 'xgboost_vectorizer.pkl',
    'random_forest': 'vectorizer.pkl'
}
LABEL_ENCODER_NAMES = {
    'svm': 'svm_label_encoder.pkl', 
    'xgboost': 'xgboost_label_encoder.pkl',
    'random_forest': 'label_encoder.pkl',
    'embeddings': 'embedding_label_encoder.pkl',
    'neural_torch': 'neural_torch_embeddings_and_encoder.pkl'
}


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

# Active subject mapping — change this to swap to a different classification standard
SUBJECT_MAPPING = FORD_SEDICI_MATERIAS


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

2. The metadata includes a "dc.type" field that indicates the document type (e.g. "Tesis", "Articulo", "Libro", "Objeto de conferencia"). Use this field to determine which type-specific rules to apply (e.g. institucionDesarrollo for Tesis). Always return "dc.type" as-is in the output — do NOT validate it against the text.

3. For each key-value pair in the metadata (except dc.type):
    - Search the text for the metadata value (or a variation of it, such as differences in case, abbreviations, punctuation, or word order).
    - If the value exists in the text but is written differently, update the metadata value to match the exact appearance in the text.
    - If the value does not appear in the text, remove that key from the metadata.
    - for sedici.uri dc.uri and isrelatedwith must be exactly the same if not match exactly the same just put like null
    - Same for issn and isbn has to be exactly the same if not match exactly the same just put like null
    - For issn and isbn values, return ONLY the number itself (e.g. "2314-3991"), never include prefixes like "ISSN:", "ISBN:", "ISSN: ", etc.

4. Ensure all metadata values in the JSON object match their exact appearance in the text.

5. Return **only** the corrected JSON schema. Do not include explanations, comments, the original text, or the original metadata. The output first char must be '{' and the last one'}'

### special case for date:

The date field MUST always be normalized to one of these formats (from most specific to least specific):
- "yyyy/mm/dd" (e.g. "2020/03/15") — when full date is available
- "yyyy/mm" (e.g. "2023/08") — when only month and year are available
- "yyyy" (e.g. "2021") — when only year is available
- null — when no date information appears in the text at all

Strict rules for date:
- If the text contains a month name (in any language), translate it to its 2-digit number. Use leading zeros (e.g. January = 01, August = 08).
- If the text contains only a year, return only "yyyy".
- If the text contains month and year but no day, return "yyyy/mm".
- If the text contains day, month, and year, return "yyyy/mm/dd". Use leading zeros for day and month (e.g. 5 = 05).
- If the metadata has a date but NO date information appears anywhere in the text, set date to null.
- Do NOT invent or guess date components that are not present in the text.
- IMPORTANT: When in doubt, prefer null. If you are not certain that a date in the text corresponds to the publication/submission date of the document (and not some other date mentioned in the content), set date to null. It is better to return null than to return a wrong date.

Month name translation reference:
- enero/january = 01, febrero/february = 02, marzo/march = 03, abril/april = 04
- mayo/may = 05, junio/june = 06, julio/july = 07, agosto/august = 08
- septiembre/september = 09, octubre/october = 10, noviembre/november = 11, diciembre/december = 12

Date examples:

Input text mentions: "agosto 2016"
Output date: "2016/08"

Input text mentions: "published in 2024"
Output date: "2024"

Input text mentions: "15 de marzo de 2020"
Output date: "2020/03/15"

Input text mentions: "September 2019"
Output date: "2019/09"

Input text mentions: "submitted on March 5, 2021"
Output date: "2021/03/05"

Input text mentions no date at all:
Output date: null

### special case for event:

The event field must contain ONLY the event name as it appears in the text. Do NOT include location, city, date, modality, or any other information appended to the event name.

Strict rules for event:
- Extract only the event/conference name itself.
- Remove any parenthetical information containing location, city, date, or modality (e.g. "(La Plata, 2019)", "(modalidad virtual, 23 al 26 de agosto de 2019)").
- Remove trailing location or date information even if not in parentheses.
- If the event name does not appear in the text at all, set it to null.

Event examples:

Input metadata: "IV Congreso Internacional de Enseñanza del Derecho (La Plata, modalidad virtual, 23 al 26 de agosto de 2019)"
Text only contains: "IV Congreso Internacional de Enseñanza del Derecho"
Output event: "IV Congreso Internacional de Enseñanza del Derecho"

Input metadata: "X Jornadas de Sociología (Buenos Aires, noviembre 2018)"
Text contains: "X Jornadas de Sociología"
Output event: "X Jornadas de Sociología"

Input metadata: "Workshop on NLP, held in Madrid, 2023"
Text contains: "Workshop on NLP"
Output event: "Workshop on NLP"

### special case for language:

The language field is an EXCEPTION to the general rule. Do NOT remove it even if no explicit language mention appears in the text.
Instead, always detect the language of the text and return it.

Strict rules for language:
- Detect the language the text is written in.
- Return the language as a two-letter ISO 639-1 code (e.g. "es", "en", "pt", "fr").
- If the metadata has a language value, validate it against the actual text language. If it matches, keep it. If it does not match, correct it to the actual language of the text.
- NEVER return null or None for language. Always return a value.

### special case for originPlaceInfo:

originPlaceInfo represents the broader institutional origin of the document: the faculty, university, or organization that published or hosts the work. It applies to ALL document types.
Typical values are faculties (e.g. "Facultad de Informática", "Facultad de Ciencias Exactas"), universities (e.g. "Universidad Nacional de La Plata"), editorial units, or organizations.

Pay special attention to abbreviations and initials for institutions and places. Academic texts frequently use abbreviations like:
- "UNLP" = "Universidad Nacional de La Plata"
- "UBA" = "Universidad de Buenos Aires"
- "CONICET" = "Consejo Nacional de Investigaciones Científicas y Técnicas"
- "FCE" = "Facultad de Ciencias Exactas"
- "FaHCE" = "Facultad de Humanidades y Ciencias de la Educación"
- And similar institutional abbreviations.

Strict rules for originPlaceInfo:
- Capitalisation: always use title case (only the first letter of each significant word capitalised). Prepositions and conjunctions stay lowercase (de, del, y, en, a, con, por, etc.). Do NOT write the full name in all capitals. ONLY abbreviations and acronyms stay in all caps (e.g. UNLP, CONICET, UBA, UTN). Example: "FACULTAD DE CIENCIAS EXACTAS" → "Facultad de Ciencias Exactas".
- If the metadata contains a full institution name (e.g. "Universidad Nacional de La Plata") and the text contains its abbreviation or initials (e.g. "UNLP"), consider it a match and keep the full name from the metadata.
- If the text contains the abbreviation/initials but NOT the full name, still keep the metadata value as it matches the institution.
- This field is an EXCEPTION to the general rule: even if the metadata value is null, empty, or does not match the text, if the text clearly mentions a faculty, university, or organization where the work originates, you should extract and return it.
- originPlaceInfo can be a SINGLE value (string) or MULTIPLE values (comma-separated string) when multiple faculties or institutions are involved.
- When multiple distinct faculties or institutions appear in the text as author affiliations, include ALL of them separated by ", " (e.g. "Facultad de Ciencias Exactas, Facultad de Ciencias de la Salud").
- Do not duplicate: if multiple authors share the same faculty, list it only once.
- Typical values include: "Facultad de ..." (faculties), "Universidad Nacional de ..." (universities), organizations, editorial units, or research networks.
- Do NOT confuse originPlaceInfo with institucionDesarrollo. originPlaceInfo is the broader origin (faculty, university), while institucionDesarrollo is the specific research unit (lab, institute, center).
- Institution name canonicalization — always apply these rules:
  - Expand university abbreviations to their full name: UNLP → "Universidad Nacional de La Plata", UBA → "Universidad de Buenos Aires", UTN → "Universidad Tecnológica Nacional", UNC → "Universidad Nacional de Córdoba".
  - CONICET is an exception: always keep "CONICET", never write the full name "Consejo Nacional de Investigaciones Científicas y Técnicas". If the text has the full name (with or without the "(CONICET)" parenthetical), output just "CONICET".
  - "Facultad de Bellas Artes" was renamed to "Facultad de Artes" in 2014 — always use "Facultad de Artes".
  - Do NOT append redundant institutional labels in parentheses such as "(UNLP)" or "(UBA)" after a faculty name you have already identified.

### special case for institucionDesarrollo (Tesis only):

institucionDesarrollo represents the specific research center, laboratory, or institute where the thesis research was developed. This field is ONLY relevant for Tesis (thesis) documents.
Typical values are research labs, institutes, or centers within a university, such as:
- "Instituto de Investigaciones en Informática"
- "Laboratorio de Investigación y Formación en Informática Avanzada"
- "Centro de Investigaciones Cardiovasculares"
- "Centro de Investigación y Desarrollo en Criotecnología de Alimentos"
- "Instituto de Estudios Inmunológicos y Fisiopatológicos"

This field is an EXCEPTION to the general rule: even if the metadata value is null or empty, if the text mentions a specific research center, laboratory, or institute where the research was conducted, you should extract and return it.

Strict rules for institucionDesarrollo:
- Capitalisation: same rule as originPlaceInfo — use title case, keep abbreviations/acronyms in all caps (e.g. CONICET, INTA, UNLP), never write the full name in all capitals.
- Apply the same canonicalization rules as originPlaceInfo: expand UNLP/UBA/UTN to full name, keep "CONICET" as abbreviation, use "Facultad de Artes" not "Facultad de Bellas Artes".
- This field applies ONLY to Tesis documents. For other document types, ignore it.
- Look for mentions of research units identified by keywords like "Instituto", "Laboratorio", "Centro de Investigación", "Centro de Estudios", "Grupo de Investigación", "Unidad de Investigación", "Cátedra".
- If the metadata has a value, validate it against the text using the same abbreviation matching rules as originPlaceInfo.
- If the metadata is null/empty but the text clearly mentions a research center, lab, or institute where the thesis was developed, extract and return it.
- If multiple research units are mentioned, return them as a JSON array with each unit as a separate element — do NOT join them into a single comma-separated string. Order the elements by their first appearance in the text. Example: ["Centro de Química Inorgánica", "Instituto de Investigaciones Fisicoquímicas Teóricas y Aplicadas"]. If the input metadata has them in a different order or concatenated, correct it.
- If only one research unit is found, return it as a plain string (not an array).
- Use the full institutional name as it appears in the text. If only an abbreviation appears, return the abbreviation.
- Do NOT confuse with originPlaceInfo: institucionDesarrollo is the specific research unit (lab/institute/center), not the faculty or university.

### special case for degree.name (Tesis only):

degree.name represents the academic degree obtained by the author. It MUST always be expressed in the person/graduate form, NOT the program name.

Strict rules:
- Always convert the program form to the person form:
  - "Licenciatura en X"  →  "Licenciado en X" (or "Licenciada en X" if author is female)
  - "Doctorado en X"     →  "Doctor en X" (or "Doctora en X")
  - "Ingeniería en X"    →  "Ingeniero en X" (or "Ingeniera en X")
  - "Maestría en X"      →  "Magíster en X" (or use "Maestro/a en X" if the text uses that form)
  - "Tecnicatura en X"   →  "Técnico en X" (or "Técnica en X")
  - "Especialización en X" → "Especialista en X"
  - Forms already in person form ("Licenciado en X", "Doctor en X") stay unchanged.
- The degree MUST include the subject area when available (e.g. "Licenciado en Química", NOT just "Licenciado").
- Gender: use masculine form unless the text or the author's name clearly indicates feminine gender.
- Capitalisation: preserve the capitalisation as it appears in the text. Do not convert the entire value to uppercase.
- Context inference — if degree.name is null/empty but the text contains enough context, infer it:
  - Look for phrases like: "para obtener el grado de", "para acceder al título de", "trabajo final de licenciatura", "tesis doctoral", "tesis de grado".
  - If the text mentions a faculty name alongside "trabajo final" or a degree reference, map it to its most common degree. Examples:
    - "Facultad de Nutrición" → "Licenciado en Nutrición"
    - "Facultad de Informática" → look for the specific program mentioned; if absent, return null.
    - "Facultad de Medicina" + "tesis doctoral" → "Doctor en Medicina"
  - If ambiguous or multiple degrees are possible, return null rather than guessing.

degree.name examples:

Metadata has "Doctorado en Ciencias Naturales" → Output: "Doctor en Ciencias Naturales"
Metadata has "Licenciatura en Nutrición" → Output: "Licenciado en Nutrición"
Metadata has "Ingeniería Forestal" → Output: "Ingeniero Forestal"
Text: "trabajo final para obtener el título de Licenciada en Psicología" → Output: "Licenciada en Psicología"
Text: "trabajo final" + "Facultad de Nutrición" (no explicit degree stated) → Output: "Licenciado en Nutrición"
Text: "tesis doctoral" + "Facultad de Ciencias Exactas" (no specific degree) → Output: null

### special case for degree.grantor (Tesis only):

degree.grantor is the institution that awards (grants) the academic degree. It applies ONLY to Tesis documents.

Strict rules for degree.grantor:
- Always expand abbreviations to the full institution name.
  Examples: UNLP → "Universidad Nacional de La Plata", UBA → "Universidad de Buenos Aires",
            UNC → "Universidad Nacional de Córdoba", UTN → "Universidad Tecnológica Nacional".
- If degree.grantor is not explicitly stated in the text, set it to null.
- Do NOT infer or guess the grantor institution from context alone.

### special case for name fields (creator, director, codirector, compiler, collaborator, editor, publisher):

These fields contain people's names (or an organization name for publisher). Apply these cleaning rules to ALL of them:

Strict rules:
- Remove ALL honorific or academic title prefixes. Remove any abbreviation ending in a period that precedes a name:
  Dr., Dra., Lic., Lica., Ing., Inga., Mg., Mgr., Mgtr., MSc., Mag., Prof., Profa., Agr., Arq.,
  Abog., Med., Vet., MV., Esp., Psic., Farm., Geof., Ftal., Coord., Colab., Tec., Bio., Cra., Ec.,
  and any similar abbreviated title followed by a period.
- Remove ALL parenthetical content that refers to institutional affiliations, roles, or identifiers.
  Examples to remove: (UNLP), (FCAyF-UNLP), (CONICET), (EEA INTA General Villegas),
  (COORDINADOR), (COORDINADORA), (compiladoras), [o-oi-6404-0552], or any text in ( ) or [ ].
- Remove trailing periods that are not part of the name (e.g. "Leandro Adrián." → "Leandro Adrián").
- Do NOT remove organization names when they ARE the value (e.g. publisher: "Editorial UNLP" → keep).
- If the field is a list, apply these rules to each element independently.
- When a field contains multiple people (array), always return the elements in the same order they appear in the text. If the input metadata has them in a different order, fix it.
- Return only the clean name: e.g. "García, María José" or "María José García".

Name field examples:

Input: "Dr. Juan García"                          → Output: "Juan García"
Input: "Agr. Sc. Mariana del Pino"                → Output: "Mariana del Pino"
Input: "ANTONIO CAMOU (COORDINADOR)"              → Output: "ANTONIO CAMOU"
Input: "Chamorro, Adriana (FCAyF-UNLP)"           → Output: "Chamorro, Adriana"
Input: "Girón, Paula (EEA INTA General Villegas)" → Output: "Girón, Paula"
Input: "Di Paolo, Leandro Adrián."                → Output: "Di Paolo, Leandro Adrián"
Input: ["Dr. Luis López", "Lic. Ana Martínez (CONICET)"] → Output: ["Luis López", "Ana Martínez"]

### special case for journalTitle:

The journalTitle field contains the full name of the journal where the article was published.

Strict rules for journalTitle:
- Extract the journal name exactly as it appears in the text — do not shorten, truncate, or omit any words.
- Do NOT invent, approximate, or guess a journal name that is not clearly present in the text.
- If the journal name does not appear in the text, set journalTitle to null.

### special case for journalVolumeAndIssue:

You are cleaning and normalizing volume and issue information from academic publication metadata.

Your task is to normalize the input text into a single, consistent textual format.
This is a normalization step only — do NOT infer or add information that is not explicitly present.

Strict rules:

- Use only lowercase.
- Remove punctuation, symbols, and parentheses.
- Use the following canonical tokens only:
  - "vol {number}" for volume
  - "no {number}" for issue
  - "especial" for special issues (use this exact word only)
  - "suplemento {number}" for supplements
  - "{year}" for years (4 digits, 1900–2099)

- All elements are optional.
- Always use the same order:
  vol → no → especial → suplemento → year
- Separate elements using ", " (comma + space).
- Do NOT use abbreviations, symbols, or alternative words.

Normalization rules:

- Convert all variants of "volume" to "vol".
- Convert all variants of "number", "issue", "n°", "nº", etc. to "no".
- Convert any form of "special issue" or "special number" to "especial".
- Convert patterns like "7 (2)" or "9(2)" into "vol 7, no 2".
- A standalone year is NOT a valid value for this field. journalVolumeAndIssue MUST include at least a volume number ("vol N") or issue number ("no N").
- If no volume or issue information is found in the text, set journalVolumeAndIssue to null.
- Remove months, editorial notes, and unrelated text.
- Do NOT invent missing values.

journalVolumeAndIssue examples:

Input: "Vol. 7 (2)"
Output: "vol 7, no 2"

Input: "Vol8, N°2, Suplemento N°1"
Output: "vol 8, no 2, suplemento 1"

Input: "Número Especial, Septiembre 2020"
Output: "especial, 2020"

Input: "2021" (year only, no volume or issue)
Output: null

### Full input/output examples:

Input example:
- Text: "This paper was written by Juan M. Pérez in 2024."
- Metadata: {"creator": "Perez, Juan Manuel", "date": "2024", "journalTitle": "Journal of AI Research"}

Output example:
{"creator": "Juan M. Pérez", "date": "2024"}

Input example:
- Text: "Dr. María García collaborated with John O'Connor to publish this work in august 2023."
- Metadata: {"creator":["Garcia, Maria", "OConnor, John"], "date": "2023/08/01", "publisher": "AI Press"}

Output example:
{"creator": ["María García", "John O'Connor"], "date": "2023/08"}

Input example:
- Text: "Presentado en el IV Congreso Internacional de Enseñanza del Derecho durante agosto 2019."
- Metadata: {"event": "IV Congreso Internacional de Enseñanza del Derecho (La Plata, modalidad virtual, 23 al 26 de agosto de 2019)", "date": "2019/08/23"}

Output example:
{"event": "IV Congreso Internacional de Enseñanza del Derecho", "date": "2019/08"}

Input example:
- Text: "Publicado en Revista de Derecho, volumen 5 número 3, septiembre 2020."
- Metadata: {"journalTitle": "Revista de Derecho", "journalVolumeAndIssue": "Vol. 5, N° 3", "date": "2020/09/01"}

Output example:
{"journalTitle": "Revista de Derecho", "journalVolumeAndIssue": "vol 5, no 3", "date": "2020/09"}

Input example (Tesis with institucionDesarrollo):
- Text: "Tesis presentada para obtener el grado de Doctor en Ciencias Naturales, Facultad de Ciencias Naturales y Museo, UNLP. El trabajo fue realizado en el Instituto de Investigaciones Fisicoquímicas Teóricas y Aplicadas (INIFTA). Director: Dr. Juan Pérez."
- Metadata: {"originPlaceInfo": "Facultad de Ciencias Naturales y Museo", "institucionDesarrollo": null, "director": "Dr. Juan Pérez", "degree.grantor": "Universidad Nacional de La Plata", "degree.name": "Doctor en Ciencias Naturales", "date": "2022"}

Output example:
{"originPlaceInfo": "Facultad de Ciencias Naturales y Museo", "institucionDesarrollo": "Instituto de Investigaciones Fisicoquímicas Teóricas y Aplicadas", "director": "Juan Pérez", "degree.grantor": "Universidad Nacional de La Plata", "degree.name": "Doctor en Ciencias Naturales", "date": "2022"}

Input example (Tesis with multiple institucionDesarrollo):
- Text: "El trabajo fue realizado en el Centro de Química Inorgánica (CEQUINOR) y en el Instituto de Investigaciones Fisicoquímicas Teóricas y Aplicadas (INIFTA). Autores: López, Ana; García, Carlos."
- Metadata: {"originPlaceInfo": "Facultad de Ciencias Exactas", "institucionDesarrollo": "Instituto de Investigaciones Fisicoquímicas Teóricas y Aplicadas, Centro de Química Inorgánica", "creator": ["García, Carlos", "López, Ana"], "date": "2021"}

Output example:
{"originPlaceInfo": "Facultad de Ciencias Exactas", "institucionDesarrollo": ["Centro de Química Inorgánica", "Instituto de Investigaciones Fisicoquímicas Teóricas y Aplicadas"], "creator": ["López, Ana", "García, Carlos"], "date": "2021"}

you must pay attention in the json provided after this:
"""



HEADER_PROMPT = """ Extract the metadata from the text and provide it in JSON format:
You have to extract the metadata:
language, title,  creator, rights, rightsurl, date, originPlaceInfo"""

#dc.uri, sedici.uri,subtitle, subject,isRelatedWith


MIDDLE_PROMPT = """Here is a JSON Example format:"""

END_PROMPT = """Now, extract the information from the following text and provide it in the specified JSON format:"""


JSON_GENERAL = {
  "language": "es",
#  "keywords": "['Energía eólica', 'modelos analíticos de estelas', 'eficiencia del parque', 'validación de modelos']",
  "title": "SIMULACIÓN MEDIANTE MODELOS ANALÍTICOS DE ESTELA EN PARQUES EÓLICOS Y VALIDACIÓN CON MEDICIONES DEL PARQUE EÓLICO RAWSON",
#  "subtitle": "Estadisticas y Desempeño de los Modelos Analíticos de Estelas",
  "creator": "['Lazzari, Florencia', 'Otero, Alejandro']",
#  "subject": "Otras ingenierías y tecnologías",
  "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
  "rightsurl" : "http://creativecommons.org/licenses/by-nc-sa/4.0/",
#  "dc.uri": "http://sedici.unlp.edu.ar/handle/10915/108413",
#  "sedici.uri": "http://portalderevistas.unsa.edu.ar/index.php/averma/article/view/1213",
  "date": "2018-01-01",
  "originPlaceInfo": "ASADES",
#  "isRelatedWith": "http://sedici.unlp.edu.ar/handle/10915/128795",
}

PROMPT_GENERAL = f"""{HEADER_PROMPT}{MIDDLE_PROMPT}{JSON_GENERAL}{END_PROMPT}"""



JSON_TESIS = {
        "language": "es",
#        "keywords": "['Sistemas silvopastoriles', 'Eucalyptus', 'Pastizal natural', 'Sistema Nelder modificado', 'Pampa deprimida']",
        "title": "¿Es compatible la producción forestal con la producción forrajera en plantaciones de Eucalyptus híbrido?",
#        "subtitle": "Una experiencia para la provincia de Buenos Aires",
        "creator": "Siccardi, Bárbara",
#        "subject": "Agricultura,silvicultura y pesca",
        "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
        "rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
#        "dc.uri": "http://sedici.unlp.edu.ar/handle/10915/159750",
        "date": "2023-01-01",
        "originPlaceInfo": "Facultad de Ciencias Agrarias y Forestales",
#        "isRelatedWith": "http://sedici.unlp.edu.ar/handle/10915/118764",
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
#        "subject": "Ciencias físicas",
        "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
        "rightsurl" : "http://creativecommons.org/licenses/by-nc-sa/4.0/",
  #      "dc.uri": "http://sedici.unlp.edu.ar/handle/10915/168246",
 #       "sedici.uri": "http://portalderevistas.unsa.edu.ar/index.php/averma/article/view/1213",
        "date": "2022-01-01",
        "originPlaceInfo": "Asociación Argentina de Astronomía",
#        "isRelatedWith": "http://sedici.unlp.edu.ar/handle/10915/118464",
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
#        "subject": "Ciencias físicas",
        "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
        "rightsurl" : "http://creativecommons.org/licenses/by-nc-sa/4.0/",
  #      "dc.uri": "http://sedici.unlp.edu.ar/handle/10915/168246",
 #       "sedici.uri": "http://portalderevistas.unsa.edu.ar/index.php/averma/article/view/1213",
        "date": "2022-01-01",
        "originPlaceInfo": "Asociación Argentina de Astronomía",
#        "isRelatedWith": "http://sedici.unlp.edu.ar/handle/10915/118464",
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
#        "subject": "Ciencias biológicas",
        "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
        "rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
#       "dc.uri": "http://sedici.unlp.edu.ar/handle/10915/131176",
#        "sedici.uri": "http://portalderevistas.unsa.edu.ar/index.php/averma/article/view/1213",
        "date": "2021-01-01",
        "originPlaceInfo": "['Facultad de Ciencias Naturales y Museo', 'Facultad de Ciencias Exactas']",
#        "isRelatedWith": "http://sedici.unlp.edu.ar/handle/10915/118183",
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
        "originPlaceInfo": "",
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
        "originPlaceInfo": "",
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
        "originPlaceInfo": "",
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
        "originPlaceInfo": "",
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
        "originPlaceInfo": "",
        "isRelatedWith": ""
}"""

        # "dc.uri": "",
        # "sedici.uri": "",

PROMPT_CLOUD_LLM_VALIDATOR = """You are an expert metadata extraction system specialized in analyzing academic documents from SEDICI (Servicio de Difusión de la Creación Intelectual) repository of Universidad Nacional de La Plata.

**TASK**: Extract metadata from the provided academic document text and return it in JSON format.

**STEP 1 — CLASSIFY DOCUMENT TYPE**:
First, determine which type the document belongs to. Include it in the output as "dc.type":
- "Tesis" — thesis or dissertation (look for: director, degree, "para obtener el grado de", "trabajo final")
- "Articulo" — journal article (look for: journal name, volume, issue, ISSN)
- "Libro" — book (look for: ISBN, publisher, editorial)
- "Objeto de conferencia" — conference paper/poster (look for: conference name, proceedings, "congreso", "jornadas")

**STEP 2 — EXTRACT METADATA FIELDS**:

**Common fields for all document types:**
- dc.type: Document type (one of: "Tesis", "Articulo", "Libro", "Objeto de conferencia")
- language: Detect the language the document is written in and return it as a two-letter ISO 639-1 code (es/en/pt/fr/etc.). NEVER omit this field — always return a value.
- title: Main document title
- creator: Author(s) as an array. Apply name cleaning rules (see below).
- subject: Academic subject/discipline mapped to FORD classification (see below)
- keywords: Keywords as an array of strings
- abstract: The document abstract as a plain string. Extract the full abstract text exactly as it appears. Omit if not present.
- rights: License information (e.g., Creative Commons full name)
- rightsurl: URL of the license, extracted exactly as it appears
- date: Publication date — apply date normalization rules (see below)
- originPlaceInfo: Faculty, university, or organization — apply canonicalization rules (see below)

**Type-specific fields (include only if the document type matches):**

**For Tesis:**
- director: Thesis director/supervisor. Apply name cleaning rules.
- codirector: Co-director/co-supervisor. Apply name cleaning rules. Omit if not present.
- degree.grantor: Institution granting the degree. Always expand abbreviations to full name. Omit if not explicitly stated.
- degree.name: Academic degree — apply degree.name rules (see below).
- institucionDesarrollo: Specific research center, lab, or institute where the research was developed (e.g. "Instituto de Investigaciones en Informática", "Laboratorio de Investigación y Formación en Informática Avanzada"). Look for keywords: "Instituto", "Laboratorio", "Centro de Investigación", "Centro de Estudios", "Grupo de Investigación". Return as a string if one, or an array if multiple. Omit if not found.

**For Articulo:**
- journalTitle: Full journal name exactly as it appears. Do NOT shorten or approximate. Omit if not clearly present.
- journalVolumeAndIssue: Normalized volume/issue — apply journalVolumeAndIssue rules (see below).
- issn: ISSN number only (e.g. "2314-3991"), no prefix. Must match exactly as it appears. Omit if not found.
- event: Conference/event name only — apply event rules (see below).

**For Libro:**
- publisher: Publisher name
- isbn: ISBN number only, no prefix. Must match exactly as it appears.
- compiler: Compiler if applicable. Apply name cleaning rules.
- editor: Editor if applicable. Apply name cleaning rules.

**For Objeto de conferencia:**
- issn: ISSN number only, no prefix. Must match exactly as it appears. Omit if not found.
- event: Conference/event name only — apply event rules (see below).

---

**DATE NORMALIZATION RULES**:
Normalize the publication/creation date to one of these formats (from most to least specific):
- "yyyy/mm/dd" (e.g. "2020/03/15") — when full date is available
- "yyyy/mm" (e.g. "2023/08") — when only month and year are available
- "yyyy" (e.g. "2021") — when only year is available
- omit the field — when no date information appears in the text

Strict rules:
- Extract only the publication/creation date, NOT submission, defense, or revision dates.
- Translate month names to 2-digit numbers. Use leading zeros (January=01, August=08).
- Do NOT invent or guess date components not present in the text.
- When in doubt, prefer omitting over returning a wrong date.

Month reference: enero/january=01, febrero/february=02, marzo/march=03, abril/april=04, mayo/may=05, junio/june=06, julio/july=07, agosto/august=08, septiembre/september=09, octubre/october=10, noviembre/november=11, diciembre/december=12

---

**NAME CLEANING RULES** (applies to: creator, director, codirector, compiler, editor):
- Remove ALL honorific/academic title prefixes: Dr., Dra., Lic., Lica., Ing., Inga., Mg., Mgr., Mgtr., MSc., Mag., Prof., Profa., Agr., Arq., Abog., Med., Vet., MV., Esp., Psic., Farm., Bio., Tec., and any similar abbreviated title followed by a period.
- Remove ALL parenthetical content referring to affiliations, roles, or identifiers: (UNLP), (CONICET), (FCAyF-UNLP), (COORDINADOR), (compiladoras), [o-oi-6404-0552], etc.
- Remove trailing periods that are not part of the name.
- Maintain the order authors appear in the text.
- Return as array when multiple people, plain string when one.

Name examples:
- "Dr. Juan García" → "Juan García"
- "Chamorro, Adriana (FCAyF-UNLP)" → "Chamorro, Adriana"
- "ANTONIO CAMOU (COORDINADOR)" → "ANTONIO CAMOU"
- ["Dr. Luis López", "Lic. Ana Martínez (CONICET)"] → ["Luis López", "Ana Martínez"]

---

**DEGREE.NAME RULES** (Tesis only):
Always express the degree in the person/graduate form, NOT the program name form:
- "Licenciatura en X" → "Licenciado en X" (or "Licenciada en X" if author is female)
- "Doctorado en X" → "Doctor en X" (or "Doctora en X")
- "Ingeniería en X" → "Ingeniero en X" (or "Ingeniera en X")
- "Maestría en X" → "Magíster en X"
- "Tecnicatura en X" → "Técnico en X"
- "Especialización en X" → "Especialista en X"
- Forms already in person form stay unchanged.
- The degree MUST include the subject area when available (e.g. "Licenciado en Química", NOT just "Licenciado").
- Use masculine form unless the text or author name clearly indicates feminine gender.
- If degree.name is not found, look for phrases like "para obtener el grado de", "para acceder al título de", "trabajo final de licenciatura", "tesis doctoral".

---

**EVENT RULES** (Articulo and Objeto de conferencia):
Extract ONLY the event/conference name itself. Strip all location, city, date, modality, and other appended info.
- Remove parenthetical content with location or date: "(La Plata, 2019)", "(modalidad virtual, 23 al 26 de agosto de 2019)".
- Remove trailing location or date info even if not in parentheses.

Event examples:
- "IV Congreso Internacional de Enseñanza del Derecho (La Plata, modalidad virtual, 23 al 26 de agosto de 2019)" → "IV Congreso Internacional de Enseñanza del Derecho"
- "X Jornadas de Sociología (Buenos Aires, noviembre 2018)" → "X Jornadas de Sociología"

---

**JOURNALVOLUMEANDISSUE RULES**:
Normalize to a single consistent format using only these canonical tokens:
- "vol {number}" for volume
- "no {number}" for issue/number
- "especial" for special issues
- "suplemento {number}" for supplements
- "{year}" for years (4 digits)
- All lowercase. Separate elements with ", ". Order: vol → no → especial → suplemento → year.
- A standalone year is NOT valid — must include at least "vol N" or "no N".
- Omit if no volume or issue information is found.

journalVolumeAndIssue examples:
- "Vol. 7 (2)" → "vol 7, no 2"
- "Vol8, N°2, Suplemento N°1" → "vol 8, no 2, suplemento 1"
- "Número Especial, Septiembre 2020" → "especial, 2020"
- "2021" (year only) → omit field

---

**ORIGINPLACEINFO RULES**:
Represents the broader institutional origin: faculty, university, or organization. Applies to ALL document types.
- Use title case: only first letter of significant words capitalized. Prepositions and conjunctions stay lowercase (de, del, y, en, a, con, por). Abbreviations/acronyms stay ALL CAPS.
- Institution canonicalization (always apply):
  - UNLP → "Universidad Nacional de La Plata"
  - UBA → "Universidad de Buenos Aires"
  - UTN → "Universidad Tecnológica Nacional"
  - UNC → "Universidad Nacional de Córdoba"
  - CONICET → always keep as "CONICET" (never expand to full name)
  - "Facultad de Bellas Artes" → "Facultad de Artes" (renamed in 2014)
  - Do NOT append "(UNLP)" or similar after a faculty name already identified.
- If multiple distinct faculties/institutions appear as author affiliations, include ALL separated by ", ". Do not duplicate.
- Even if not explicitly stated, if the text clearly identifies a faculty or university of origin, extract and return it.
- Do NOT confuse with institucionDesarrollo: originPlaceInfo is the faculty/university, not the specific lab or research center.

---

**FORD SUBJECT MAPPING**:
Map the document's academic subject to one of these FORD categories:
- Ciencias físicas / Ciencias químicas / Ciencias de la tierra y ciencias ambientales relacionadas
- Ciencias biológicas / Otras ciencias naturales
- Ciencias de la computación e información / Ingeniería civil / Ingeniería eléctrica, electrónica e informática
- Ingeniería mecánica / Ingeniería química / Ingeniería de los materiales
- Economía y negocios / Educación / Sociología / Derecho / Ciencia política
- Psicología y ciencias cognitivas / Geografía social y económica
- Artes / Historia y arqueología / Lenguas y literatura / Filosofía, ética y religión

---

**GENERAL EXTRACTION RULES**:
1. Extract ONLY information clearly present and unambiguous in the text.
2. If a field cannot be determined with high confidence, omit it from the JSON (do not set to null, just omit).
3. Ignore page numbers, headers, footers, and bibliographic references when extracting metadata.
4. For issn and isbn: return ONLY the number (e.g. "2314-3991"), never include prefixes like "ISSN:", "ISBN:".
5. Do NOT include "isRelatedWith" — this is a repository URI that does not appear in the document text.

---

**OUTPUT FORMAT**:
Return ONLY a valid JSON object. The first character must be '{' and the last '}'. No explanations, no comments, no markdown fences.

**EXAMPLE OUTPUT** (Tesis):
{
    "dc.type": "Tesis",
    "language": "es",
    "title": "Análisis de sistemas fotovoltaicos distribuidos en redes eléctricas urbanas",
    "creator": ["García, María Elena", "Rodríguez, Carlos Alberto"],
    "subject": "Ingeniería eléctrica, electrónica e informática",
    "keywords": ["energía solar", "sistemas fotovoltaicos", "redes distribuidas"],
    "abstract": "Esta tesis analiza el impacto de los sistemas fotovoltaicos distribuidos en la estabilidad de redes eléctricas urbanas...",
    "rights": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
    "rightsurl": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
    "date": "2023/06/15",
    "originPlaceInfo": "Facultad de Ingeniería, Universidad Nacional de La Plata",
    "director": "Juan Carlos Mendez",
    "degree.grantor": "Universidad Nacional de La Plata",
    "degree.name": "Ingeniero Electricista",
    "institucionDesarrollo": "Instituto de Investigaciones en Informática LIDI"
}

**EXAMPLE OUTPUT** (Articulo):
{
    "dc.type": "Articulo",
    "language": "en",
    "title": "Deep learning approaches for named entity recognition",
    "creator": ["Smith, John", "Doe, Jane"],
    "subject": "Ciencias de la computación e información",
    "keywords": ["deep learning", "NER", "natural language processing"],
    "abstract": "This paper proposes novel deep learning approaches for named entity recognition across multiple languages...",
    "date": "2022",
    "journalTitle": "Journal of Artificial Intelligence Research",
    "journalVolumeAndIssue": "vol 45, no 3",
    "issn": "1076-9757"
}

Now analyze the following document text and extract the metadata:"""
