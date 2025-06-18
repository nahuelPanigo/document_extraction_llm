from docx import Document
from app.service.strategies.reader_strategy import ReaderStrategy


class DocxReader(ReaderStrategy):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DocxReader, cls).__new__(cls)
        return cls.instance

    def get_correct_tag(self, font_size: int, sizes: dict) -> str:
        if font_size >= sizes['h1']:
            return "h1"
        if font_size >= sizes['h2']:
            return "h2"
        return "p"

    def get_fontsizes(self, docx_path: str) -> dict:
        doc = Document(docx_path)
        sizes = []
        for para in doc.paragraphs[:100]:  # limitar a los primeros 100 párrafos
            for run in para.runs:
                if run.font.size:
                    pt_size = run.font.size.pt  # convertir a puntos
                    if pt_size < 40:
                        sizes.append(round(pt_size))

        sizes = sorted(set(sizes))
        if not sizes:
            return {'h1': 16, 'h2': 14, 'p': 9}  # defaults si no hay tamaños

        h1_size = sizes[-1]
        n = len(sizes)
        h2_size = sizes[int(n * 0.75)] if n > 1 else sizes[0]
        paragraph_sizes = [size for size in sizes if size < h2_size]
        return {
            'h1': h1_size,
            'h2': h2_size,
            'p': min(paragraph_sizes) if paragraph_sizes else sizes[0]
        }


    def extract_text_with_xml_tags(self, docx_path:str) -> str:
        sizes_dict = self.get_fontsizes(docx_path)
        doc = Document(docx_path)

        text_with_tags = ""
        current_tag = "p"
        current_text = []

        for para in doc.paragraphs:
            para_text = ""
            max_font_size = 0
            for run in para.runs:
                if run.font.size:
                    font_size = round(run.font.size.pt)
                    max_font_size = max(max_font_size, font_size)
                para_text += run.text

            if para_text.strip():
                tag = self.get_correct_tag(max_font_size, sizes_dict)
                if current_tag != tag:
                    if current_text:
                        text_with_tags += f"<{current_tag}>" + " ".join(current_text) + f"</{current_tag}>"
                    current_text = [para_text.strip()]
                    current_tag = tag
                else:
                    current_text.append(para_text.strip())

                if len(text_with_tags.split(" ")) > 2000:
                    break

        if current_text:
            text_with_tags += f"<{current_tag}>" + " ".join(current_text) + f"</{current_tag}>"

        return text_with_tags
    
    def extract_text(self, docx_path: str) -> str:
        doc = Document(docx_path)
        lines = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
        return "\n".join(lines)
