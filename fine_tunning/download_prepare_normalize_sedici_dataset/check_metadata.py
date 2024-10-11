import re
from constant import DATA_FOLDER,JSON_FOLDER
from utils.normalice_data import normalize_text,build_pattern_issn,build_pattern_volume
from utils.read_and_write_files import read_data_json, read_data_txt,detect_encoding
from utils.colors_terminal import Bcolors

TXT_FOLDER = DATA_FOLDER / "texts2"

csv_file =  "results_from_14k_pfd_text.csv"
json_file = "metadata_to_check4.json"
file_metada = "final_metadata_Chekced2.json"
check_changes_file = "check_results.json"


def parse_and_search_patters_ids(value, pdf_text,key):
    try:
        if(key=="sedici.identifier.issn"):
            pattern =  build_pattern_issn(value)
            return re.search(pattern, pdf_text) is not None
        else:
            pattern = build_pattern_volume(value)
            return re.search(pattern, pdf_text, re.IGNORECASE) is not None
    except:
        return False

def search_text_in_pdf(value, file_text):
    if isinstance(value, list):
        res = []
        for elem in value:
            res.append(search_text_in_pdf(elem,file_text))
        return res
    pattern = re.compile(re.escape(normalize_text(value)), re.IGNORECASE)
    matches = pattern.findall(normalize_text(file_text))
    return bool(matches)


def process_pdf_data_wrapper(args):
    return process_txt_data(*args)

def make_col_split(value):
    if isinstance(value,list):
        col = []
        for elem in value:
            col.extend([word.rstrip(',') for word in elem.split()])
        return col
    return [word.rstrip(',') for word in value.split()]



def process_txt_data(file_path, reg, pdf_id):
    results = {}
    enc=detect_encoding(file_path)['encoding']
    print(pdf_id)
    try:
        pdf_text = read_data_txt(file_path,enc)
        # max_tokens = max((CANT_TOKENS * TOKENS_LENGTH),len(pdf_text))
        # pdf_text = pdf_text[0:max_tokens]
        auth_and_contr = ["sedici.creator.person","sedici.contributor.director"
                        ,"sedici.contributor.juror","sedici.contributor.codirector"]
        issn_isbn_vol =["sedici.identifier.issn","sedici.relation.journalVolumeAndIssue"]
        for key, value in reg.items():
            if key in auth_and_contr :
                result = search_text_in_pdf(make_col_split(value),pdf_text)
            else:
                result = search_text_in_pdf(value, pdf_text)
                if(not result) and (key in issn_isbn_vol):
                    result = parse_and_search_patters_ids(value, pdf_text,key)
            results[key] = (value, result)
        return pdf_id, results
    except:
        print(Bcolors.FAIL + "error en el archivo ",pdf_id,enc + Bcolors.ENDC)
        return pdf_id,{}



#lo que hay que chequear
dict = read_data_json(JSON_FOLDER / json_file,"utf-8")
#la metadata de los archivos solamente las que validaremos en finetunnig
metadata = read_data_json(JSON_FOLDER / file_metada,"utf-8")
check_dict = {}
print(len(dict.keys()))
for key in dict.keys():
    file_path=TXT_FOLDER / f"{key}.txt"
    check_dict [key] = {}
    # enc=detect_encoding(file_path)['encoding']
    # pdf_text = read_data_txt(file_path,enc)
    # text=normalize_text(pdf_text)
    #check_dict [key] ["text"] = text
    reg = {x: metadata[key].get(x,"") for x in dict[key] if x != "dc.description.abstract"}
    res = process_txt_data(file_path,reg,key)
    resultado_lista =[x[1] for x in list(res[1].values())]
    flattened = [item for sublist in resultado_lista for item in (sublist if isinstance(sublist, list) else [sublist])]
    print(flattened)
    if False in flattened:
        print('\x1b[0;31;40m'+"hay claves que no machean en el archivo",key,"claves:"+'\x1b[0m')
        print(res)
        enc=detect_encoding(file_path)['encoding']
        pdf_text = read_data_txt(file_path,enc)
        text=normalize_text(pdf_text)
        print("------------")
        print(text[0:900])
        # print(reg["dc.title"])
        # a =  normalize_text(text[72:228])
        # b =  normalize_text(reg["dc.title"])
        # print([(x, x in a) for x in b.split()])
        # print([(x, x in b) for x in a.split()])
        break
#         value = metadata[key][reg_key]
#         if(isinstance(value,list)):
#             norm_value = normalize_text(' '.join(value))
#         else:
#             norm_value = normalize_text(value)
#         check_dict [key] [reg_key] = value
#         check_dict [key] [reg_key+"norm"] = norm_value
# write_to_json(DATA_FOLDER+"check_con_attr_y_txt.json",check_dict,"utf-8")