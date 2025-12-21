#!/usr/bin/env python3
"""
PDF Image Analyzer - Detailed analysis of images in PDF pages
This script examines all images in a PDF and helps distinguish real content from backgrounds
"""

import os
import sys
import pdfplumber
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

def analyze_pdf_images(pdf_path, max_pages=5):
    """Analyze all images in PDF pages with detailed visualization"""
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"📄 Analyzing PDF: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            
            # Analyze each page
            for page_num in range(min(max_pages, len(pdf.pages))):
                page = pdf.pages[page_num]
                print(f"\n{'='*60}")
                print(f"📄 PAGE {page_num + 1}")
                print(f"{'='*60}")
                print(f"Page dimensions: {page.width:.1f} x {page.height:.1f}")
                print(f"Number of images found: {len(page.images)}")
                
                if len(page.images) == 0:
                    print("  No images on this page")
                    continue
                
                # We'll show images individually instead of all together
                num_images = len(page.images)
                
                # Analyze each image
                for i, img_obj in enumerate(page.images):
                    try:
                        print(f"\n  📷 IMAGE {i+1}:")
                        
                        # Extract image properties
                        x0, y0, x1, y1 = img_obj['x0'], img_obj['y0'], img_obj['x1'], img_obj['y1']
                        width, height = x1 - x0, y1 - y0
                        
                        # Print all available properties
                        print(f"    Position: ({x0:.1f}, {y0:.1f}) to ({x1:.1f}, {y1:.1f})")
                        print(f"    Dimensions: {width:.1f} x {height:.1f}")
                        print(f"    Area: {width * height:.0f} pixels²")
                        
                        # Calculate coverage of the page
                        page_area = page.width * page.height
                        coverage = (width * height) / page_area * 100
                        print(f"    Page coverage: {coverage:.1f}%")
                        
                        # Print all available metadata
                        print(f"    Available properties: {list(img_obj.keys())}")
                        for key, value in img_obj.items():
                            if key not in ['x0', 'y0', 'x1', 'y1']:
                                print(f"      {key}: {value}")
                        
                        # Classification heuristics
                        is_full_page = coverage > 80
                        is_large = width > page.width * 0.6 or height > page.height * 0.6
                        is_artifact = img_obj.get('tag') == 'Artifact'
                        is_figure = img_obj.get('tag') == 'Figure'
                        is_small = width < 100 or height < 50
                        
                        print(f"    🔍 Analysis:")
                        print(f"      Full page image: {'Yes' if is_full_page else 'No'}")
                        print(f"      Large image: {'Yes' if is_large else 'No'}")
                        print(f"      Tagged as Artifact: {'Yes' if is_artifact else 'No'}")
                        print(f"      Tagged as Figure: {'Yes' if is_figure else 'No'}")
                        print(f"      Small image: {'Yes' if is_small else 'No'}")
                        
                        # Recommendation
                        if is_full_page:
                            recommendation = "🚫 SKIP - Full page (likely background)"
                        elif is_artifact and not is_figure:
                            recommendation = "🚫 SKIP - Artifact (decorative)"
                        elif is_small:
                            recommendation = "🚫 SKIP - Too small for OCR"
                        elif is_figure:
                            recommendation = "✅ PROCESS - Tagged as Figure"
                        elif not is_large:
                            recommendation = "✅ PROCESS - Reasonable size content"
                        else:
                            recommendation = "⚠️  UNCERTAIN - Large but not full page"
                        
                        print(f"    {recommendation}")
                        
                        # Extract and display the image
                        try:
                            cropped_page = page.crop(bbox=(x0, y0, x1, y1))
                            img = cropped_page.to_image(resolution=100)  # Lower resolution for display
                            pil_image = img.original
                            
                            print(f"    ✅ Successfully extracted image: {pil_image.size}")
                            
                            # Show image individually
                            plt.figure(figsize=(10, 8))
                            plt.imshow(pil_image)
                            
                            title = f"Page {page_num+1}, Image {i+1}\n"
                            title += f"Size: {width:.0f}x{height:.0f} ({coverage:.1f}% coverage)\n"
                            title += f"Tag: {img_obj.get('tag', 'No tag')}"
                            
                            if is_full_page:
                                title += "\n🚫 FULL PAGE"
                            elif is_figure:
                                title += "\n✅ FIGURE"
                            elif is_artifact:
                                title += "\n🚫 ARTIFACT"
                            else:
                                title += "\n📄 CONTENT"
                            
                            plt.title(title, fontsize=12)
                            plt.axis('off')
                            plt.tight_layout()
                            plt.show()
                            
                            # Save individual image for inspection
                            save_path = f"page_{page_num+1}_image_{i+1}.png"
                            pil_image.save(save_path)
                            print(f"    💾 Saved as: {save_path}")
                            
                        except Exception as e:
                            print(f"    ❌ Failed to extract image: {e}")
                    
                    except Exception as e:
                        print(f"    ❌ Error analyzing image {i+1}: {e}")
                
                # Images are now shown individually above
                
                # Summary for this page
                total_images = len(page.images)
                full_page_images = sum(1 for img in page.images 
                                     if ((img['x1'] - img['x0']) * (img['y1'] - img['y0'])) / (page.width * page.height) > 0.8)
                artifact_images = sum(1 for img in page.images if img.get('tag') == 'Artifact')
                figure_images = sum(1 for img in page.images if img.get('tag') == 'Figure')
                
                print(f"\n  📊 PAGE {page_num + 1} SUMMARY:")
                print(f"    Total images: {total_images}")
                print(f"    Full page images: {full_page_images}")
                print(f"    Artifact images: {artifact_images}")
                print(f"    Figure images: {figure_images}")
                print(f"    Potential content images: {total_images - full_page_images - artifact_images + figure_images}")
                
    except Exception as e:
        print(f"❌ Error analyzing PDF: {e}")

