import pdfplumber
from transformers import AutoProcessor, AutoModelForCausalLM
from constant import DATA_FOLDER

PDF_FOLDER = DATA_FOLDER / "pdfs2/"

# Cargar el procesador y modelo de MOLMO
processor = AutoProcessor.from_pretrained(
    'allenai/MolmoE-1B-0924',
    trust_remote_code=True,
    torch_dtype='auto',
    device_map='auto'
)

model = AutoModelForCausalLM.from_pretrained(
    'allenai/MolmoE-1B-0924',
    trust_remote_code=True,
    torch_dtype='auto'
)

# Función para convertir página del PDF a imagen y luego extraer el texto usando MOLMO
def pdf_page_to_text_molmo(pdf_path, page_num):
    # Abrir el archivo PDF con pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        # Seleccionar la página deseada
        page = pdf.pages[page_num]
        
        # Convertir la página a una imagen
        page_image = page.to_image(resolution=300)  # Puedes ajustar la resolución según sea necesario
        pil_image = page_image.original  # Obtener la imagen PIL directamente
        
        # Preprocesar la imagen usando el procesador de MOLMO
        pixel_values = processor(pil_image, return_tensors="pt").pixel_values
        
        # Mover la imagen al dispositivo adecuado (CPU/GPU)
        pixel_values = pixel_values.to(model.device)
        
        # Generar el texto con MOLMO
        generated_ids = model.generate(pixel_values)
        
        # Decodificar el texto generado
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return generated_text

# Ejemplo de uso
pdf_path = PDF_FOLDER / "10915-168489.pdf"
page_number = 0  # Índice de la página que deseas procesar
texto_generado = pdf_page_to_text_molmo(pdf_path, page_number)

print(f"Texto extraído de la página {page_number + 1}:", texto_generado)
