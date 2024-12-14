from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[0]

MODEL_PARAMETERS = {
    "LOCATION" : ROOT_DIR / "fine-tuned-model2",
    "NAME" : "allenai/led-base-16384",
    "MAX_TOKENS_INPUT" : 4096,
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
Now, extract the information from the following text and provide it in the specified JSON format:"""