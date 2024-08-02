URL_GROBID_SERVICES="http://localhost:8070/api/processFulltextDocument"

FILETYPES = [".pdf", ".docx"]

JSON_STRUCT={"DATE": "dc.date.issued",
            "ABSTARCT":["dc.description.abstract","abstract"],
            "LANGUAJE": ["dc.language","teiHeader"],
            "SUBJECT": "dc.subject",
            "TITLE" : ["dc.title","title"],
            "TYPE": "dc.type",
            "AUTHOR": ["sedici.creator.person","author"],
            #"sedici.description.note": "Tesis digitalizada en SEDICI gracias a la colaboraci\u00f3n de la Biblioteca de la Facultad de Ingenier\u00eda (UNLP).",
            "sedici.subject.materias": "Ingenier\u00eda",
            #"sedici.description.fulltext": "true",
            "mods.originInfo.place": "Facultad de Ingenier\u00eda",
            "sedici.subtype": "Tesis de grado",
            "sedici.rights.license": "Creative Commons Attribution 3.0 Unported (CC BY 3.0)",
            "sedici.rights.uri": "http://creativecommons.org/licenses/by/3.0/",
            "sedici.contributor.director": "Rifaldi, Alfredo",
            "thesis.degree.name": "Ingeniero Electricista",
            "thesis.degree.grantor": "Universidad Nacional de La Plata",
            "sedici.date.exposure": "1991",
            #"sedici2003.identifier": "ARG-UNLP-TDG-0000000911"}
            }