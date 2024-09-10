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
#BASE_MODEL="allenai/led-base-16384"
BASE_MODEL="google/gemma-2-2b"
MAX_TOKENS_INPUT= 512
MAX_TOKENS_OUTPUT= 512
LOG_DIR = ROOT_DIR /  "log"
FINAL_MODEL_PATH =ROOT_DIR / "fine-tuned-model"
CHECKPOINT_MODEL_PATH = ROOT_DIR / "results"