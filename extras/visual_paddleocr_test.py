#!/usr/bin/env python3
"""
Visual test script for PaddleOCR functionality
This script tests PaddleOCR and shows images with extracted text using matplotlib
"""

import os
import sys
import time
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

try:
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR successfully imported")
except ImportError as e:
    print(f"❌ PaddleOCR import failed: {e}")
    print("Install with: pip install paddlepaddle paddleocr")
    sys.exit(1)

try:
    import pdfplumber
    print("✅ pdfplumber successfully imported")
except ImportError as e:
    print(f"❌ pdfplumber import failed: {e}")
    print("Install with: pip install pdfplumber")
    sys.exit(1)

def visualize_ocr_results(image, results, title="OCR Results"):
    """Visualize image with OCR results overlaid"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
    
    # Show original image
    ax1.imshow(image)
    ax1.set_title("Original Image")
    ax1.axis('off')
    
    # Show image with bounding boxes and text
    ax2.imshow(image)
    ax2.set_title(title)
    
    extracted_texts = []
    
    # Handle new OCRResult format
    if results and len(results) > 0:
        ocr_result = results[0]
        
        # Check if it's the new OCRResult object
        if hasattr(ocr_result, '__len__'):
            # New format - OCRResult object behaves like a list
            try:
                for i, detection in enumerate(ocr_result):
                    if hasattr(detection, 'bbox') and hasattr(detection, 'text'):
                        # New format with bbox and text attributes
                        bbox = detection.bbox
                        text = detection.text
                        confidence = getattr(detection, 'confidence', 1.0)
                    elif hasattr(detection, '__len__') and len(detection) >= 2:
                        # Old format compatibility
                        bbox = detection[0]
                        text_info = detection[1]
                        if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                            text, confidence = text_info[0], text_info[1]
                        else:
                            text, confidence = str(text_info), 1.0
                    else:
                        continue
                    
                    extracted_texts.append(f"{text} ({confidence:.2f})")
                    
                    # Draw bounding box
                    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                        # Convert bbox to polygon points
                        if len(bbox) == 4 and all(isinstance(x, (int, float)) for x in bbox):
                            # Format: [x1, y1, x2, y2]
                            x1, y1, x2, y2 = bbox
                            points = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
                        else:
                            # Format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                            points = np.array(bbox)
                    else:
                        points = np.array(bbox)
                    
                    rect = patches.Polygon(points, linewidth=2, edgecolor='red', 
                                         facecolor='none', alpha=0.7)
                    ax2.add_patch(rect)
                    
                    # Add text label
                    ax2.text(points[0][0], points[0][1] - 5, f"{i+1}: {text[:20]}...", 
                            color='red', fontsize=8, weight='bold',
                            bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
            except Exception as e:
                print(f"Error processing OCR results: {e}")
                # Fallback: try to print the structure for debugging
                print(f"OCR Result type: {type(ocr_result)}")
                if hasattr(ocr_result, '__dict__'):
                    print(f"OCR Result attributes: {dir(ocr_result)}")
    
    ax2.axis('off')
    
    # Show extracted text
    if extracted_texts:
        full_text = "\n".join([f"{i+1}. {text}" for i, text in enumerate(extracted_texts)])
        plt.figtext(0.02, 0.5, f"Extracted Text:\n{full_text}", 
                   fontsize=10, verticalalignment='top', 
                   bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.8))
    else:
        plt.figtext(0.02, 0.5, "No text extracted", 
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle="round,pad=0.5", facecolor='lightcoral', alpha=0.8))
    
    plt.tight_layout()
    plt.show()
    
    return extracted_texts

def debug_paddleocr_results(results):
    """Debug function to understand PaddleOCR result format"""
    print(f"\n🔍 DEBUG: OCR Results Structure")
    print(f"Type: {type(results)}")
    print(f"Length: {len(results) if results else 'None'}")
    
    if results and len(results) > 0:
        ocr_result = results[0]
        print(f"First element type: {type(ocr_result)}")
        print(f"First element length: {len(ocr_result) if hasattr(ocr_result, '__len__') else 'No len'}")
        
        # Check if it's OCRResult object
        if hasattr(ocr_result, '__dict__'):
            print(f"OCRResult attributes: {[attr for attr in dir(ocr_result) if not attr.startswith('_')]}")
        
        # Try to access individual detections
        if hasattr(ocr_result, '__len__') and len(ocr_result) > 0:
            try:
                first_detection = ocr_result[0]
                print(f"First detection type: {type(first_detection)}")
                print(f"First detection: {first_detection}")
                
                # Check attributes of detection
                if hasattr(first_detection, '__dict__'):
                    print(f"Detection attributes: {[attr for attr in dir(first_detection) if not attr.startswith('_')]}")
                
                # Try to access bbox and text
                if hasattr(first_detection, 'bbox'):
                    print(f"Bbox: {first_detection.bbox}")
                if hasattr(first_detection, 'text'):
                    print(f"Text: {first_detection.text}")
                if hasattr(first_detection, 'confidence'):
                    print(f"Confidence: {first_detection.confidence}")
                    
            except Exception as e:
                print(f"Error accessing detection: {e}")
    print()

def test_paddleocr_with_visualization():
    """Test PaddleOCR with visual output"""
    print("\n=== Testing PaddleOCR with Visualization ===")
    
    # Initialize PaddleOCR
    try:
        ocr = PaddleOCR(use_textline_orientation=True, lang='es')
        print("✅ PaddleOCR initialized successfully")
    except Exception as e:
        print(f"❌ PaddleOCR initialization failed: {e}")
        return
    
    # Test 1: Simple test image
    print("\n📷 Testing on simple test image...")
    try:
        # Create a simple test image
        from PIL import Image, ImageDraw, ImageFont
        
        width, height = 600, 200
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        texts = [
            "Hello PaddleOCR!",
            "This is a test document.",
            "Can you extract this text?"
        ]
        
        for i, text in enumerate(texts):
            draw.text((20, 20 + i * 50), text, fill='black', font=font)
        
        # Test OCR
        img_array = np.array(img)
        start_time = time.time()
        results = ocr.ocr(img_array)
        end_time = time.time()
        
        print(f"⏱️  OCR processing time: {end_time - start_time:.3f}s")
        
        # Debug the results structure first
        debug_paddleocr_results(results)
        
        visualize_ocr_results(img, results, "Simple Test Image - OCR Results")
        
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
    
    # Test 2: Existing debug images
    print("\n📷 Testing on existing debug images...")
    for i in range(3):
        debug_image_path = f'debug_image_{i}.png'
        if os.path.exists(debug_image_path):
            print(f"\nTesting {debug_image_path}...")
            try:
                img = Image.open(debug_image_path)
                img_array = np.array(img)
                
                start_time = time.time()
                results = ocr.ocr(img_array)
                end_time = time.time()
                
                print(f"⏱️  OCR processing time: {end_time - start_time:.3f}s")
                visualize_ocr_results(img, results, f"Debug Image {i} - OCR Results")
                
            except Exception as e:
                print(f"❌ Error processing {debug_image_path}: {e}")
    
    # Test 3: Extract and test PDF images
    print("\n📄 Testing PDF image extraction...")
    pdf_path = "/home/nahuel/Documents/tesis/data/sedici/pdfs/10915-100193.pdf"
    
    if os.path.exists(pdf_path):
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[2]  # Test page 5
                print(f"📄 Processing page 2 of PDF")
                print(f"   Found {len(page.images)} images")
                
                for i, img_obj in enumerate(page.images[:3]):  # Only first 3 images
                    try:
                        x0, y0, x1, y1 = img_obj['x0'], img_obj['y0'], img_obj['x1'], img_obj['y1']
                        width, height = x1 - x0, y1 - y0
                        
                        print(f"\n  📷 Image {i+1}: {width:.1f}x{height:.1f}")
                        print(f"    Tag: {img_obj.get('tag', 'None')}")
                        print(f"    Object type: {img_obj.get('object_type', 'None')}")
                        
                        # Skip full page images (likely page backgrounds)
                        page_width, page_height = page.width, page.height
                        
                        # Check if this image covers most of the page (likely a page background)
                        if (width > page_width * 0.8 and height > page_height * 0.8):
                            print(f"    ⚠️  Skipping - full page image (likely background)")
                            continue
                        
                        # Skip images that are too small for meaningful OCR
                        if width < 50 or height < 20:
                            print(f"    ⚠️  Skipping - too small for meaningful OCR")
                            continue
                        
                        # Skip images tagged as 'Artifact' (usually decorative/background)
                        if img_obj.get('tag') == 'Artifact':
                            print(f"    ⚠️  Skipping - marked as Artifact (likely decorative)")
                            continue
                        
                        print(f"    ✅ Processing this image...")
                        
                        # Extract image
                        cropped_page = page.crop(bbox=(x0, y0, x1, y1))
                        img = cropped_page.to_image(resolution=200)
                        pil_image = img.original
                        
                        # Convert to numpy array
                        img_array = np.array(pil_image)
                        
                        print(f"    📏 Image shape: {img_array.shape}")
                        
                        # Run OCR
                        start_time = time.time()
                        results = ocr.ocr(img_array)
                        end_time = time.time()
                        
                        print(f"    ⏱️  OCR time: {end_time - start_time:.3f}s")
                        
                        # Visualize results
                        visualize_ocr_results(pil_image, results, 
                                            f"PDF Page 5 - Image {i+1} OCR Results")
                        
                        # Print summary
                        if results and results[0]:
                            text_count = len([line for line in results[0] if line and len(line) > 1 and line[1]])
                            print(f"    📝 Found {text_count} text regions")
                            
                            # Print extracted text for debugging
                            for j, line in enumerate(results[0]):
                                if line and len(line) > 1 and line[1]:
                                    text_info = line[1]
                                    if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                        text, confidence = text_info[0], text_info[1]
                                        print(f"      Text {j+1}: '{text}' (confidence: {confidence:.3f})")
                                    else:
                                        print(f"      Text {j+1}: '{text_info}'")
                        else:
                            print(f"    📝 No text detected")
                            
                    except Exception as e:
                        print(f"    ❌ Error processing PDF image {i+1}: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ PDF processing failed: {e}")
    else:
        print(f"❌ PDF not found: {pdf_path}")

def compare_preprocessing():
    """Compare OCR results with and without preprocessing"""
    print("\n=== Comparing Preprocessing Effects ===")
    
    try:
        import cv2
        ocr = PaddleOCR(use_textline_orientation=True, lang='es')
        
        # Test on an existing debug image
        for i in range(3):
            debug_image_path = f'debug_image_{i}.png'
            if os.path.exists(debug_image_path):
                print(f"\nComparing preprocessing on {debug_image_path}...")
                
                # Load image
                img = Image.open(debug_image_path)
                
                # Original image
                img_array_orig = np.array(img)
                results_orig = ocr.ocr(img_array_orig)
                
                # Preprocessed image (grayscale + threshold)
                gray = cv2.cvtColor(img_array_orig, cv2.COLOR_RGB2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                img_preprocessed = Image.fromarray(thresh)
                
                img_array_prep = np.array(img_preprocessed)
                results_prep = ocr.ocr(img_array_prep)
                
                # Create comparison visualization
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
                
                # Original image
                ax1.imshow(img)
                ax1.set_title("Original Image")
                ax1.axis('off')
                
                # Preprocessed image
                ax2.imshow(img_preprocessed, cmap='gray')
                ax2.set_title("Preprocessed Image")
                ax2.axis('off')
                
                # Original results
                ax3.imshow(img)
                if results_orig and results_orig[0]:
                    for line in results_orig[0]:
                        if line and len(line) > 1:
                            bbox = np.array(line[0])
                            rect = patches.Polygon(bbox, linewidth=2, edgecolor='red', 
                                                 facecolor='none', alpha=0.7)
                            ax3.add_patch(rect)
                ax3.set_title(f"Original - {len(results_orig[0]) if results_orig and results_orig[0] else 0} detections")
                ax3.axis('off')
                
                # Preprocessed results
                ax4.imshow(img_preprocessed, cmap='gray')
                if results_prep and results_prep[0]:
                    for line in results_prep[0]:
                        if line and len(line) > 1:
                            bbox = np.array(line[0])
                            rect = patches.Polygon(bbox, linewidth=2, edgecolor='blue', 
                                                 facecolor='none', alpha=0.7)
                            ax4.add_patch(rect)
                ax4.set_title(f"Preprocessed - {len(results_prep[0]) if results_prep and results_prep[0] else 0} detections")
                ax4.axis('off')
                
                plt.tight_layout()
                plt.show()
                
                # Print text comparison
                def extract_text_from_results(results):
                    if not results or not results[0]:
                        return "No text found"
                    texts = []
                    for line in results[0]:
                        if line and len(line) > 1 and line[1]:
                            text_info = line[1]
                            if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                texts.append(text_info[0])
                            else:
                                texts.append(str(text_info))
                    return " | ".join(texts) if texts else "No text found"
                
                print(f"Original text: {extract_text_from_results(results_orig)}")
                print(f"Preprocessed text: {extract_text_from_results(results_prep)}")
                
                break  # Only test first available image
                
    except ImportError:
        print("❌ OpenCV not available for preprocessing comparison")
    except Exception as e:
        print(f"❌ Preprocessing comparison failed: {e}")

def main():
    """Main test function"""
    print("🔍 PaddleOCR Visual Diagnostic Script")
    print("=" * 60)
    
    test_paddleocr_with_visualization()
    compare_preprocessing()
    
    print("\n" + "=" * 60)
    print("🏁 Visual testing completed!")
    print("Check the matplotlib windows to see OCR results on images.")

if __name__ == "__main__":
    main()