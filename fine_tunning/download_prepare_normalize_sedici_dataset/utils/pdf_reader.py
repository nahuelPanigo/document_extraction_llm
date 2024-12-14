import pdfplumber
#from PIL import Image
#import numpy as np
import cv2
import numpy as np
#from easyocr import Reader
#from transformers import AutoProcessor, AutoModelForCausalLM
from paddleocr import PaddleOCR
import time



class PdfReader:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PdfReader, cls).__new__(cls)
        return cls.instance


    """commented because not used OCR and MULTIMODAL TOO MUCH TIME"""
    # def pdf_page_to_text_molmo(image):
    #     processor = AutoProcessor.from_pretrained(
    #         'allenai/MolmoE-1B-0924',
    #         trust_remote_code=True,
    #         torch_dtype='auto',
    #         device_map='auto'
    #     )
    #     model = AutoModelForCausalLM.from_pretrained(
    #         'allenai/MolmoE-1B-0924',
    #         trust_remote_code=True,
    #         torch_dtype='auto'
    #     )

    # def extract_ocr(self,image):
    #     try:
    #         np_array = np.frombuffer(image, np.uint8)
    #         image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    #         reader = Reader(['es'])
    #         result = reader.readtext(image, detail=0)
    #         return " ".join(result)
    #     except:
    #         return ""

       


    def extract_text_with_xml_tags2(self, pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            sizes_dict =  self.get_fontsizes(pdf_path)
            current_tag,current_fontsize = self.get_first_tag(pdf.pages[0],sizes_dict)
            text_with_tags = f"<{current_tag}>"
            current_text = []
            for page in pdf.pages:
                text_with_tags,current_tag,current_text,current_fontsize = self.extract_page_pdf_plumber(page,current_tag,current_text,current_fontsize,text_with_tags,sizes_dict)
                if(len(text_with_tags.split(" ")) > 4000):
                    return text_with_tags
            text_with_tags += " ".join(current_text)
            text_with_tags += f"</{current_tag}>"
            return text_with_tags

    def read_text_from_image_paddle(image):
        nparray = np.frombuffer(image,np.uint8)
        image = cv2.imdecode(nparray, cv2.IMREAD_COLOR)
        ocr = PaddleOCR(lang = 'es')
        result = ocr.ocr(image,cls = False)
        result = " ".join([word_info[1][0] for line in result for word_info in line])
        return result
   
    def initialize_tags_and_current(self,current_text,current_tag,font_size,text_with_tags,sizes_dict):
        text_with_tags += " ".join(current_text)
        text_with_tags += f"</{current_tag}>"
        current_fontsize = font_size
        current_tag = self.get_correct_tag(current_fontsize, sizes_dict)
        text_with_tags += f"<{current_tag}>"
        return [],current_tag,current_fontsize,text_with_tags
    
    def initialize_tags_and_current2(self,current_text,current_tag,font_size,text_with_tags,sizes_dict):
        text_with_tags += " ".join(current_text)
        text_with_tags += f"</{current_tag}>"
        current_fontsize = font_size
        current_tag = self.get_correct_tag(current_fontsize, sizes_dict)
        return [],current_tag,current_fontsize,text_with_tags

    def extract_page_pdf_plumber(self, page, current_tag, current_text, current_fontsize, text_with_tags, sizes_dict):
        # Extraer tanto las palabras como las imágenes
        words = page.extract_words()  # Extrae texto
        images = [
            {
                'data': image['stream'].get_data(),
                'top': image['top'],
                'left': image['left']
            }
            for image in page.images
        ]
        images.sort(key=lambda x: (x['top'], x['left']))
        for word in words:
            if(len(images > 0)):
                if (word['top'] < images[0]['top']) or ((word['top'] == images[0]['top']) and (word['left'] < images[0]['left'])):
                    font_size = round(float(word['height']))  
                    if current_fontsize != font_size:
                        current_text,current_tag,current_fontsize,text_with_tags = self.initialize_tags_and_current(current_text,current_tag,font_size,text_with_tags,sizes_dict)     
                    current_text.append(word['text'])
                else: 
                    font_size = round(float(word['height']))
                    current_text,current_tag,current_fontsize,text_with_tags = self.initialize_tags_and_current2(current_text,current_tag,font_size,text_with_tags,sizes_dict)  
                    current_text += f"<image_extracted>{self.read_text_from_image_paddle(image["data"])}<image_extracted>"
                    text_with_tags += f"<{current_tag}>"
        if(len(images) != 0 ):
            for image in images:
                current_text,current_tag,current_fontsize,text_with_tags = self.initialize_tags_and_current2(current_text,current_tag,font_size,text_with_tags,sizes_dict)
                text_with_tags = f"<image_extracted>{self.read_text_from_image_paddle(image["data"])}<image_extracted>"
                text_with_tags += f"<{current_tag}>"
        return text_with_tags,current_tag,current_text,current_fontsize 


    def get_correct_tag(self,font_size,sizes):
        """this function returns the correct tag based on the font size"""
        if font_size >= sizes['h1']:
            return "h1"
        if font_size >= sizes['h2']:
            return "h2"
        return "p"


    # def extract_page_pdf_plumber(self,page,current_tag,current_text,current_fontsize,text_with_tags,sizes_dict):
    #     """this function extracts the text of pdf and add xml with pdfpumber strategy"""
    #     for obj in page.extract_words():
    #         font_size = round(float(obj['height']))  # Redondear a entero más cercano
    #         if (current_fontsize != font_size):
    #             text_with_tags += " ".join(current_text) 
    #             text_with_tags += f"</{current_tag}>"
    #             current_text = []
    #             current_fontsize = font_size
    #             current_tag = self.get_correct_tag(current_fontsize,sizes_dict)
    #             text_with_tags += f"<{current_tag}>"
    #         current_text.append(obj['text'])


    # def extract_page_ocr(self, text_with_tags, pix, reader): 
    #     """this function extracts the text of pdf and add xml with ocr strategy"""
    #     img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    #     result = reader.readtext(img_np)
    #     text_with_tags = ""
    #     for detection in result:
    #         text_with_tags += detection[1] 
  
    def get_first_tag(self,page,sizes_dict):
            try:
                first_word = page.extract_words()[0]
                current_fontsize = round(float(first_word['height'])) 
                return self.get_correct_tag(current_fontsize,sizes_dict),current_fontsize
            except:
                return "p",10


    def extract_text_with_xml_tags(self, pdf_path):
        sizes_dict =  self.get_fontsizes(pdf_path)
        with pdfplumber.open(pdf_path) as pdf:
            current_tag,current_fontsize = self.get_first_tag(pdf.pages[0],sizes_dict)
            text_with_tags = f"<{current_tag}>"
            current_text = []
            for page in pdf.pages:
                for obj in page.extract_words():
                    font_size = round(float(obj['height']))  # Redondear a entero más cercano
                    if (current_tag != self.get_correct_tag(font_size,sizes_dict)):
                        text_with_tags += " ".join(current_text) 
                        text_with_tags += f"</{current_tag}>"
                        current_text = []
                        current_fontsize = font_size
                        current_tag = self.get_correct_tag(current_fontsize,sizes_dict)
                        text_with_tags += f"<{current_tag}>"
                    current_text.append(obj['text'])
                if(len(text_with_tags.split(" ")) > 4000):
                    return text_with_tags
            text_with_tags += " ".join(current_text)
            text_with_tags += f"</{current_tag}>"
            return text_with_tags
            
    def get_fontsizes(self,pdf_path):
        fontsizes = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
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
    start_time = time.time()
    ROOT_DIR = Path(__file__).resolve().parents[2]
    DATA_FOLDER = Path(os.getenv("DATA_FOLDER", ROOT_DIR / "data" / "sedici"))
    PDF_FOLDER = DATA_FOLDER / "pdfs3/"
    file = "10915-103423.pdf"
    filepath = PDF_FOLDER / file
    extracted_text = pdf_reader.extract_text_with_xml_tags2(filepath)
    print(extracted_text[0:1000])
    end_time = time.time()
    print("The time of execution of above program is :",
      (end_time-start_time) * 10**3, "ms")
    


