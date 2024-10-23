import pandas as pd
from constant import DATA_FOLDER,PDF_URL
import requests
from bs4 import BeautifulSoup
import re
import time
import os

PDF_FOLDER = DATA_FOLDER / "pdfs3/"
TXT_FOLDER = DATA_FOLDER / "texts3/"

csv_file = pd.read_csv(DATA_FOLDER / "sedici.csv", low_memory=False)

pd.set_option('display.max_colwidth', None)  


ford_sedici_materias = {"Geofísica":"Ciencias físicas","Administración":"Economía y negocios","Agrimensura":"Ciencias de la tierra y ciencias ambientales relacionadas","Antropología":"Otras humanidades","Arqueología":"Historia y arqueología","Arquitectura":"Ingeniería civil","Artes Audiovisuales":"Artes","Artes Plásticas":"Artes","Artes y Humanidades":"Artes","Astronomía":"Ciencias físicas","Bellas Artes":"Artes","Bibliotecología y ciencia de la información":"Geografía social y económica","Bibliotecología":"Geografía social y económica","Biología":"Ciencias biológicas","Bioquímica":"Ciencias biológicas","Botánica":"Ciencias biológicas","Ciencias Agrarias":"Agricultura,silvicultura y pesca","Ciencias Astronómicas":"Ciencias físicas","Ciencias de la Educación":"Educación","Ciencias Económicas":"Economía y negocios","Ciencias Exactas":"Ciencias físicas","Ciencias Informáticas":"Ciencias de la computación e información","Ciencias Jurídicas":"Derecho","Ciencias Médicas":"Medicina básica","Ciencias Naturales":"Ciencias biológicas","Ciencias Sociales":"Sociología","Ciencias Veterinarias":"Ciencia veterinaria","Comunicación Social":"Geografía social y económica","Comunicación Visual":"Geografía social y económica","Comunicación":"Geografía social y económica","Contabilidad":"Economía y negocios","Cooperativismo":"Economía y negocios","Cs de la Computación":"Ciencias de la computación e información","Cs. Agrícolas y Biológicas":"Ciencias biológicas","Cs. Ambientales":"Ciencias de la tierra y ciencias ambientales relacionadas","Cs. de la Tierra y Planetarias":"Ciencias de la tierra y ciencias ambientales relacionadas","Cs. de los Materiales":"Ingeniería de los materiales","Cs. Sociales":"Sociología","Derecho":"Derecho","Derechos Humanos":"Derecho","Desarrollo Regional":"Otras ciencias sociales","Diseño Industrial":"Biotecnología industrial","Ecología":"Biotecnología ambiental","Econometría y Finanzas":"Economía y negocios","Economía":"Economía y negocios","Educación Física":"Educación","Educación":"Educación","Electrotecnia":"Ingeniería eléctrica, electrónica e informática","Energía":"Ingenieria ambiental","Farmac.":"Biotecnología médica","Farmacia":"Biotecnología médica","Filosofía":"Filosofía, ética y religión","Física y Astronomía":"Ciencias físicas","Física":"Ciencias físicas","Genética y Biología Molecular":"Ciencias biológicas","Geografía":"Otras ciencias sociales","Geología":"Ciencias de la tierra y ciencias ambientales relacionadas","Gestión y Contabilidad":"Economía y negocios","Historia del Arte":"Artes","Historia":"Historia y arqueología","Humanidades":"Otras humanidades","Información":"Geografía social y económica","Informática":"Ciencias de la computación e información","Ingeniería Aeronáutica":"Ingeniería mecánica","Ingeniería Agronómica":"Agricultura,silvicultura y pesca","Ingeniería Civil":"Ingeniería civil","Ingeniería Electrónica":"Ingeniería eléctrica, electrónica e informática","Ingeniería en Materiales":"Ingeniería de los materiales","Ingeniería Forestal":"Agricultura,silvicultura y pesca","Ingeniería Hidráulica":"Ingeniería civil","Ingeniería Mecánica":"Ingeniería mecánica","Ingeniería Química":"Ingeniería química","Ingeniería":" Otras ingenierías y tecnologías","Inmunología y Microbiología":"Ciencias biológicas","Legislación":"Derecho","Letras":"Lenguas y literatura","Matemática":"Matemáticas","Medicina":"Medicina clínica","Medios de Comunicación":"Geografía social y económica","Multidisciplina":"Otras humanidades","Multimedia":"Geografía social y económica","Música":"Artes","Negocios":"Economía y negocios","Neurociencia":"Psicología y ciencias cognitivas","Odontología":"Medicina clínica","Paleontología":"Ciencias de la tierra y ciencias ambientales relacionadas","Periodismo":"Geografía social y económica","Política":"Ciencia política","Profesiones de la Salud":"Ciencias de la salud","Psicología":"Psicología y ciencias cognitivas","Psiquiatría":"Medicina clínica","Química":"Ciencias químicas","Redes y Seguridad":"Ciencias de la computación e información","Relaciones Internacionales":"Ciencia política","Salud":"Ciencias de la salud","Sociología Jurídica":"Derecho","Sociología":"Sociología","Software":"Ciencias de la computación e información","Toxicología y Farmacia":"Biotecnología médica","Trabajo Social":"Sociología","Turismo":"Medios de comunicación","Urbanismo":"Ingeniería civil","Veterinaria":"Ciencia veterinaria","Zoología":"Ciencias biológicas","Zoonosis":"Ciencia veterinaria"}

