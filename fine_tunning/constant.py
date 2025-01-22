from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]  / "fine_tunning"
DATA_FOLDER = ROOT_DIR / "data" / "sedici"
JSONS_FOLDER = DATA_FOLDER / "jsons/"
DATASET_WITH_METADATA_CHECKED = "final_metadata_Chekced.json"
#DATASET_WITH_TEXT_DOC = "metadata_and_text.json"
DATASET_WITH_TEXT_DOC = "metadata_correjidaFinal_text.json"
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
        "dc.subject.ford",
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
MAX_TOKENS_INPUT= 1024
MAX_TOKENS_OUTPUT= 512
LOG_DIR = ROOT_DIR /  "log"
FINAL_MODEL_PATH =ROOT_DIR / "fine-tuned-model"
CHECKPOINT_MODEL_PATH = ROOT_DIR / "results"
PROMPT =""" Extract the metadata from the text and provide it in JSON format:
This are the possible metadata and with their respective value of the dcmi standard

    'sedici.rights.license' : "DCMIID":"dc.rights
    'sedici.rights.uri' : "DCMIID":"dc.rights
    'sedici.relation.isRelatedWith' : "DCMIID":"dc.relation
    'sedici.identifier.uri' : "DCMIID":"dc.identifier
    'dc.identifier.uri' : "DCMIID":"dc.identifier
    'sedici.contributor.editor' : "DCMIID":"dc.contributor
    'sedici.contributor.compiler' : "DCMIID":"dc.contributor
    'dc.publisher' : "DCMIID":"dc.publisher
    'dc.date.issued' : {'type': "str","DCMIID":"dc.date
    'sedici.contributor.colaborator' : "DCMIID":"dc.contributor
    'sedici.institucionDesarrollo' : "DCMIID":"dc.contributor
    'thesis.degree.name' : "DCMIID":"dc.contributor.degree.name
    'thesis.degree.grantor' : "DCMIID":"dc.contributor.degree.grantor
    'sedici.relation.event' : "DCMIID":"dc.relation
    'sedici.identifier.isbn' : "DCMIID":"dc.identifier
    'sedici.identifier.issn' : "DCMIID":"dc.identifier
    'dc.title' : "DCMIID":"dc.title
    'sedici.title.subtitle' : "DCMIID":"dc.title
    'sedici.creator.person' : "DCMIID":"dc.creator
    'dc.language' : "DCMIID":"dc.language
    'dc.subject' : "DCMIID":"dc.subject
    'sedici.contributor.director' : "DCMIID":"dc.contributor
    'sedici.contributor.codirector' : "DCMIID":"dc.contributor
    'dc.type' : "DCMIID":"dc.type
    'sedici.relation.journalTitle' : "DCMIID":"dc.title
    'sedici.relation.journalVolumeAndIssue' : "DCMIID":"dc.relation.journalVolumeAndIssue
    'mods.originInfo.place' : "DCMIID":"mods.originInfo.place
    'id' : {"type": str},
    'dc.subject.ford' : "DCMIID":"dc.subject"}

Example JSON output format:
{
  "dc.language": "value",
  "dc.subject": "value",
  "dc.title": "value",
  "dc.type": "value",
  "sedici.creator.person": "value",
  "dc.subject.ford": "value",
  "sedici.contributor.director": "value",
  "sedici.contributor.codirector": "value",
  "sedici.title.subtitle": "value",
  "sedici.relation.journalVolumeAndIssue": "value",
  "sedici.relation.journalTitle": "value",
  "sedici.identifier.issn": "value"
}

Now, extract the information from the following text and provide it in the specified JSON format:"""



"""
If dc.type is "Tesis", the following keys must not be present:
-"sedici.relation.journalVolumeAndIssue
-"sedici.relation.journalTitle"
-"sedici.identifier.issn"
If dc.type is "Artículo", the following keys must not be present:
-"sedici.contributor.director"
-"sedici.contributor.codirector"
"""