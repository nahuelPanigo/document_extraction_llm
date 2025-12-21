#!/usr/bin/env python3
"""
Test script for PaddleOCR functionality
This script tests PaddleOCR on both single images and PDF extraction
"""

import os
import sys
import time
import numpy as np
from PIL import Image

try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR successfully imported")
except ImportError as e:
    print(f"❌ PaddleOCR import failed: {e}")
    print("Install with: pip install paddlepaddle paddleocr")
    sys.exit(1)

def test_paddleocr_basic():
    """Test basic PaddleOCR functionality"""
    print("\n=== Testing Basic PaddleOCR ===")
    
    try:
        # Initialize PaddleOCR with Spanish support
        ocr = PaddleOCR(use_textline_orientation=True, lang='es')
        print("✅ PaddleOCR initialized successfully")
        return ocr
    except Exception as e:
        print(f"❌ PaddleOCR initialization failed: {e}")
        return None

def test_image_ocr(ocr, image_path):
    """Test OCR on a single image"""
    print(f"\n=== Testing OCR on {image_path} ===")
    
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return None
    
    try:
        # Load image
        img = Image.open(image_path)
        print(f"📷 Image loaded: {img.size} pixels, mode: {img.mode}")
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Run OCR
        start_time = time.time()
        results = ocr.ocr(img_array)
        end_time = time.time()
        
        print(f"⏱️  OCR processing time: {end_time - start_time:.3f}s")
        
        # Parse results
        text_parts = []
        if results and results[0]:  # Check if results exist and are not None
            print(f"📝 Found {len(results[0])} text regions:")
            for i, line in enumerate(results[0]):
                if line and len(line) > 1 and line[1]:  # Check if line exists and has text
                    bbox, (text, confidence) = line
                    text_parts.append(text)
                    print(f"  {i+1}. Text: '{text}' (confidence: {confidence:.3f})")
                    print(f"      BBox: {bbox}")
        else:
            print("📝 No text found in image")
        
        full_text = ' '.join(text_parts)
        print(f"\n📄 Full extracted text ({len(full_text)} chars):")
        print(f"'{full_text[:200]}{'...' if len(full_text) > 200 else ''}'")
        
        return full_text
        
    except Exception as e:
        print(f"❌ OCR processing failed: {e}")
        return None

def test_pdf_extraction():
    """Test OCR on PDF images"""
    print("\n=== Testing PDF Image Extraction ===")
    
    try:
        import pdfplumber
        print("✅ pdfplumber available")
    except ImportError:
        print("❌ pdfplumber not available, install with: pip install pdfplumber")
        return
    
    pdf_path = "/home/nahuel/Documents/tesis/data/sedici/pdfs/10915-100193.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        print("Please update the PDF path in the script")
        return
    
    try:
        ocr = PaddleOCR(use_textline_orientation=True, lang='es')
        
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[4]  # Test page 5 (0-indexed)
            print(f"📄 Testing page 5 of PDF")
            print(f"   Page dimensions: {page.width} x {page.height}")
            print(f"   Found {len(page.images)} images")
            
            for i, img_obj in enumerate(page.images):
                if i > 2:  # Only test first 3 images
                    break
                    
                try:
                    x0, y0, x1, y1 = img_obj['x0'], img_obj['y0'], img_obj['x1'], img_obj['y1']
                    width, height = x1 - x0, y1 - y0
                    
                    print(f"\n  Image {i+1}: {width:.1f}x{height:.1f} pixels")
                    
                    if width < 10 or height < 10:
                        print(f"    ⚠️  Skipping - too small")
                        continue
                    
                    # Extract image
                    cropped_page = page.crop(bbox=(x0, y0, x1, y1))
                    img = cropped_page.to_image(resolution=200)
                    
                    # Convert to numpy array
                    img_array = np.array(img.original)
                    print(f"    📷 Extracted image: {img_array.shape}")
                    
                    # Run OCR
                    start_time = time.time()
                    results = ocr.predict(img_array)
                    end_time = time.time()
                    
                    print(f"    ⏱️  OCR time: {end_time - start_time:.3f}s")
                    
                    # Parse results
                    if results and results[0]:
                        text_parts = []
                        for line in results[0]:
                            if line and len(line) > 1 and line[1]:
                                text_parts.append(line[1][0])
                        
                        extracted_text = ' '.join(text_parts)
                        if extracted_text.strip():
                            print(f"    📝 Found text: '{extracted_text[:100]}{'...' if len(extracted_text) > 100 else ''}'")
                        else:
                            print(f"    📝 No text found")
                    else:
                        print(f"    📝 No OCR results")
                        
                except Exception as e:
                    print(f"    ❌ Error processing image {i+1}: {e}")
                    continue
                    
    except Exception as e:
        print(f"❌ PDF processing failed: {e}")

def create_test_image():
    """Create a simple test image with text"""
    print("\n=== Creating Test Image ===")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple image with text
        width, height = 400, 100
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font, fall back to default if not available
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # Draw some text
        text = "Hello PaddleOCR! This is a test."
        draw.text((10, 30), text, fill='black', font=font)
        
        # Save test image
        test_image_path = 'test_ocr_image.png'
        img.save(test_image_path)
        print(f"✅ Created test image: {test_image_path}")
        
        return test_image_path
        
    except Exception as e:
        print(f"❌ Failed to create test image: {e}")
        return None

def main():
    """Main test function"""
    print("🔍 PaddleOCR Diagnostic Script")
    print("=" * 50)
    
    # Test basic PaddleOCR
    ocr = test_paddleocr_basic()
    if not ocr:
        print("❌ Cannot proceed without PaddleOCR")
        return
    
    # Create and test on a simple image
    test_image = create_test_image()
    if test_image:
        test_image_ocr(ocr, test_image)
    
    # Test on existing debug images if they exist
    for i in range(3):
        debug_image = f'debug_image_{i}.png'
        if os.path.exists(debug_image):
            test_image_ocr(ocr, debug_image)
    
    # Test PDF extraction
    test_pdf_extraction()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    main()