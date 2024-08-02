import pdfplumber

class PdfReader:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PdfReader, cls).__new__(cls)
        return cls.instance

    def extract_text_with_xml_tags(self,pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            text_with_tags = ""
            prev_style = None
            tag = None  # Inicializamos 'tag' aquí para asegurarnos de que siempre tenga un valor asignado
            count = 1
            for page in pdf.pages:
                for obj in page.extract_words():
                    fontname = obj.get('fontname', '')  # Obtener el valor de 'fontname' o usar una cadena vacía si no está presente
                    if prev_style is None or (obj['height'] == prev_style['height'] and fontname == prev_style['fontname']):
                        text_with_tags += obj['text'] + " "
                    else:
                        # Si el estilo cambia, cerramos la etiqueta anterior y abrimos una nueva si es necesario
                        if prev_style is not None and prev_style['tag'] is not None:  # Comprobamos si prev_style['tag'] no es None
                            text_with_tags += f"</{prev_style['tag']}> "
                        if obj['height'] > 14:
                            tag = "h1"
                        elif obj['height'] > 12:
                            tag = "h2"
                        else:
                            tag = None  # No necesitamos etiquetas <p>
                        if tag:
                            text_with_tags += f"<{tag}>"
                        text_with_tags += f"{obj['text']} "
                    prev_style = {'height': obj['height'], 'fontname': fontname, 'tag': tag}
                if prev_style is not None and prev_style['tag'] is not None:  # Comprobamos si prev_style['tag'] no es None
                    text_with_tags += f"</{prev_style['tag']}> "  # Cerrar la última etiqueta al final de la página
                if count == 1:
                    #obtenemos solo la primera pagina
                    break
            return text_with_tags
