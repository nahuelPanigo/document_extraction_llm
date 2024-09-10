import os
from utils.pdf_reader import PdfReader
from utils.read_and_write_files import write_to_text
from multiprocessing import Pool
from constant import PDF_FOLDER,DATA_FOLDER

TXT_FOLDER2 = DATA_FOLDER / "texts2"

def process_pdf_data_wrapper(args):
    return process_pdf_data(*args)

def process_pdf_data(pdf_path, pdf_id):
    pdfreader = PdfReader()
    text = pdfreader.extract_text_with_xml_tags(pdf_path)
    txt_filename=TXT_FOLDER2+pdf_id+".pdf"
    write_to_text(txt_filename,text)


def extract_text():
    pdf_paths = [os.path.join(PDF_FOLDER,x) for x in os.listdir(PDF_FOLDER)]   
    with Pool(2) as pool:
        pool.map(process_pdf_data_wrapper, pdf_paths)
    return




if __name__ == '__main__':
    extract_text()