import sys
from pathlib import Path
import time
import re

# Add parent directory to path to import constants
sys.path.append(str(Path(__file__).parent.parent))
from constants import PDF_FOLDER

# Import libraries
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("❌ pdfplumber not available")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("❌ PyMuPDF not available")

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    from pdfminer.layout import LAParams
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False
    print("❌ pdfminer not available")

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("❌ pypdf not available")

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("❌ EasyOCR not available")

class ExtractionStrategy:
    """Base class for extraction strategies"""
    
    def __init__(self, name):
        self.name = name
    
    def extract_text(self, pdf_path):
        """Extract text from PDF - to be implemented by subclasses"""
        raise NotImplementedError
    
    def clean_cid_artifacts(self, text):
        """DON'T clean anything - show raw extraction"""
        return text
    
    def analyze_corruption(self, text):
        """Analyze what type of corruption we have"""
        if not text:
            return "empty"
        
        # Count different types of issues
        cid_count = len(re.findall(r'\(cid:\d+\)', text))
        control_count = sum(1 for c in text if 1 <= ord(c) <= 31 and c not in '\t\n\r')
        
        # Check for repeated patterns (like /g3/g3/g3)
        repeated_patterns = len(re.findall(r'(/\w+)+', text))
        
        # Check for unicode escape sequences
        unicode_escapes = len(re.findall(r'\\u[0-9a-fA-F]{4}', text))
        
        corruption_type = []
        if cid_count > 50:
            corruption_type.append(f"CID({cid_count})")
        if control_count > 100:
            corruption_type.append(f"Control({control_count})")
        if repeated_patterns > 100:
            corruption_type.append(f"Repeated({repeated_patterns})")
        if unicode_escapes > 10:
            corruption_type.append(f"Unicode({unicode_escapes})")
        
        return " + ".join(corruption_type) if corruption_type else "clean"

class PdfPlumberStrategy(ExtractionStrategy):
    """pdfplumber extraction with tag detection"""
    
    def __init__(self):
        super().__init__("PDFPlumber")
    
    def extract_text(self, pdf_path):
        if not PDFPLUMBER_AVAILABLE:
            return "❌ pdfplumber not available"
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Try to get font sizes for tagging
                sizes_dict = self._get_font_sizes(pdf)
                
                if sizes_dict:
                    return self._extract_with_tags(pdf, sizes_dict)
                else:
                    # Fallback to simple extraction
                    return self._extract_simple(pdf)
                    
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _get_font_sizes(self, pdf):
        """Get font sizes for tag detection"""
        try:
            fontsizes = []
            for i, page in enumerate(pdf.pages[:3]):  # First 3 pages
                for word in page.extract_words():
                    size = round(float(word.get("height", 0)))
                    if size > 0 and size < 40 and size not in fontsizes:
                        fontsizes.append(size)
            
            if len(fontsizes) >= 2:
                fontsizes.sort()
                h1_size = fontsizes[-1]
                h2_size = fontsizes[int(len(fontsizes) * 0.75)] if len(fontsizes) > 1 else fontsizes[0]
                return {'h1': h1_size, 'h2': h2_size, 'p': min(fontsizes)}
            
        except Exception:
            pass
        
        return None
    
    def _extract_with_tags(self, pdf, sizes_dict):
        """Extract text with HTML-like tags"""
        try:
            # Get initial tag
            first_word = pdf.pages[0].extract_words()[0]
            current_fontsize = round(float(first_word['height']))
            current_tag = self._get_correct_tag(current_fontsize, sizes_dict)
            
            text_with_tags = f"<{current_tag}>"
            current_text = []
            
            for page in pdf.pages:
                for word in page.extract_words():
                    font_size = round(float(word['height']))
                    if current_fontsize != font_size:
                        text_with_tags += " ".join(current_text)
                        text_with_tags += f"</{current_tag}>"
                        current_text = []
                        current_fontsize = font_size
                        current_tag = self._get_correct_tag(current_fontsize, sizes_dict)
                        text_with_tags += f"<{current_tag}>"
                    current_text.append(word['text'])
            
            # Close final tag
            text_with_tags += " ".join(current_text)
            text_with_tags += f"</{current_tag}>"
            
            return self.clean_cid_artifacts(text_with_tags)
            
        except Exception as e:
            return f"❌ Tag extraction failed: {e}"
    
    def _extract_simple(self, pdf):
        """Simple text extraction wrapped in <p> tags"""
        try:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            # Wrap in paragraph tags
            full_text = f"<p>{full_text}</p>"
            return self.clean_cid_artifacts(full_text)
            
        except Exception as e:
            return f"❌ Simple extraction failed: {e}"
    
    def _get_correct_tag(self, font_size, sizes):
        """Determine tag based on font size"""
        if font_size >= sizes['h1']:
            return "h1"
        if font_size >= sizes['h2']:
            return "h2"
        return "p"

