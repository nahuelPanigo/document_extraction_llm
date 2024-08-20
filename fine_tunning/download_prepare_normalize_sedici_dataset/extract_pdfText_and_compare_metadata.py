
import os
from utils.read_and_write_files import read_data_pdf,write_to_text,read_data_json
from multiprocessing import Pool
from constant import DATASET_FILENAME,PDF_FOLDER,TXT_FOLDER,JSON_FOLDER


def process_pdf_data_wrapper(args):
    return process_pdf_data(*args)

def process_pdf_data(pdf_path, pdf_id):
    text = read_data_pdf(pdf_path)
    txt_filename=TXT_FOLDER+pdf_id+".pdf"
    write_to_text(txt_filename,text)


def extract_text():
    keys = [x.replace(".txt", "") for x in os.listdir(TXT_FOLDER)]   
    data_dict = read_data_json(JSON_FOLDER+DATASET_FILENAME,"utf-8")
    newDict= {x:v for x,v in data_dict.items() if x not in keys} 
    pdf_paths = [(os.path.join(PDF_FOLDER, f"{key}.pdf"), key) for key, reg in newDict.items()]
    with Pool(2) as pool:
        pool.map(process_pdf_data_wrapper, pdf_paths)
    return




if __name__ == '__main__':
    extract_text()