def combine_non_nulls(row):
    non_null_values = [row[col] for col in values if pd.notna(row[col])]
    if non_null_values:
        if len(non_null_values) == 1:
            return non_null_values[0]
        else:
            return non_null_values
    else:
        return None



def transform_uri(uri):
    try:
        # Intentar hacer el split y replace
        return uri.split("handle/")[1].replace("/", "-")
    except Exception as e:
        print("uri mal formateado",uri,e)   
        return None


def transform_subject(subject):
    try:
        subject_split1 = subject.split("||")[0]
        subject_split2 = subject_split1.split("::")[0].strip()
        return ford_sedici_materias[subject_split2]
    except Exception as e:
        print("subject mal formateado",subject_split1,subject_split2,subject,e)   
        return None

def transform_contributor(contributor):
    try:
        contributor_split = contributor.split("||")
        contributors = []
        for elem in contributor_split:
            elem_split = elem.split("::")
            contributors.append(elem_split[0].strip())
        if len(contributors) == 1:
            return contributors[0]
        return contributors
    except Exception as e:
        print("contributor mal formateado",contributor,e)
        return None

def transform_institution(institution):
    try:
        institution_split = institution.split("||")
        institutions = []
        for elem in institution_split:
            elem_split = elem.split("::")
            institutions.append(elem_split[0].strip())
        if len(institutions) == 1:
            return institutions[0]
        return institutions
    except Exception as e:
        print("contributor mal formateado",institution,e)
        return None





columns_types = {
    'sedici.rights.license' : {'type':str,'cant' : "unique","DCMIID":"dc.rights"},
    'sedici.rights.uri' : {'type':str,'cant' : "unique","DCMIID":"dc.rights"},
    'sedici.relation.isRelatedWith' : {'type':str,'cant' : "unique","DCMIID":"dc.relation"},
#    'dc.coverage.spatial' : {'type':str,'cant' : "unique","DCMIID":"dc.coverage"},
#    'dc.coverage.temporal' : {'type':str,'cant' : "unique","DCMIID":"dc.coverage"},
    'sedici.identifier.uri' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier"},
    'dc.identifier.uri' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier"},
    'sedici.contributor.editor' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'sedici.contributor.compiler' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'dc.publisher' : {'type':str,'cant' : "unique","DCMIID":"dc.publisher"},
    'dc.date.issued' : {'type': pd.Timestamp,'cant' : "unique","DCMIID":"dc.date"},
    'sedici.contributor.colaborator' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'dc.description.abstract' : {'type':str,'cant' : "many","DCMIID":"dc.description"},
    'sedici.institucionDesarrollo' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'thesis.degree.name' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor.degree.name"},
    'thesis.degree.grantor' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor.degree.grantor"},
    'sedici.relation.event' : {'type':str,'cant' : "unique","DCMIID":"dc.relation"},
    'sedici.identifier.isbn' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier"},
    'sedici.identifier.issn' : {'type':str,'cant' : "unique","DCMIID":"dc.identifier"},
    'dc.title' : {'type':str,'cant' : "unique","DCMIID":"dc.title"},
    'sedici.title.subtitle' : {'type':str,'cant' : "unique","DCMIID":"dc.title"},
    'sedici.creator.person' : {'type':str,'cant' : "unique","DCMIID":"dc.creator"},
    'dc.language' : {'type':str,'cant' : "unique","DCMIID":"dc.language"},
    'dc.subject' : {'type':str,'cant' : "unique","DCMIID":"dc.subject"},
    'sedici.contributor.director' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'sedici.contributor.codirector' : {'type':str,'cant' : "unique","DCMIID":"dc.contributor"},
    'dc.type' : {'type':str,'cant' : "unique","DCMIID":"dc.type"},
    'sedici.relation.journalTitle' : {'type':str,'cant' : "unique","DCMIID":"dc.title"},
    'sedici.relation.journalVolumeAndIssue' : {'type':str,'cant' : "unique","DCMIID":"dc.relation.journalVolumeAndIssue"},
    'sedici.subject.materias' : {'type':str,'cant' : "unique","DCMIID":"dc.subject"},
    'mods.originInfo.place' : {'type':str,'cant' : "unique","DCMIID":"mods.originInfo.place"},
#    'dc.description.filiation' : {'type':str,'cant' : "unique","DCMIID":"dc.description.filiation"},
}

