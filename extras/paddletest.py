import os
import subprocess
import tempfile
from paddleocr import PaddleOCR
from PIL import Image

def extract_images_with_pdfimages(pdf_path: str):
    """
    Extract images from a PDF using `pdfimages -png`.
    Returns a list of filepaths to the extracted PNG images.
    """
    print(f"📄 Processing PDF: {pdf_path}")
    
    temp_dir = tempfile.mkdtemp(prefix="pdfimgs_")
    temp_prefix = os.path.join(temp_dir, "img")

    cmd = ["pdfimages", "-png", pdf_path, temp_prefix]
    print(f"🔧 Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"pdfimages error:\n{result.stderr}")

    images = [
        os.path.join(temp_dir, f)
        for f in os.listdir(temp_dir)
        if f.endswith(".png")
    ]

    images.sort()
    print(f"📷 Found {len(images)} images:")
    
    # Show image info with dimensions
    for i, img_path in enumerate(images, 1):
        try:
            with Image.open(img_path) as img:
                print(f"   {i}. {os.path.basename(img_path)} - {img.size[0]}x{img.size[1]} pixels")
        except Exception as e:
            print(f"   {i}. {os.path.basename(img_path)} - Error reading: {e}")
    
    return images, temp_dir


def ocr_images_with_paddle(images: list):
    print(f"\n🔍 Starting OCR processing with PaddleOCR...")
    ocr = PaddleOCR(lang="es")

    all_text = ""
    
    for i, img_path in enumerate(images, 1):
        print(f"\n📷 Processing image {i}/{len(images)}: {os.path.basename(img_path)}")
        
        try:
            # Show image dimensions
            with Image.open(img_path) as img:
                print(f"   📏 Size: {img.size[0]}x{img.size[1]} pixels, Mode: {img.mode}")
        except Exception as e:
            print(f"   ❌ Error reading image info: {e}")
            continue
        
        try:
            result = ocr.predict(img_path)
            print(f"   🔍 OCR result type: {type(result)}")

            # Parse result
            if result and result[0]:
                data = result[0]
                print(f"   🔍 Data type: {type(data)}")
                
                if isinstance(data, dict) and "rec_texts" in data:
                    texts = data["rec_texts"]
                    scores = data["rec_scores"]
                    
                    if texts:
                        print(f"   ✅ Found {len(texts)} text blocks:")
                        for j, (text, score) in enumerate(zip(texts, scores), 1):
                            print(f"      {j}. \"{text}\" (confidence: {score:.3f})")
                            all_text += text + "\n"
                    else:
                        print(f"   ❌ No text found in image")
                else:
                    print(f"   ❌ Unexpected data structure: {data}")
            else:
                print(f"   ❌ No OCR results returned")
                
        except Exception as e:
            print(f"   ❌ OCR error: {e}")
            import traceback
            traceback.print_exc()

    return all_text


if __name__ == "__main__":
    # Use the CORRECT PDF you specified
    pdf_path = "/home/nahuel/Documents/tesis/data/sedici/pdfs/10915-117661.pdf"

    print("🚀 ENHANCED PADDLEOCR TEST")
    print("=" * 50)
    
    # Check if PDF exists
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        
        # Show available PDFs
        pdf_dir = "/home/nahuel/Documents/tesis/data/sedici/pdfs"
        if os.path.exists(pdf_dir):
            available_pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
            print(f"📁 Available PDFs: {available_pdfs[:10]}")
        exit(1)

    try:
        print("📷 Extracting images...")
        images, temp_dir = extract_images_with_pdfimages(pdf_path)

        if images:
            print(f"\n🎯 Processing {len(images)} images with PaddleOCR...")
            text = ocr_images_with_paddle(images)
            
            print(f"\n{'='*50}")
            print("📄 FINAL EXTRACTED TEXT")
            print(f"{'='*50}")
            if text.strip():
                print(text)
                print(f"\n📊 Total characters extracted: {len(text)}")
            else:
                print("❌ No text was extracted from any images")
        else:
            print("❌ No images found in the PDF.")
            
        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temp directory: {temp_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
