from constant import PDF_FOLDER,JSON_FILENAME2
from utils import read_json,write_json
from pdf_reader import PdfReader



if  __name__ == "__main__":
    final_dict = {}
    reader =  PdfReader()
    dict = read_json(JSON_FILENAME2)
    lista =  []    
    for key,value in dict.items():
          lista = lista + list(value.keys())
    #     filename = PDF_FOLDER /  f"{key}.pdf"
    #     text = reader.extract_text_with_xml_tags(filename)
    #     value ["original_text"] =   text
    #     final_dict[key] = value
    # write_json("metadata_correjidaFinal_text.json",final_dict)
    print(set(lista))