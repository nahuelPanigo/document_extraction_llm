import pdfplumber
import numpy as np

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


    def extract_page_pdf_plumber(self,page,current_tag,current_text,current_fontsize,text_with_tags,sizes_dict):
        """this function extracts the text of pdf and add xml with pdfpumber strategy"""
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


    def extract_page_ocr(self, text_with_tags, pix, reader): 
        """this function extracts the text of pdf and add xml with ocr strategy"""
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        result = reader.readtext(img_np)
        text_with_tags = ""
        for detection in result:
            text_with_tags += detection[1] 
  

    # def extract_text_with_xml_tags2(self, pdf_path):
    #     """this function extracts the text of pdf and add xml 
    #     tags the tags are based on the font size of the text"""
    #     sizes_dict =  self.get_fontsizes(pdf_path)
    #     reader = easyocr.Reader(['es'])
    #     pdf_document = fitz.open(pdf_path)
    #     with pdfplumber.open(pdf_path) as pdf:
    #         try:
    #             first_word = pdf.pages[0].extract_words()[0]
    #             current_fontsize = round(float(first_word['height'])) 
    #             current_tag = self.get_correct_tag(current_fontsize,sizes_dict)
    #         except:
    #             current_tag = "p"
    #             current_fontsize = 10     
    #         text_with_tags = f"<{current_tag}>"
    #         current_text = []
    #         for page in pdf.pages:
    #             extracted_text = page.extract_text()
    #             if extracted_text:
    #                 self.extract_page_pdf_plumber(page,current_tag,current_text,current_fontsize,text_with_tags,sizes_dict)
    #             else:
    #                 print(f"entro en la pagina {page.page_number}")
    #                 pixmap = page.get_textmap()
    #                 self.extract_page_ocr(text_with_tags,pixmap,reader)
    #         text_with_tags += " ".join(current_text)
    #         text_with_tags += f"</{current_tag}>"
    #               # Cleanup
    #         pdf_document.close()
    #         return text_with_tags

    def extract_text_with_xml_tags(self, pdf_path):
        sizes_dict =  self.get_fontsizes(pdf_path)
        print(sizes_dict)
        with pdfplumber.open(pdf_path) as pdf:
            first_word = pdf.pages[0].extract_words()[0]
            try:
                current_fontsize = round(float(first_word['height'])) 
                current_tag = self.get_correct_tag(current_fontsize,sizes_dict)
            except:
                current_tag = "p"    
            text_with_tags = f"<{current_tag}>"
            current_text = []
            for page in pdf.pages:
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
                if(len(text_with_tags.split(" ")) > 4000):
                    return text_with_tags
            text_with_tags += " ".join(current_text)
            text_with_tags += f"</{current_tag}>"
            return text_with_tags
            
    def get_fontsizes(self,pdf_path):
        fontsizes = []
        count = 0
        with pdfplumber.open(pdf_path) as pdf:
            print(pdf.metadata)
            for page in pdf.pages:
                count +=1
                if(count == 3):
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

