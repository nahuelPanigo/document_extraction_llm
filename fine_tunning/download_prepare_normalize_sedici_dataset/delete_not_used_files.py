import os
from constant import JSON_FOLDER,PDF_FOLDER,XML_FOLDER,TXT_FOLDER,DATASET_WITH_TEXT_DOC
from utils.read_and_write_files import read_data_json

data = read_data_json(JSON_FOLDER / DATASET_WITH_TEXT_DOC, "utf-8")
correct_files_ids = list(data.keys())

pdfs_ids = [x.replace(".pdf","") for x in os.listdir(PDF_FOLDER) if x.replace(".pdf","") not in correct_files_ids]


# Eliminar los archivos de la lista pdfs_ids
for file in pdfs_ids:
    file_path_pdf = os.path.join(PDF_FOLDER, file+".pdf")
    file_path_xml = os.path.join(XML_FOLDER, file+".xml")
    file_path_txt = os.path.join(TXT_FOLDER, file+".txt")
    try:
        os.remove(file_path_pdf)
        print(f"Archivo eliminado: {file_path_pdf}")
        os.remove(file_path_xml)
        print(f"Archivo eliminado: {file_path_xml}")
        os.remove(file_path_txt)
        print(f"Archivo eliminado: {file_path_txt}")
    except OSError as e:
        print(f"Error al eliminar el archivo {file}: {e}")



print(len(correct_files_ids))
print(len(os.listdir(TXT_FOLDER)))
print(len(os.listdir(PDF_FOLDER)))
print(len(os.listdir(XML_FOLDER)))
