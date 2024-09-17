from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]  / "fine_tunning"
DATA_FOLDER = ROOT_DIR / "data" / "sedici"
JSONS_FOLDER = DATA_FOLDER / "jsons/"
DATASET_WITH_METADATA_CHECKED = "final_metadata_Chekced.json"
DATASET_WITH_TEXT_DOC = "metadata_and_text.json"
KEYS_DATA = {
    "general": [
        "dc.date.accessioned",
        "dc.date.available",
        "dc.date.issued",
        "dc.identifier.uri",
        "dc.description.abstract",
        "dc.language",
        "dc.subject",
        "dc.title",
        "dc.type",
        "sedici.creator.person",
        "sedici.subject.materias",
        "sedici.description.fulltext",
        "mods.originInfo.place",
        "sedici.subtype",
        "sedici.rights.license",
        "sedici.rights.uri",
        "sedici2003.identifier"
    ],
    "Tesis" : [
        "sedici.contributor.director",
        "thesis.degree.name",
        "thesis.degree.grantor",
        "sedici.date.exposure",
        "sedici.description.note"
    ],
    "Articulo":[
        "dc.format.extent",
        "sedici.description.peerReview",
        "sedici.relation.journalTitle",
        "sedici.relation.journalVolumeAndIssue",
        "sedici.title.subtitle",
        "sedici.description.note"
    ],
    "Objeto de conferencia":[
        "sedici.relation.event",
        "sedici.description.peerReview",
        "sedici.date.exposure"
    ]
}
BASE_MODEL_LED="allenai/led-base-16384"
BASE_MODEL_GEMMA="google/gemma-2-2b"
BASE_MODEL_LLAMA="Meta-Llama-3.1-8B"
BASE_MODEL_MISTRAL="mistralai/Mistral-7B-v0.1"
BASE_MODEL="google/gemma-2-2b"
MAX_TOKENS_INPUT= 8192
MAX_TOKENS_OUTPUT= 512
LOG_DIR = ROOT_DIR /  "log"
FINAL_MODEL_PATH =ROOT_DIR / "fine-tuned-model"
CHECKPOINT_MODEL_PATH = ROOT_DIR / "results"
PROMPT =""" Extract the following information from the text and provide it in JSON format:
Required keys:
- dc.language
- dc.subject
- dc.title
- dc.type
- sedici.creator.person
- sedici.subject.materias

Optional keys (if available in the text):
- sedici.contributor.director
- sedici.contributor.codirector
- sedici.title.subtitle
- sedici.relation.journalVolumeAndIssue
- sedici.relation.journalTitle
- sedici.identifier.issn

Example JSON output format:

{
  "dc.language": "value",
  "dc.subject": "value",
  "dc.title": "value",
  "dc.type": "value",
  "sedici.creator.person": "value",
  "sedici.subject.materias": "value",
  "sedici.contributor.director": "value",
  "sedici.contributor.codirector": "value",
  "sedici.title.subtitle": "value",
  "sedici.relation.journalVolumeAndIssue": "value",
  "sedici.relation.journalTitle": "value",
  "sedici.identifier.issn": "value"
}

The values from the key sedici.subject.materias must be one or more of the following:

['Ingeniería', 'Ingeniería Química', 'Química', 'Ciencias Veterinarias', 'Veterinaria', 'Ciencias Jurídicas', 
'Relaciones Internacionales', 'Ciencias Agrarias', 'Ingeniería Agronómica', 'Comunicación Social', 'Periodismo',
'Comunicación', 'Ciencias Astronómicas', 'Astronomía', 'Trabajo Social', 'Odontología', 'Educación', 'Ciencias Informáticas', 
'Ciencias Exactas', 'Bioquímica', 'Software', 'Matemática', 'Biología', 'Física', 'Humanidades', 'Psicología', 'Historia', 'Bibliotecología', 
'Filosofía', 'Letras', 'Ciencias de la Educación', 'Educación Física', 'Sociología', 'Ciencias Naturales', 'Geografía', 'Ciencias Sociales', 'Política', 
'Ciencias Económicas', 'Turismo', 'Economía', 'Salud', 'Sistemas', 'Redes y Seguridad', 'Informática', 'Ingeniería Civil', 'Bellas Artes', 'Música', 'Zoología', 
'Botánica', 'Paleontología', 'Arqueología', 'Antropología', 'Ecología', 'Geología']

If dc.type is "Tesis", the following keys must not be present:
-"sedici.relation.journalVolumeAndIssue
-"sedici.relation.journalTitle"
-"sedici.identifier.issn"
If dc.type is "Artículo", the following keys must not be present:
-"sedici.contributor.director"
-"sedici.contributor.codirector"

Now, extract the information from the following text and provide it in the specified JSON format:"""