class PyMuPDFStrategy(ExtractionStrategy):
    """PyMuPDF extraction strategy with advanced font handling"""
    
    def __init__(self):
        super().__init__("PyMuPDF")
    
    def extract_text(self, pdf_path):
        if not PYMUPDF_AVAILABLE:
            return "❌ PyMuPDF not available"
        
        try:
            doc = fitz.open(str(pdf_path))
            
            # Try different extraction methods
            methods = [
                ("Standard", self._extract_standard),
                ("HTML Mode", self._extract_html),
                ("XHTML Mode", self._extract_xhtml),
                ("Dict Mode", self._extract_dict_mode),
                ("Rawdict Mode", self._extract_rawdict),
            ]
            
            results = {}
            
            for method_name, method_func in methods:
                try:
                    result = method_func(doc)
                    corruption = self.analyze_corruption(result)
                    results[method_name] = {
                        'text': result,
                        'corruption': corruption,
                        'length': len(result),
                        'score': self._score_extraction(result)
                    }
                    print(f"    {method_name}: {len(result)} chars, corruption: {corruption}")
                        
                except Exception as e:
                    print(f"    {method_name} method failed: {e}")
                    results[method_name] = {
                        'text': f"❌ Error: {e}",
                        'corruption': 'error',
                        'length': 0,
                        'score': 0
                    }
            
            doc.close()
            
            # Return the best result (or all results for comparison)
            best_method = max(results.keys(), key=lambda k: results[k]['score'])
            best_text = results[best_method]['text']
            
            return f"<p>{best_text}</p>" if best_text else "❌ All PyMuPDF methods failed"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _extract_standard(self, doc):
        """Standard text extraction"""
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text
    
    def _extract_html(self, doc):
        """HTML mode extraction"""
        text = ""
        for page in doc:
            text += page.get_text("html") + "\n"
        return text
    
    def _extract_xhtml(self, doc):
        """XHTML mode extraction"""
        text = ""
        for page in doc:
            text += page.get_text("xhtml") + "\n"
        return text
    
    def _extract_dict_mode(self, doc):
        """Text extraction using dict mode"""
        text = ""
        for page in doc:
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            text += span.get("text", "") + " "
                    text += "\n"
        return text
    
    def _extract_rawdict(self, doc):
        """Raw dict mode - access glyph data directly"""
        text = ""
        for page in doc:
            try:
                rawdict = page.get_text("rawdict")
                for block in rawdict.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line.get("spans", []):
                                # Try to get actual character data
                                span_text = span.get("text", "")
                                if span_text:
                                    text += span_text + " "
                                else:
                                    # If no text, try to access char data
                                    chars = span.get("chars", [])
                                    for char in chars:
                                        c = char.get("c", "")
                                        if c:
                                            text += c
                        text += "\n"
            except Exception as e:
                text += f"[rawdict error: {e}]"
        return text
    
    def _score_extraction(self, text):
        """Score extraction quality (higher = better)"""
        if not text:
            return 0
        
        # Count readable characters vs problematic ones
        total_chars = len(text)
        cid_chars = len(re.findall(r'\(cid:\d+\)', text))
        control_chars = sum(1 for c in text if 1 <= ord(c) <= 31)
        
        readable_chars = total_chars - cid_chars - control_chars
        return readable_chars / max(total_chars, 1)

