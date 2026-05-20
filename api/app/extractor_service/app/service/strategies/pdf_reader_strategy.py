import pdfplumber
from app.service.strategies.reader_strategy import ReaderStrategy
from app.service.utils.multicolumn import detect_page_columns

import subprocess
import tempfile
import glob
import os
from PIL import Image
import numpy as np
from collections import defaultdict
from typing import Tuple



class PdfReader(ReaderStrategy):
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


    def extract_text_with_xml_tags(self, pdf_path, ocr=True, max_words=None):
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


    @staticmethod
    def _is_full_width_line(words: list, page, split_xs: list) -> bool:
        if not split_xs or len(words) < 2:
            return False
        min_x = min(w["x0"] for w in words)
        max_x = max(w["x1"] for w in words)
        if not any(min_x < sx < max_x for sx in split_xs):
            return False
        sorted_words = sorted(words, key=lambda w: w["x0"])
        gap_threshold = max(20.0, page.width * 0.035)
        for left, right in zip(sorted_words, sorted_words[1:]):
            gap = right["x0"] - left["x1"]
            if gap >= gap_threshold and any(left["x1"] <= sx <= right["x0"] for sx in split_xs):
                return False
        return True

    def _extract_words_column_ordered(self, page, split_x, n_cols: int, strip_footers: bool = False) -> str:
        words = page.extract_words()
        if not words:
            return page.extract_text() or ""

        if strip_footers:
            words = [w for w in words if w["bottom"] < page.height * 0.94]

        if not words:
            return ""

        if not split_x:
            split_xs = [page.width * i / n_cols for i in range(1, n_cols)]
        else:
            split_xs = [split_x] if n_cols == 2 else [page.width * i / n_cols for i in range(1, n_cols)]

        boundaries = [0.0] + split_xs + [float(page.width)]

        line_map: dict[int, list] = defaultdict(list)
        for w in words:
            y_key = round(w["top"] / 2) * 2
            line_map[y_key].append(w)

        col_lines: list[list[str]] = [[] for _ in range(n_cols)]

        for y_key in sorted(line_map):
            line_words = sorted(line_map[y_key], key=lambda w: w["x0"])
            line_text = " ".join(w["text"] for w in line_words)

            if self._is_full_width_line(line_words, page, split_xs):
                col_lines[0].append(line_text)
                continue

            col_word_groups: list[list[str]] = [[] for _ in range(n_cols)]
            for w in line_words:
                x_center = (w["x0"] + w["x1"]) / 2
                col_idx = n_cols - 1
                for i in range(n_cols):
                    if boundaries[i] <= x_center < boundaries[i + 1]:
                        col_idx = i
                        break
                col_word_groups[col_idx].append(w["text"])

            for i, group in enumerate(col_word_groups):
                if group:
                    col_lines[i].append(" ".join(group))

        parts = ["\n".join(lines) for lines in col_lines if lines]
        return "\n\n".join(parts)

    def _process_page_column_aware(self, page, page_det: dict, strip_footers: bool = False) -> Tuple[list, int]:
        n_cols = page_det["columns"]
        split_x = page_det["method_b"].get("split_x")

        if n_cols > 1:
            text = self._extract_words_column_ordered(page, split_x, n_cols, strip_footers)
        else:
            if strip_footers:
                words = [w for w in page.extract_words() if w["bottom"] < page.height * 0.94]
                line_map: dict[int, list] = defaultdict(list)
                for w in words:
                    y_key = round(w["top"] / 2) * 2
                    line_map[y_key].append(w)
                lines = []
                for y_key in sorted(line_map):
                    lw = sorted(line_map[y_key], key=lambda w: w["x0"])
                    lines.append(" ".join(w["text"] for w in lw))
                text = "\n".join(lines)
            else:
                text = page.extract_text() or ""

        word_count = len(text.split()) if text else 0
        return ([text.strip()] if text.strip() else []), word_count

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

    def extract_text(self, pdf_path: str, ocr: bool = False, max_words: int = None,
                     multicolumn: bool = False, strip_footers: bool = False) -> Tuple[str, bool]:
        """Extract plain text. Returns (text, is_multicolumn).

        multicolumn=True: reorder words column-by-column per page (left col first, then right).
        strip_footers=True: skip text in the bottom 6% of each page.
        is_multicolumn is computed from per-page detection on the first 5 content pages.
        """
        print("Extracting text from PDF...")
        ocr_reader = None
        if ocr and not multicolumn:
            try:
                import easyocr
                print("🔧 Initializing EasyOCR...")
                ocr_reader = easyocr.Reader(['en', 'es'])
            except ImportError:
                print("❌ EasyOCR not available. Install with: pip install easyocr")

        all_chunks = []
        total_words = 0
        multi_page_votes: list[bool] = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_det = None

                # Always detect on first 5 pages to build the is_multicolumn vote.
                if page_idx < 5:
                    page_det = detect_page_columns(page)
                    page_word_count = len(page.extract_words())
                    if page_word_count >= 25:
                        multi_page_votes.append(page_det["columns"] > 1)

                if multicolumn:
                    # For pages beyond the first 5 we still need per-page detection
                    # to decide whether that individual page is multi-column.
                    if page_det is None:
                        page_det = detect_page_columns(page)
                    chunks, wc = self._process_page_column_aware(page, page_det, strip_footers)
                else:
                    chunks, wc = self._process_page_plain(page, ocr_reader)

                all_chunks.extend(chunks)
                total_words += wc
                if max_words and total_words >= max_words:
                    break

        n = len(multi_page_votes)
        multi_count = sum(multi_page_votes)
        if n == 0:
            is_multicolumn = False
        elif n <= 2:
            is_multicolumn = multi_count >= 1
        else:
            is_multicolumn = (multi_count / n) > 0.60

        return "\n\n".join(all_chunks), is_multicolumn

