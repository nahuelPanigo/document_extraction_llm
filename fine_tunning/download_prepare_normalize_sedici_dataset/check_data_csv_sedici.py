import pandas as pd
from constant import DATA_FOLDER
import requests
from bs4 import BeautifulSoup
import re
import time


csv_file = pd.read_csv(DATA_FOLDER / "sedici.csv", low_memory=False)

pd.set_option('display.max_colwidth', None)  


columns_types = {
    'sedici.rights.license' : {'type':str,'cant' : "unique","DCMIID":"dc.rights"},
    'sedici.rights.uri' : {'type':str,'cant' : "unique","DCMIID":"dc.rights"},
    'sedici.relation.isRelatedWith' : {'type':str,'cant' : "unique","DCMIID":"dc.relation"},
    'dc.coverage.spatial' : {'type':str,'cant' : "unique","DCMIID":"dc.coverage"},
    'dc.coverage.temporal' : {'type':str,'cant' : "unique","DCMIID":"dc.coverage"},
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
    'collection' : {'type':str,'cant' : "unique","DCMIID":"collection"},
    'dc.description.filiation' : {'type':str,'cant' : "unique","DCMIID":"dc.description.filiation"},
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
        # For many, concatenate non-null values
        combined_series_list = []  # Create a list to hold series

        for value in values:
            non_null_series = subset_df[value].dropna()  # Drop nulls from each series
            combined_series_list.append(non_null_series)  # Append the non-null series

        # Combine all values into one series
        combined_series = pd.concat(combined_series_list, ignore_index=True)

        # Set the result in the DataFrame; take the first non-null value
        subset_df[key] = combined_series[combined_series.first_valid_index()] if not combined_series.empty else None



columns_to_drop = [x for x in columns_to_select if x not in columns_types.keys()]

subset_df.drop(columns_to_drop, axis=1, inplace=True)

subset_df['dc.date.issued'] = pd.to_datetime(subset_df['dc.date.issued'], errors='coerce')

# Create a boolean mask for filtering: True where the year is greater than 2017
mask = subset_df['dc.date.issued'].dt.year > 2018

# Use the mask to filter the DataFrame
filtered_df = subset_df[mask]
# Print the remaining columns to verify
filtered_df.to_csv(DATA_FOLDER / "sedici_filtered_2018_2024.csv", index=False)

# # # Muestra la nueva columna combinada
# # print(subset_df[['dc.description.abstract_combined']].head())s

# #filtered_df = subset_df[subset_df['dc.description.filiation_combined'].notnull()]

# filtered_df = subset_df[subset_df['sedici.contributor.compiler[es]'].notnull()]



# #filtered_df = subset_df[subset_df['dc.description.filiation_combined'] != '']
# print(filtered_df.info())

# extensiones = {}
# for uri in filtered_df['dc.identifier.uri'].head(100):
#     try:
#         url = re.sub(r'\s+', '', uri.split("|")[0]) 
#     except:
#         print("float error")
#     try:
#         response =requests.get(url,timeout=10)
#         time.sleep(4)
#     except requests.exceptions.RequestException as e:  
#         print(f"could not request url:{url}", e)
#     try:
#         soup = BeautifulSoup(response.content , "html.parser")
#         files = soup.find_all(class_='file-list')[0]
#         for x in files.children:
#             try:
#                 splited = x.get_text(strip=True).split("-")
#                 ext = splited[len(splited)-1]
#                 if (ext in extensiones):
#                     extensiones[ext] +=1
#                 else:
#                     extensiones[ext] = 1
#             except Exception as e:
#                 print("error no descripcion o extension",e)
#     except Exception as e:
#         print(f"error en la uri{url}",e,response.status_code)
#         if response.status_code == 429:
#             time.sleep(10)
# print(extensiones)
# # # Filter for non-nuell values in sedici.identifier.uri[]

# # non_null_subset = subset_df[subset_df['sedici.identifier.uri[]'].notnull()]

# # # Display the non-null rows
# # print(non_null_subset)