import pdfplumber
import time
import subprocess
import tempfile
import glob
import os
from PIL import Image
import numpy as np
import re



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


    def extract_text_with_xml_tags(self, pdf_path, ocr=False, max_words=None):
        """Extract text with XML tags. If max_words is set, stops after that many words (per-page boundary)."""
        sizes_dict = self.get_fontsizes(pdf_path)
        print(sizes_dict)

        ocr_reader = None
        processed_image_sizes = set()

        if ocr:
            try:
                import easyocr
                print("🔧 Initializing EasyOCR for image text extraction...")
                ocr_reader = easyocr.Reader(['en', 'es'])
            except ImportError:
                print("❌ EasyOCR not available. Install with: pip install easyocr")
                ocr = False

        with pdfplumber.open(pdf_path) as pdf:
            try:
                first_word = pdf.pages[0].extract_words()[0]
                current_fontsize = round(float(first_word['height']))
                current_tag = self.get_correct_tag(current_fontsize, sizes_dict)
            except Exception:
                current_tag = "p"
                current_fontsize = 10

            text_with_tags = f"<{current_tag}>"
            current_text = []
            words = 0

            for page_idx, page in enumerate(pdf.pages):
                page_words = page.extract_words()
                words += len(page_words)

                for obj in page_words:
                    font_size = round(float(obj['height']))
                    if current_fontsize != font_size:
                        text_with_tags += " ".join(current_text)
                        text_with_tags += f"</{current_tag}>"
                        current_text = []
                        current_fontsize = font_size
                        current_tag = self.get_correct_tag(current_fontsize, sizes_dict)
                        text_with_tags += f"<{current_tag}>"
                    current_text.append(obj['text'])

                if ocr and ocr_reader:
                    ocr_text = self._extract_ocr_from_page(
                        pdf_path, page_idx + 1, page, processed_image_sizes, ocr_reader
                    )
                    if ocr_text:
                        text_with_tags += ocr_text

                if max_words and words >= max_words:
                    text_with_tags += " ".join(current_text)
                    text_with_tags += f"</{current_tag}>"
                    return text_with_tags

            text_with_tags += " ".join(current_text)
            text_with_tags += f"</{current_tag}>"
            return text_with_tags

    def _extract_ocr_from_page(self, pdf_path, page_num, page, processed_sizes, ocr_reader):
        """
        Extract OCR text from images on a specific page
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)
            page: pdfplumber page object
            processed_sizes: Set of already processed image sizes
            ocr_reader: EasyOCR reader instance
        
        Returns:
            String with OCR text wrapped in <img> tags
        """
        try:
            # Extract images from this specific page using pdfimages
            temp_dir = tempfile.mkdtemp(prefix="ocr_page_")
            temp_prefix = os.path.join(temp_dir, "img")
            
            # Extract only from specific page
            cmd = ["pdfimages", "-f", str(page_num), "-l", str(page_num), "-png", pdf_path, temp_prefix]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"⚠️ pdfimages failed for page {page_num}: {result.stderr}")
                return ""
            
            # Get extracted image files
            image_files = glob.glob(f"{temp_prefix}-*.png")
            if not image_files:
                return ""
            
            image_files.sort()
            page_width, page_height = page.width, page.height
            ocr_texts = []
            
            for img_file in image_files:
                try:
                    with Image.open(img_file) as img:
                        img_width, img_height = img.size
                        size_key = (img_width, img_height)
                        
                        # Skip if already processed (duplicate detection)
                        if size_key in processed_sizes:
                            print(f"🔄 Skipping duplicate image {size_key}")
                            continue
                        
                        # Skip if image is similar to page size (likely full page scan)
                        if self._is_page_sized_image(img_width, img_height, page_width, page_height):
                            print(f"📄 Skipping page-sized image {size_key}")
                            continue
                        
                        # Process image with OCR
                        print(f"🔍 Processing image {size_key} with EasyOCR...")
                        img_array = np.array(img)
                        results = ocr_reader.readtext(img_array)
                        text = ' '.join([result[1] for result in results])
                        
                        if text.strip():
                            ocr_texts.append(f"<img>{text.strip()}</img>")
                            print(f"✅ Extracted: {text[:50]}...")
                        
                        # Mark this size as processed
                        processed_sizes.add(size_key)
                        
                except Exception as e:
                    print(f"❌ Error processing image {img_file}: {e}")
                    continue
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            return ''.join(ocr_texts)
            
        except Exception as e:
            print(f"❌ Error in OCR extraction for page {page_num}: {e}")
            return ""
    
    def _is_page_sized_image(self, img_width, img_height, page_width, page_height, tolerance=0.8):
        """
        Check if image is similar to page size (likely a full page scan)
        
        Args:
            img_width, img_height: Image dimensions in pixels
            page_width, page_height: Page dimensions in points
            tolerance: Similarity threshold (0.8 = 80% similar)
        
        Returns:
            Boolean indicating if image is page-sized
        """
        # Convert page dimensions to approximate pixel size (assuming ~150 DPI)
        page_width_px = page_width * 150 / 72  # Convert points to pixels
        page_height_px = page_height * 150 / 72
        
        # Check if image is similar to page size
        width_ratio = min(img_width / page_width_px, page_width_px / img_width)
        height_ratio = min(img_height / page_height_px, page_height_px / img_height)
        
        return width_ratio >= tolerance and height_ratio >= tolerance
            
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


    # def extract_text(self, pdf_path: str, ocr: bool = False) -> str:
    #     """
    #     Extract plain text from PDF and optionally OCR from images

    #     Args:
    #         pdf_path: Path to PDF file
    #         ocr: Boolean flag to enable/disable OCR processing
    #     """
    #     print("Extracting text from PDF...")

    #     # Initialize OCR if enabled
    #     ocr_reader = None
    #     processed_image_sizes = set()

    #     if ocr:
    #         try:
    #             import easyocr
    #             print("🔧 Initializing EasyOCR for image text extraction...")
    #             ocr_reader = easyocr.Reader(['en', 'es'])
    #         except ImportError:
    #             print("❌ EasyOCR not available. Install with: pip install easyocr")
    #             ocr = False

    #     with pdfplumber.open(pdf_path) as pdf:
    #         lines = []
    #         for page_idx, page in enumerate(pdf.pages):
    #             # Try column detection first, fall back to normal extraction
    #             text = self._detect_column_layout(page)
    #             if text is None:
    #                 text = page.extract_text()
    #             if text:
    #                 lines.append(text.strip())

    #             # Extract OCR text from images if enabled
    #             if ocr and ocr_reader:
    #                 ocr_text = self._extract_ocr_from_page(
    #                     pdf_path, page_idx + 1, page, processed_image_sizes, ocr_reader
    #                 )
    #                 if ocr_text:
    #                     # Remove tags for plain text output
    #                     ocr_plain = ocr_text.replace('<img>', '').replace('</img>', '')
    #                     lines.append(ocr_plain.strip())

    #         return "\n\n".join(lines) 


    def _process_page_plain(self, page, ocr_reader=None):
        """
        Extract plain text from one page, optionally with OCR.
        Returns (chunks, word_count) where chunks is a list of text strings.
        """
        chunks = []
        text = page.extract_text()
        word_count = len(text.split()) if text else 0
        if text:
            chunks.append(text.strip())

        if ocr_reader:
            try:
                page_image = page.to_image(resolution=300).original
                results = ocr_reader.readtext(page_image, detail=0)
                ocr_text = "\n".join(results)
                if ocr_text.strip():
                    chunks.append(ocr_text.strip())
            except Exception as e:
                print(f"OCR failed on page: {e}")

        return chunks, word_count

    def extract_text(self, pdf_path: str, ocr: bool = False, max_words: int = None) -> str:
        """Extract plain text. If max_words is set, stops after that many words (per-page boundary)."""
        print("Extracting text from PDF...")

        ocr_reader = None
        if ocr:
            try:
                import easyocr
                print("🔧 Initializing EasyOCR...")
                ocr_reader = easyocr.Reader(['en', 'es'])
            except ImportError:
                print("❌ EasyOCR not installed. Run: pip install easyocr")

        with pdfplumber.open(pdf_path) as pdf:
            all_chunks = []
            total_words = 0
            for page in pdf.pages:
                chunks, page_word_count = self._process_page_plain(page, ocr_reader)
                all_chunks.extend(chunks)
                total_words += page_word_count
                if max_words and total_words >= max_words:
                    break

        return "\n\n".join(all_chunks)


