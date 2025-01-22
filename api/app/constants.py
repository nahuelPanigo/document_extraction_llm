from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[0]

MODEL_PARAMETERS = {
    "LOCATION" : ROOT_DIR / "fine-tuned-model",
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

PROMPT = """
You’re an advanced data extractor with expertise in structuring and formatting information into JSON format from various texts.
Your task is to extract specific information from a given text and present it in the required JSON format.

you must extract title,subtitle, language, type, originInfo-place, author, date, ford-subject, journalTitle

 **Example JSON Output:**
 ```json
 {
   "language": "es",
   "ford-subject": "Psicología y ciencias cognitivas",
   "subject": "['Subjetividad', 'Infancias institucionalizadas', 'Salud mental']",
   "title": "Infancias institucionalizadas en casas de abrigo",
   "type": "Articulo",
   "author": "['Gastaminza, Florencia', 'Pérez, Edith Alba']",
   "journalTitle": "Investigación Joven",
   "originInfo-place": "Universidad Nacional de La Plata",
   "issn": "2314-3991",
   "date": "2019",
   "subtitle": "Una propuesta preliminar en el campo de las políticas públicas, la salud mental y el género"
}

Now You Must extract the information in json Format provided from the following text:
"""