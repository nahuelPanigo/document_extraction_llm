from docx import Document


class WordReader:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(WordReader, cls).__new__(cls)
        return cls.instance
    
    def extract_text_with_xml_tags(self,file_path):
        if file_path.endswith(".docx"):
            doc = Document(file_path)
            text_with_tags = ""
            for paragraph in doc.paragraphs:
                size = paragraph.style.font.size
                if size is not None and size.pt > 16:
                    tag = "h1"
                elif size is not None and size.pt > 12:
                    tag = "h2"
                else:
                    tag = None
                if tag:
                    text_with_tags += f"<{tag}>{paragraph.text}</{tag}> "
                else:
                    text_with_tags += paragraph.text
            return text_with_tags