columns_to_select = columns_types.keys()


final_columns = {x:[] for x in columns_to_select}
columns = csv_file.columns.tolist()
for x in columns_to_select:
    for y in columns:
        if x in y :
            final_columns[x].append(y)


columns_to_select = [item for sublist in final_columns.values() for item in sublist]



subset_df = csv_file[columns_to_select].copy()

for key, values in final_columns.items():
    if columns_types[key]['cant'] == "unique":
        # Combine values using backfill
        subset_df[key] = subset_df[values].bfill(axis=1).iloc[:, 0]

        # Set the column to None if all values were NaN
        subset_df[key] = subset_df[key].where(subset_df[key].notnull(), None)

    else:
        # Aplicar la función por filas (axis=1) para combinar los valores no nulos
        subset_df[key] = subset_df.apply(combine_non_nulls, axis=1)

columns_to_drop = [x for x in columns_to_select if x not in columns_types.keys()]

subset_df.drop(columns_to_drop, axis=1, inplace=True)

subset_df['dc.date.issued'] = pd.to_datetime(subset_df['dc.date.issued'], errors='coerce')

# Create a boolean mask for filtering: True where the year is greater than 2019
mask = subset_df['dc.date.issued'].dt.year > 2017

# Use the mask to filter the DataFrame
filtered_df = subset_df[mask]

# Print the remaining columns to verify



set_dctype = {x : 0 for x in filtered_df["dc.type"].unique()}
for e in filtered_df["dc.type"]:
    set_dctype[e]+=1

filter = ["Libro","Objeto de conferencia","Tesis","Articulo"]

filtered_df = filtered_df.loc[filtered_df['dc.type'].isin(filter)]


filtered_df["not_null"] = filtered_df.notnull().sum(axis=1)

filtered_df = filtered_df.sort_values(by=['not_null'], ascending=False).drop(columns=['not_null'])


texts =[x.replace(".txt","") for x in os.listdir(TXT_FOLDER)]

filtered_df['id'] = filtered_df['dc.identifier.uri'].apply(transform_uri)
filtered_df = filtered_df.loc[filtered_df['id'].isin(texts)]



filtered_df['dc.subject.ford'] = filtered_df['sedici.subject.materias'].apply(transform_subject)
filtered_df.drop('sedici.subject.materias',axis=1,inplace=True)

contributors = ["sedici.contributor.compiler","sedici.contributor.director","sedici.contributor.codirector","sedici.creator.person","sedici.contributor.colaborator"]

for contributor in contributors:    
    filtered_df[contributor] = filtered_df[contributor].apply(transform_contributor)

institutions = ["mods.originInfo.place","sedici.institucionDesarrollo"]

for institution in institutions:
    filtered_df[institution] = filtered_df[institution].apply(transform_institution)

filtered_df["dc.subject"] = filtered_df["dc.subject"].apply(lambda x: x.split("||") if pd.notna(x) else None)


# guardar csv con los metadatos extraidos y cambiados
filtered_df.to_csv(DATA_FOLDER / "sedici_filtered_2018_2024.csv", index=False)  

# Convertir listas a strings en la columna "sedici.institucionDesarrollo"
filtered_df["sedici.institucionDesarrollo"] = filtered_df["sedici.institucionDesarrollo"].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

# Ahora puedes obtener los valores únicos sin problemas
print(filtered_df["sedici.institucionDesarrollo"].unique())

# for uri in filtered_df['dc.identifier.uri'].head(5000):
#     try:
#         id = uri.split("handle/")[1]
#         url = PDF_URL+id+"/Documento_completo.pdf?sequence=1&isAllowed=y"
#         response =requests.get(url,timeout=10)
#         time.sleep(2)
#         id = id.replace("/","-")
#         if response.status_code == 200:
#             file_path = PDF_FOLDER / f"{id}.pdf"
#             with open(file_path, "wb") as f:
#                 f.write(response.content)
#             print("bajo",id)
#     except Exception as e:
#         print(f"error en la uri{url}",e,response.status_code)
#         if response.status_code == 429:
#             time.sleep(10)
# # Filter for non-nuell values in sedici.identifier.uri[]

# non_null_subset = subset_df[subset_df['sedici.identifier.uri[]'].notnull()]

# # Display the non-null rows
