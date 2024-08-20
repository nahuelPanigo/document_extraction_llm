import re
from constant import TXT_FOLDER,DATA_FOLDER,JSON_FOLDER,DATASET_FILENAME
from utils.normalice_data import normalize_text
from utils.read_and_write_files import read_data_txt,read_data_json,write_to_json
from utils.colors_terminal import Bcolors

def find_abstract_fragment(norm_text, abstract, first,last,text):
    abstract_words = abstract.split()
    first_3_words = ' '.join(abstract_words[first:first+3])
    last_word = " "+abstract_words[last]

    pattern = re.escape(first_3_words) + r'.*?' + re.escape(last_word)
    match = re.search(pattern, norm_text)
    
    if match:
        start = match.start()
        end = match.end()
        return norm_text[start:end], True
    return None, False

def verify_abstract_match(norm_text,text,norm_abstract):
    final_word = len(norm_abstract.split()) - 1
    first_word = 0
    fragment, found = find_abstract_fragment(norm_text, norm_abstract, first_word,first_word,text)
    try:
        for x in range(5):
            fragment, found = find_abstract_fragment(norm_text, norm_abstract, first_word+x,final_word,text)
            if found:
                return fragment, True
            fragment, found = find_abstract_fragment(norm_text, norm_abstract, first_word,final_word-x,text)
            if found:
                return fragment, True
    except:
        return None, False
    return None,False

def print_results(normalized_text,normalized_abstract,id,col_20_40,col_40_100,text,abstract):
    if(abstract.split()[0] == "[Autogenerado]:"):
        return True,abstract
    extracted_text, matches = verify_abstract_match(normalized_text,text, normalized_abstract)
    if matches:
        len_abstract = len(normalized_abstract.split())
        not_words_abstract_in_text = [x for x in normalized_abstract.split() if x not in normalize_text(extracted_text)]
        not_words_text_in_abstract = [x for x in normalize_text(extracted_text).split()if x not in normalized_abstract]
        len_not_text = len(not_words_abstract_in_text) if len(not_words_abstract_in_text) != 0 else 1
        len_not_abstract = len(not_words_text_in_abstract) if len(not_words_text_in_abstract) != 0 else 1
        prom_abstr = len_not_abstract / len_abstract
        prom_text = len_not_text /len_abstract
        
        if (prom_text < 0.2) and (prom_abstr < 0.2 ):
            print(Bcolors.OKGREEN+"ok: "+id + Bcolors.ENDC)
            return True,extracted_text
        if (prom_text < 0.4) and (prom_abstr < 0.4 ):
            col_20_40.append(id)
            print(normalized_abstract)
            print("---------------------------------------")
            print(extracted_text)
            print(Bcolors.WARNING+"verificar a mano del id "+id+Bcolors.ENDC)
        else:
            col_40_100.append(id)
            print(Bcolors.FAIL+"verificar a mano + 40 %"+id+Bcolors.ENDC)
        return False,extracted_text
    else:
        col_40_100.append(id)
        print(Bcolors.FAIL+"verificar a mano + 40 %"+id+Bcolors.ENDC)
        return False,extracted_text






json_abs_check = "abstract_to_check.json"


dict = read_data_json(DATA_FOLDER+json_abs_check,"utf-8")
dict_metadata = read_data_json(JSON_FOLDER+DATASET_FILENAME,"utf-8")
ids = [x[0] for x in dict.items() if "dc.description.abstract" in x[1]]
res = True
col_20_40 = []
col_40_100 = []

for id in ids:
    print("----------------------------------")
    abstract = dict_metadata[id]["dc.description.abstract"]
    text = read_data_txt(TXT_FOLDER+id+".txt","utf-8")
    normalized_text = normalize_text(text)
    try:
        normalized_abstract = normalize_text(abstract)
        res,extracted_text = print_results(normalized_text,normalized_abstract,id,col_20_40,col_40_100,text,abstract)
    except:
        extracted_text = []
        for abs in abstract:
            normalized_abstract = normalize_text(abs)
            res,extracted = print_results(normalized_text,normalized_abstract,id,col_20_40,col_40_100,text,abs)
            extracted_text.append(extracted)
            if(not res):
                break
    if(res):
        dict_metadata[id]["dc.description.abstract"] =  extracted_text
        #dict.pop(id)
    else:
        dict_metadata[id]["dc.description.abstract"] =  extracted_text
        break

write_to_json(DATA_FOLDER+json_abs_check,dict,"utf-8")
write_to_json(JSON_FOLDER+DATASET_FILENAME,dict_metadata,"utf-8")