if __name__ == '__main__':
    pdf_reader = PdfReader()
    from pathlib import Path
    import os
    import time
    ROOT_DIR = Path(__file__).resolve().parents[2]
    DATA_FOLDER = Path(ROOT_DIR / "data" / "sedici")
    PDF_FOLDER = DATA_FOLDER / "pdfs/"
    file = "10915-20286.pdf"  # Use the test PDF
    filepath = PDF_FOLDER / file
    
    print("🔍 TESTING PDF READER WITH OCR")
    print("=" * 50)
    
    # Test without OCR
    print("\n📄 Testing WITHOUT OCR...")
    start_time = time.time()
    extracted_text_no_ocr = pdf_reader.extract_text_with_xml_tags(filepath, ocr=False)
    end_time = time.time()
    no_ocr_time = (end_time - start_time) * 1000
    print(f"⏱️ Time without OCR: {no_ocr_time:.2f}ms")
    print(f"📝 Characters extracted: {len(extracted_text_no_ocr)}")
    
    print(extracted_text_no_ocr)
    

 
    # # Test with OCR
    # print("\n📷 Testing WITH OCR...")
    # start_time = time.time()
    # extracted_text_with_ocr = pdf_reader.extract_text_with_xml_tags(filepath, ocr=True)
    # end_time = time.time()
    # with_ocr_time = (end_time - start_time) * 1000
    # print(f"⏱️ Time with OCR: {with_ocr_time:.2f}ms")
    # print(f"📝 Characters extracted: {len(extracted_text_with_ocr)}")
    
    # # Show OCR additions
    # if "<img>" in extracted_text_with_ocr:
    #     ocr_count = extracted_text_with_ocr.count("<img>")
    #     print(f"🖼️ OCR extractions found: {ocr_count}")
        
    #     # Show first OCR extraction as example
    #     img_start = extracted_text_with_ocr.find('<img>')
    #     if img_start != -1:
    #         img_end = extracted_text_with_ocr.find('</img>', img_start) + 6
    #         sample_ocr = extracted_text_with_ocr[img_start:img_end]
    #         print(f"📝 Sample OCR: {sample_ocr}")
    # else:
    #     print("🖼️ No OCR extractions found")
    
    # print(f"\n📊 OCR Processing added: {with_ocr_time - no_ocr_time:.2f}ms")
    # print(f"📊 Character increase: +{len(extracted_text_with_ocr) - len(extracted_text_no_ocr)}")
    
    # # Uncomment to see full extracted text
    # # print("\n" + "="*50)
    # # print("EXTRACTED TEXT WITH OCR:")
    # # print("="*50) 
    # # print(extracted_text_with_ocr)



