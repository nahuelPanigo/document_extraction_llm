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


    def extract_text_with_xml_tags(self, pdf_path, ocr=False):
        """
        Extract text with XML tags and optionally OCR from images
        
        Args:
            pdf_path: Path to PDF file
            ocr: Boolean flag to enable/disable OCR processing
        """
        sizes_dict = self.get_fontsizes(pdf_path)
        print(sizes_dict)
        
        # Initialize OCR if enabled
        ocr_reader = None
        processed_image_sizes = set()  # Track processed image sizes to avoid duplicates
        
        if ocr:
            try:
                import easyocr
                print("🔧 Initializing EasyOCR for image text extraction...")
                ocr_reader = easyocr.Reader(['en', 'es'])
            except ImportError:
                print("❌ EasyOCR not available. Install with: pip install easyocr")
                ocr = False
        
        with pdfplumber.open(pdf_path) as pdf:
            # Get initial tag and font size
            try:
                first_word = pdf.pages[0].extract_words()[0]
                current_fontsize = round(float(first_word['height'])) 
                current_tag = self.get_correct_tag(current_fontsize, sizes_dict)
            except:
                current_tag = "p"    
                current_fontsize = 10
                
            text_with_tags = f"<{current_tag}>"
            current_text = []
            words = 0
            
            # Process each page
            for page_idx, page in enumerate(pdf.pages):
                page_words = page.extract_words()
                words += len(page_words)
                
                # Extract text with tags (existing logic)
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
                
                # OCR processing at end of each page
                if ocr and ocr_reader:
                    ocr_text = self._extract_ocr_from_page(
                        pdf_path, page_idx + 1, page, processed_image_sizes, ocr_reader
                    )
                    if ocr_text:
                        text_with_tags += ocr_text
                
                # Check word limit
                if words > 4000:
                    text_with_tags += " ".join(current_text) 
                    text_with_tags += f"</{current_tag}>"
                    return text_with_tags
            
            # Close final tag
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
            
    def _detect_column_layout(self, page):
        """
        Detect if a page has a 2-column layout and extract accordingly.
        Returns column-extracted text if columns detected, None otherwise.
        """
        words = page.extract_words()
        if not words:
            return None

        page_width = page.width
        gap_threshold = page_width * 0.15

        # Group words by row
        rows = {}
        for word in words:
            row_key = round(word['top'] / 5) * 5
            if row_key not in rows:
                rows[row_key] = []
            rows[row_key].append(word)

        total_rows = len(rows)
        if total_rows < 4:
            return None

        # Count how many rows have a large horizontal gap (column separator)
        rows_with_gap = 0
        for row_key in rows:
            row_words = sorted(rows[row_key], key=lambda w: w['x0'])
            for i in range(1, len(row_words)):
                gap = row_words[i]['x0'] - row_words[i - 1]['x1']
                if gap > gap_threshold:
                    rows_with_gap += 1
                    break

        # Need >50% of rows with gaps to consider it a column layout
        if rows_with_gap <= total_rows * 0.5:
            return None

        # It's a 2-column layout - split words by midpoint
        mid_point = page_width / 2
        left_words = [w for w in words if (w['x0'] + w['x1']) / 2 < mid_point]
        right_words = [w for w in words if (w['x0'] + w['x1']) / 2 >= mid_point]

        def words_to_text(col_words):
            col_rows = {}
            for word in col_words:
                row_key = round(word['top'] / 5) * 5
                if row_key not in col_rows:
                    col_rows[row_key] = []
                col_rows[row_key].append(word)
            lines = []
            for rk in sorted(col_rows.keys()):
                rw = sorted(col_rows[rk], key=lambda w: w['x0'])
                line = ' '.join(w['text'] for w in rw)
                if line.strip():
                    lines.append(line)
            return '\n'.join(lines)

        left_text = words_to_text(left_words)
        right_text = words_to_text(right_words)

        return f"{left_text}\n\n{right_text}"

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


    def extract_text(self, pdf_path: str, ocr: bool = False) -> str:
        """
        Extract plain text from PDF.
        Optionally apply OCR to full pages.

        Args:
            pdf_path: Path to PDF file
            ocr: Enable OCR (default: False)
        """
        print("Extracting text from PDF...")

        text_chunks = []

        # Optional OCR initialization
        ocr_reader = None
        if ocr:
            try:
                import easyocr
                print("🔧 Initializing EasyOCR...")
                ocr_reader = easyocr.Reader(['en', 'es'])
            except ImportError:
                print("❌ EasyOCR not installed. Run: pip install easyocr")
                ocr = False

        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:

                # 1️⃣ Extract normal text
                text = page.extract_text()
                if text:
                    text_chunks.append(text.strip())

                # 2️⃣ Optional OCR on full page image
                if ocr and ocr_reader:
                    try:
                        page_image = page.to_image(resolution=300).original
                        results = ocr_reader.readtext(page_image, detail=0)
                        ocr_text = "\n".join(results)
                        if ocr_text.strip():
                            text_chunks.append(ocr_text.strip())
                    except Exception as e:
                        print(f"OCR failed on page: {e}")

        return "\n\n".join(text_chunks)


if __name__ == '__main__':
    pdf_reader = PdfReader()
    from pathlib import Path
    import os
    import time
    ROOT_DIR = Path(__file__).resolve().parents[2]
    DATA_FOLDER = Path(ROOT_DIR / "data" / "sedici")
    PDF_FOLDER = DATA_FOLDER / "pdfs/"
    file = "10915-95206.pdf"  # Use the test PDF
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
    
    #print(extracted_text_no_ocr)
    

    import re

    pattern = r'\(cid:\d+\)'
    matches = re.findall(r'\(cid:(\d+)\)', extracted_text_no_ocr)
    print("CID numbers found:", sorted([int(x)for x in set(matches)]))
    
    # Test PyMuPDF extraction
    print("\n🔬 Testing PyMuPDF extraction...")
    try:
        import fitz
        doc = fitz.open(str(filepath))
        pymupdf_text = ""
        for page_num in range(min(3, len(doc))):  # Test first 3 pages
            page = doc.load_page(page_num)
            pymupdf_text += page.get_text()
        doc.close()
        
        print(f"📝 PyMuPDF extracted {len(pymupdf_text)} characters")
        print("First 200 chars:", repr(pymupdf_text[:200]))
        
        # Check if PyMuPDF has CIDs too
        pymupdf_cids = re.findall(r'\(cid:(\d+)\)', pymupdf_text)
        if pymupdf_cids:
            print("❌ PyMuPDF also has CID issues")
        else:
            print("✅ PyMuPDF extraction looks clean!")
            
    except ImportError:
        print("❌ PyMuPDF not available")
    except Exception as e:
        print(f"❌ PyMuPDF failed: {e}")

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