class PDFMinerStrategy(ExtractionStrategy):
    """PDFMiner extraction strategy"""
    
    def __init__(self):
        super().__init__("PDFMiner")
    
    def extract_text(self, pdf_path):
        if not PDFMINER_AVAILABLE:
            return "❌ PDFMiner not available"
        
        try:
            # Try different LAParams settings
            configs = [
                ("Default", LAParams()),
                ("Detect Vertical", LAParams(detect_vertical=True)),
                ("Word Margin 0.1", LAParams(word_margin=0.1)),
                ("Char Margin 2.0", LAParams(char_margin=2.0))
            ]
            
            best_result = ""
            best_config = "None"
            
            for config_name, laparams in configs:
                try:
                    with open(pdf_path, 'rb') as file:
                        text = pdfminer_extract_text(file, laparams=laparams)
                        cleaned = self.clean_cid_artifacts(text)
                        
                        if len(cleaned) > len(best_result):
                            best_result = cleaned
                            best_config = config_name
                            
                except Exception as e:
                    print(f"  PDFMiner {config_name} failed: {e}")
                    continue
            
            return f"<p>{best_result}</p>" if best_result else "❌ All PDFMiner configs failed"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"

class PyPDFStrategy(ExtractionStrategy):
    """PyPDF extraction strategy"""
    
    def __init__(self):
        super().__init__("PyPDF")
    
    def extract_text(self, pdf_path):
        if not PYPDF_AVAILABLE:
            return "❌ PyPDF not available"
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                text = ""
                
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                cleaned = self.clean_cid_artifacts(text)
                return f"<p>{cleaned}</p>" if cleaned else "❌ No text extracted"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"

class OCRStrategy(ExtractionStrategy):
    """OCR fallback strategy"""
    
    def __init__(self):
        super().__init__("OCR (EasyOCR)")
        if OCR_AVAILABLE:
            self.reader = easyocr.Reader(['en', 'es'])
        else:
            self.reader = None
    
    def extract_text(self, pdf_path):
        if not OCR_AVAILABLE or not self.reader:
            return "❌ EasyOCR not available"
        
        try:
            # Convert PDF to images and OCR
            import tempfile
            import subprocess
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Convert first 3 pages to images
                cmd = ["pdftoppm", "-png", "-f", "1", "-l", "3", str(pdf_path), 
                       f"{temp_dir}/page"]
                
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode != 0:
                    return "❌ PDF to image conversion failed"
                
                # OCR each page
                import glob
                image_files = glob.glob(f"{temp_dir}/page-*.png")
                image_files.sort()
                
                full_text = ""
                for img_file in image_files:
                    try:
                        results = self.reader.readtext(img_file)
                        page_text = ' '.join([result[1] for result in results])
                        full_text += page_text + "\n"
                    except Exception as e:
                        print(f"  OCR failed for {img_file}: {e}")
                        continue
                
                return f"<p>{full_text}</p>" if full_text.strip() else "❌ No text from OCR"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"

