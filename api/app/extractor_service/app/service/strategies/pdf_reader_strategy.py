import pdfplumber
from app.service.strategies.reader_strategy import ReaderStrategy


class PdfReader(ReaderStrategy):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PdfReader, cls).__new__(cls)
        return cls.instance
        

    def get_correct_tag(self,font_size: int,sizes: dict) -> str:
        """this function returns the correct tag based on the font size"""
        if font_size >= sizes['h1']:
            return "h1"
        if font_size >= sizes['h2']:
            return "h2"
        return "p"
    

    def get_fontsizes(self,pdf_path: str) -> dict:
        fontsizes = []
        count = 0
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                count+=1
                if count > 3:
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


    def extract_text_with_xml_tags(self, pdf_path: str) -> str:
        sizes_dict =  self.get_fontsizes(pdf_path)
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
                if(len(text_with_tags.split(" ")) > 2000):
                    return text_with_tags
            text_with_tags += " ".join(current_text)
            text_with_tags += f"</{current_tag}>"
            return text_with_tags
            


    def extract_text(self, pdf_path: str) -> str:
        with pdfplumber.open(pdf_path) as pdf:
            lines = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.append(text.strip())
            return "\n\n".join(lines) 

