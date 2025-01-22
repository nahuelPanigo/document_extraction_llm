import os
from utils.pdf_reader import PdfReader
from utils.read_and_write_files import write_to_text
from multiprocessing import Pool
from constant import DATA_FOLDER


PDF_FOLDER = DATA_FOLDER / "pdfs3"
TXT_FOLDER = DATA_FOLDER / "texts3"

def process_pdf_data_wrapper(args):
    return process_pdf_data(*args)

def process_pdf_data(pdf_path, pdf_id):
    print(pdf_id)
    try:
        pdfreader = PdfReader()
        text = pdfreader.extract_text_with_xml_tags(pdf_path)
        txt_filename=TXT_FOLDER / f"{pdf_id}.txt"
        write_to_text(txt_filename,text)
    except:
        print(pdf_id," este rompee")

def extract_text():
    text = [x.replace(".txt",".pdf") for x in os.listdir(TXT_FOLDER)]
    pdf_paths = [(os.path.join(PDF_FOLDER,x),x.replace(".pdf","")) for x in os.listdir(PDF_FOLDER) if x not in text]   
    with Pool(2) as pool:
        pool.map(process_pdf_data_wrapper, pdf_paths)
    return




if __name__ == '__main__':
    extract_text()
    #print(process_pdf_data(PDF_FOLDER /"10915-94897.pdf","10915-94897"))