def test_extraction_strategies(pdf_id:str):
    """Test all extraction strategies on a problematic PDF"""
    
    pdf_path = PDF_FOLDER / f"{pdf_id}.pdf"
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"🧪 TESTING EXTRACTION STRATEGIES")
    print(f"📄 PDF: {pdf_id}")
    print(f"📁 Path: {pdf_path}")
    print("=" * 80)
    
    # Initialize all strategies
    strategies = [
        PdfPlumberStrategy(),
        PyMuPDFStrategy(),
        PDFMinerStrategy(),
        PyPDFStrategy(),
        OCRStrategy()
    ]
    
    results = {}
    
    for strategy in strategies:
        print(f"\n🔧 Testing: {strategy.name}")
        print("-" * 40)
        
        start_time = time.time()
        extracted_text = strategy.extract_text(pdf_path)
        end_time = time.time()
        
        execution_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Analyze corruption type
        corruption_analysis = strategy.analyze_corruption(extracted_text)
        
        # Store results
        results[strategy.name] = {
            'text': extracted_text,
            'length': len(extracted_text) if isinstance(extracted_text, str) else 0,
            'time_ms': round(execution_time, 2),
            'has_cids': '(cid:' in str(extracted_text),
            'has_control_chars': any(1 <= ord(c) <= 31 and c not in '\t\n\r' for c in str(extracted_text)),
            'corruption_type': corruption_analysis
        }
        
        # Print summary
        print(f"⏱️  Time: {execution_time:.2f}ms")
        print(f"📝 Length: {results[strategy.name]['length']} characters")
        print(f"🔍 Corruption: {corruption_analysis}")
        print(f"📖 Raw first 200 chars:")
        print(f"   {repr(extracted_text[:200])}")
        
        if len(extracted_text) > 200:
            print(f"📖 Raw middle (chars 500-700):")
            print(f"   {repr(extracted_text[500:700])}")
        
        # Show actual readable sample (if any)
        readable_sample = extract_readable_sample(extracted_text)
        if readable_sample:
            print(f"🔤 Readable sample:")
            print(f"   {readable_sample[:200]}")

def extract_readable_sample(text):
    """Try to extract readable text sample"""
    if not text:
        return ""
    
    # Remove obvious corruption patterns
    # CID patterns
    clean = re.sub(r'\(cid:\d+\)', ' ', text)
    # Control chars except newlines/tabs
    clean = re.sub(r'[\x01-\x08\x0B-\x0C\x0E-\x1F]', '', clean)
    # Repeated pattern like /g3/g3/g3
    clean = re.sub(r'(/\w+){3,}', ' ', clean)
    # HTML tags if present
    clean = re.sub(r'<[^>]+>', ' ', clean)
    
    # Get continuous text segments
    words = clean.split()
    readable_words = [w for w in words if len(w) > 2 and w.isalpha()]
    
    return ' '.join(readable_words[:20]) if readable_words else ""
    
    # Summary comparison
    print(f"\n" + "=" * 80)
    print(f"📊 EXTRACTION COMPARISON SUMMARY")
    print("=" * 80)
    
    print(f"{'Strategy':<15} {'Time(ms)':<10} {'Length':<8} {'Corruption Type':<20} {'Status'}")
    print("-" * 80)
    
    for name, result in results.items():
        corruption_type = result.get('corruption_type', 'unknown')
        status = "✅ Clean" if corruption_type == 'clean' else f"❌ {corruption_type}"
        
        print(f"{name:<15} {result['time_ms']:<10.1f} {result['length']:<8} {corruption_type:<20} {status}")
    
    # Recommend best strategy
    clean_strategies = [name for name, result in results.items() 
                       if not result['has_cids'] and not result['has_control_chars'] and result['length'] > 100]
    
    if clean_strategies:
        # Sort by length (more text is usually better)
        best_strategy = max(clean_strategies, key=lambda x: results[x]['length'])
        print(f"\n🏆 RECOMMENDED: {best_strategy} (clean extraction, {results[best_strategy]['length']} chars)")
    else:
        # If no clean extraction, recommend fastest non-empty
        non_empty = [name for name, result in results.items() if result['length'] > 100]
        if non_empty:
            best_strategy = min(non_empty, key=lambda x: results[x]['time_ms'])
            print(f"\n⚠️ FALLBACK: {best_strategy} (no clean extraction available)")
        else:
            print(f"\n❌ NO SUCCESSFUL EXTRACTION - all strategies failed")
    
    return results

if __name__ == "__main__":
    # Test with the PDF that has more CIDs - worse corruption
    test_extraction_strategies("10915-95206")
    
    # Optionally test with other PDFs
    print(f"\n" + "="*80)
    response = input("Test another PDF? Enter PDF ID (or press Enter to exit): ")
    if response.strip():
        test_extraction_strategies(response.strip())