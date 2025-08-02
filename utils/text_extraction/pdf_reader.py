import pdfplumber
#from PIL import Image
#import numpy as np
#from easyocr import Reader
#from transformers import AutoProcessor, AutoModelForCausalLM
#from paddleocr import PaddleOCR
import time



class PdfReader:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PdfReader, cls).__new__(cls)
        return cls.instance

    def get_correct_tag(self,font_size,sizes):
        """this function returns the correct tag based on the font size"""
        if font_size >= sizes['h1']:
            return "h1"
        if font_size >= sizes['h2']:
            return "h2"
        return "p"

  
    # def get_first_tag(self,page,sizes_dict):
    #         try:
    #             first_word = page.extract_words()[0]
    #             current_fontsize = round(float(first_word['height'])) 
    #             return self.get_correct_tag(current_fontsize,sizes_dict),current_fontsize
    #         except:
    #             return "p",10


    def extract_text_with_xml_tags(self, pdf_path):
        sizes_dict =  self.get_fontsizes(pdf_path)
        print(sizes_dict)
        with pdfplumber.open(pdf_path) as pdf:
            try:
                first_word = pdf.pages[0].extract_words()[0]
                current_fontsize = round(float(first_word['height'])) 
                current_tag = self.get_correct_tag(current_fontsize,sizes_dict)
            except:
                current_tag = "p"    
                current_fontsize = 10
            text_with_tags = f"<{current_tag}>"
            current_text = []
            words = 0
            for page in pdf.pages:
                words += len(page.extract_words())
                for obj in page.extract_words():
                    font_size = round(float(obj['height']))  # Redondear a entero más cercano
                    if (current_fontsize != font_size):
                        text_with_tags += " ".join(current_text) 
                        text_with_tags += f"</{current_tag}>"
                        current_text = []
                        current_fontsize = font_size
                        current_tag = self.get_correct_tag(current_fontsize,sizes_dict)
                        text_with_tags += f"<{current_tag}>"
                    current_text.append(obj['text'])
                if words > 4000:
                    text_with_tags += " ".join(current_text) 
                    text_with_tags += f"</{current_tag}>"
                    return text_with_tags
            text_with_tags += " ".join(current_text)
            text_with_tags += f"</{current_tag}>"
            return text_with_tags
            
    def get_fontsizes(self,pdf_path):
        fontsizes = []
        count = 0
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                count+=1
                if count > 5:
                    break
                for obj in page.extract_words():
                    if round(float(obj["height"])) not in fontsizes and obj["height"] < 40:
                        fontsizes.append(round((float(obj["height"]))))
            fontsizes.sort()
            h1_size = fontsizes[-1]            
            n = len(fontsizes)
            h2_size = fontsizes[int(n * 0.75)] if n > 1 else fontsizes[0]  # 75% percentil
            paragraph_sizes = [size for size in fontsizes if size < h2_size]
            return {
                'h1': h1_size,'h2': h2_size,'p': min(paragraph_sizes) if paragraph_sizes else 0
            }



if __name__ == '__main__':
    pdf_reader = PdfReader()
    from pathlib import Path
    import os
    import time
    ROOT_DIR = Path(__file__).resolve().parents[2]
    DATA_FOLDER = Path(ROOT_DIR / "data" / "sedici")
    PDF_FOLDER = DATA_FOLDER / "pdfs/"
    file = "10915-109000.pdf"
    filepath = PDF_FOLDER / file
    start_time = time.time()
    extracted_text = pdf_reader.extract_text_with_xml_tags(filepath)
    # print(len(extracted_text))
    # print(len(extracted_text.split(" ")))
    # print(extracted_text)
    end_time = time.time()
    print("The time of execution of above program is :",
      (end_time-start_time) * 10**3, "ms")



