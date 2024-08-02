DATA_FOLDER= "C:/Users/Nahuel/Documents/document_extraction_llm/fine_tunning/data/sedici/"
PDFS_FOLDER=DATA_FOLDER+"pdfs/"
XMLS_FOLDER=DATA_FOLDER + "xmls/"
JSONS_FOLDER=DATA_FOLDER+ "jsons/"
#DATASET_URL_BASE = "https://arxiv.org/pdf/"
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
ORIGINAL_FILENAME= "metadata_sedici_files.json"
DATASET_FILENAME="output.json"
LOG_DIR = "/log"
BASE_MODEL="allenai/led-base-16384"
MAX_TOKENS_INPUT= 16384
MAX_TOKENS_OUTPUT= 512 
FINAL_MODEL_PATH = "/fine-tuned-model"
CHECKPOINT_MODEL_PATH = "./results"


{'Objeto de conferencia', 'Articulo', 'Reporte', 'Tesis'}