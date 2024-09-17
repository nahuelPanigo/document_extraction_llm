from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[0]

MODEL_PARAMETERS = {
    "LOCATION" : ROOT_DIR / "fine-tuned-model",
    "NAME" : "allenai/led-base-16384",
    "MAX_TOKENS_INPUT" : 8192,
    "MAX_TOKENS_OUTPUT" : 512 
}



FILETYPES = [".pdf", ".docx"]

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