def create_filtering_recommendations(pdf_path):
    """Create filtering recommendations based on PDF analysis"""
    
    print(f"\n🎯 FILTERING RECOMMENDATIONS")
    print(f"{'='*60}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_images = []
            
            # Collect all image data
            for page_num, page in enumerate(pdf.pages[:10]):  # Analyze first 3 pages
                for img_obj in page.images:
                    x0, y0, x1, y1 = img_obj['x0'], img_obj['y0'], img_obj['x1'], img_obj['y1']
                    width, height = x1 - x0, y1 - y0
                    page_area = page.width * page.height
                    coverage = (width * height) / page_area * 100
                    
                    all_images.append({
                        'page': page_num + 1,
                        'width': width,
                        'height': height,
                        'coverage': coverage,
                        'tag': img_obj.get('tag'),
                        'object_type': img_obj.get('object_type'),
                        'area': width * height
                    })
            
            if not all_images:
                print("No images found in PDF")
                return
            
            # Analyze patterns
            full_page_count = sum(1 for img in all_images if img['coverage'] > 80)
            artifact_count = sum(1 for img in all_images if img['tag'] == 'Artifact')
            figure_count = sum(1 for img in all_images if img['tag'] == 'Figure')
            
            print(f"Total images analyzed: {len(all_images)}")
            print(f"Full page images (>80% coverage): {full_page_count}")
            print(f"Images tagged as 'Artifact': {artifact_count}")
            print(f"Images tagged as 'Figure': {figure_count}")
            
            print(f"\n🔧 RECOMMENDED FILTERING RULES:")
            print(f"1. Skip images with >80% page coverage (removes {full_page_count} images)")
            print(f"2. Skip images tagged as 'Artifact' unless also tagged as 'Figure'")
            print(f"3. Skip images smaller than 50x20 pixels")
            print(f"4. Prioritize images tagged as 'Figure' ({figure_count} found)")
            
            # Show size distribution
            areas = [img['area'] for img in all_images]
            if areas:
                print(f"\n📏 SIZE STATISTICS:")
                print(f"   Smallest image: {min(areas):.0f} pixels²")
                print(f"   Largest image: {max(areas):.0f} pixels²")
                print(f"   Average image: {np.mean(areas):.0f} pixels²")
    
    except Exception as e:
        print(f"❌ Error creating recommendations: {e}")

def main():
    """Main function"""
    print("🔍 PDF Image Analyzer")
    print("This tool analyzes all images in PDF pages to help distinguish content from backgrounds")
    print("=" * 80)
    
    pdf_path = "/home/nahuel/Documents/tesis/data/sedici/pdfs/10915-67615.pdf"
    
    # Analyze images page by page
    analyze_pdf_images(pdf_path, max_pages=10)
    
    # Create filtering recommendations
    create_filtering_recommendations(pdf_path)
    
    print(f"\n🏁 Analysis complete!")
    print(f"Check the saved PNG files to see individual extracted images.")

if __name__ == "__main__":
    main()