import json
import re
import pandas as pd
from pathlib import Path
import sys
import subprocess

# Add parent directory to path to import constants
sys.path.append(str(Path(__file__).parent.parent))
from constants import DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED, JSON_FOLDER, PDF_FOLDER

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

def analyze_cid_in_dataset():
    """Analyze CID patterns in the dataset and identify problematic documents"""
    
    # Load dataset from JSON_FOLDER
    dataset_path = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED
    print(f"📂 Loading dataset from: {dataset_path}")
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract documents from training, validation, test splits
    all_docs = []
    for split in ['training', 'validation', 'test']:
        if split in data:
            all_docs.extend(data[split])
            print(f"📊 {split}: {len(data[split])} documents")
    
    print(f"📊 Total documents: {len(all_docs)}")
    
    # Analyze each document
    problematic_docs = []
    cid_stats = {
        'total_docs': len(all_docs),
        'docs_with_cids': 0,
        'significant_cid_docs': 0
    }
    
    for doc in all_docs:
        doc_id = doc.get('id', 'unknown')
        original_text = doc.get('original_text', '')
        
        if not original_text:
            continue
            
        # Find CID patterns
        cid_matches = re.findall(r'\(cid:\d+\)', original_text)
        
        if cid_matches:
            cid_stats['docs_with_cids'] += 1
            
            # Calculate CID percentage
            total_chars = len(original_text)
            cid_chars = sum(len(match) for match in cid_matches)
            cid_percentage = (cid_chars / total_chars) * 100 if total_chars > 0 else 0
            
            # Also count unique CID numbers
            unique_cids = list(set(re.findall(r'\(cid:(\d+)\)', original_text)))
            
            # Consider significant if >5% CIDs or >20 unique CIDs
            is_significant = cid_percentage > 5.0 or len(unique_cids) > 20
            
            if is_significant:
                cid_stats['significant_cid_docs'] += 1
            
            doc_info = {
                'id': doc_id,
                'total_chars': total_chars,
                'cid_count': len(cid_matches),
                'unique_cids': len(unique_cids),
                'cid_percentage': round(cid_percentage, 2),
                'is_significant': is_significant,
                'sample_cids': sorted([int(x) for x in unique_cids[:10]])  # First 10 unique CIDs
            }
            
            problematic_docs.append(doc_info)
    
    # Sort by CID percentage (descending)
    problematic_docs.sort(key=lambda x: x['cid_percentage'], reverse=True)
    
    # Print statistics
    print("\n" + "="*60)
    print("📈 CID ANALYSIS RESULTS")
    print("="*60)
    print(f"Total documents analyzed: {cid_stats['total_docs']}")
    print(f"Documents with CIDs: {cid_stats['docs_with_cids']}")
    print(f"Documents with significant CID issues: {cid_stats['significant_cid_docs']}")
    print(f"Percentage with CID issues: {(cid_stats['docs_with_cids']/cid_stats['total_docs']*100):.1f}%")
    print(f"Percentage with significant issues: {(cid_stats['significant_cid_docs']/cid_stats['total_docs']*100):.1f}%")
    
    # Print top problematic documents
    print("\n📋 TOP 20 MOST PROBLEMATIC DOCUMENTS:")
    print("-" * 100)
    print(f"{'ID':<15} {'CID %':<8} {'CID Count':<10} {'Unique':<8} {'Sample CIDs'}")
    print("-" * 100)
    
    for doc in problematic_docs[:20]:
        print(f"{doc['id']:<15} {doc['cid_percentage']:<8.1f} "
              f"{doc['cid_count']:<10} {doc['unique_cids']:<8} {doc['sample_cids']}")
    
    # Print significant CID issues only
    significant_docs = [doc for doc in problematic_docs if doc['is_significant']]
    
    print(f"\n🚨 DOCUMENTS WITH SIGNIFICANT CID ISSUES ({len(significant_docs)} total):")
    print("-" * 80)
    
    for doc in significant_docs:
        print(f"ID: {doc['id']}")
        print(f"  CID Percentage: {doc['cid_percentage']:.2f}%")
        print(f"  CID Count: {doc['cid_count']}")
        print(f"  Unique CIDs: {doc['unique_cids']}")
        print(f"  Sample CID numbers: {doc['sample_cids']}")
        print()
    
    # Save results to file
    results = {
        'statistics': cid_stats,
        'all_cid_documents': problematic_docs,
        'significant_cid_documents': significant_docs
    }
    
    output_file = Path(__file__).parent / 'cid_analysis_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Results saved to: {output_file}")
    
    return results

def analyze_pdf_fonts(pdf_id):
    """Analyze fonts in a specific PDF file"""
    pdf_path = PDF_FOLDER / f"{pdf_id}.pdf"
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return None
    
    print(f"\n🔍 ANALYZING FONTS FOR: {pdf_id}")
    print("=" * 60)
    
    font_info = {
        'pdf_id': pdf_id,
        'pdf_path': str(pdf_path),
        'pdffonts_output': None,
        'pymupdf_fonts': None,
        'pdfplumber_fonts': None,
        'unicode_mapping_issues': []
    }
    
    # Method 1: pdffonts command line tool
    try:
        print("📋 Using pdffonts command...")
        result = subprocess.run(['pdffonts', str(pdf_path)], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            font_info['pdffonts_output'] = result.stdout
            print("✅ pdffonts successful")
            print(result.stdout)
        else:
            print(f"❌ pdffonts failed: {result.stderr}")
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"❌ pdffonts not available or timed out: {e}")
    
    # Method 2: PyMuPDF font extraction
    if PYMUPDF_AVAILABLE:
        try:
            print("\n📋 Using PyMuPDF font analysis...")
            doc = fitz.open(str(pdf_path))
            fonts = []
            
            for page_num in range(min(5, len(doc))):  # Analyze first 5 pages
                page = doc.load_page(page_num)
                font_list = page.get_fonts()
                
                for font in font_list:
                    font_dict = {
                        'page': page_num,
                        'xref': font[0],
                        'ext': font[1],
                        'type': font[2],
                        'basefont': font[3],
                        'encoding': font[4] if len(font) > 4 else 'Unknown',
                        'flags': font[5] if len(font) > 5 else None
                    }
                    
                    # Check ToUnicode mapping for this font
                    try:
                        font_buffer = doc.extract_font(font[0])
                        if font_buffer:
                            # Check if font has proper Unicode mapping
                            font_dict['has_unicode_mapping'] = True
                            font_dict['font_size_bytes'] = len(font_buffer[2]) if font_buffer[2] else 0
                        else:
                            font_dict['has_unicode_mapping'] = False
                            font_dict['unicode_issue'] = "No font buffer available"
                    except Exception as e:
                        font_dict['has_unicode_mapping'] = False
                        font_dict['unicode_issue'] = str(e)
                    
                    fonts.append(font_dict)
            
            doc.close()
            font_info['pymupdf_fonts'] = fonts
            
            print(f"✅ Found {len(fonts)} font entries")
            unicode_issues = [f for f in fonts if not f.get('has_unicode_mapping', True)]
            if unicode_issues:
                print(f"⚠️ {len(unicode_issues)} fonts have Unicode mapping issues!")
            
            for font in fonts[:10]:  # Show first 10
                unicode_status = "✅" if font.get('has_unicode_mapping', True) else "❌"
                issue = f" ({font.get('unicode_issue', '')})" if not font.get('has_unicode_mapping', True) else ""
                print(f"  {unicode_status} {font['basefont']} (Type: {font['type']}, Encoding: {font['encoding']}){issue}")
                
            # Store Unicode issues for summary
            font_info['unicode_mapping_issues'] = [f"{f['basefont']}: {f.get('unicode_issue', 'No mapping')}" 
                                                  for f in unicode_issues]
                
        except Exception as e:
            print(f"❌ PyMuPDF font analysis failed: {e}")
    
    # Method 3: pdfplumber font analysis
    if PDFPLUMBER_AVAILABLE:
        try:
            print("\n📋 Using pdfplumber font analysis...")
            with pdfplumber.open(str(pdf_path)) as pdf:
                fonts = []
                
                for page_num, page in enumerate(pdf.pages[:3]):  # First 3 pages
                    try:
                        chars = page.chars
                        for char in chars[:100]:  # Sample first 100 characters
                            font_info_char = {
                                'page': page_num,
                                'fontname': char.get('fontname', 'Unknown'),
                                'size': char.get('size', 0),
                                'text': char.get('text', ''),
                                'x0': char.get('x0', 0),
                                'y0': char.get('y0', 0)
                            }
                            fonts.append(font_info_char)
                    except Exception as e:
                        print(f"❌ Error processing page {page_num}: {e}")
                        break
                
                font_info['pdfplumber_fonts'] = fonts
                
                # Get unique font names
                unique_fonts = list(set([f['fontname'] for f in fonts if f['fontname'] != 'Unknown']))
                print(f"✅ Found {len(unique_fonts)} unique fonts")
                for font_name in unique_fonts[:10]:
                    print(f"  - {font_name}")
                    
        except Exception as e:
            print(f"❌ pdfplumber font analysis failed: {e}")
    
    return font_info

def analyze_fonts_for_problematic_pdfs(max_analyze=5):
    """Analyze fonts for the most problematic PDFs"""
    print("🔍 RUNNING CID ANALYSIS FIRST...")
    results = analyze_cid_in_dataset()
    
    significant_docs = results['significant_cid_documents']
    
    if not significant_docs:
        print("✅ No significant CID issues found!")
        return
    
    print(f"\n🎯 ANALYZING FONTS FOR TOP {max_analyze} PROBLEMATIC PDFs...")
    
    font_analyses = []
    for i, doc in enumerate(significant_docs[:max_analyze]):
        pdf_id = doc['id']
        font_analysis = analyze_pdf_fonts(pdf_id)
        if font_analysis:
            font_analyses.append(font_analysis)
    
    # Save font analysis results
    output_file = Path(__file__).parent / 'font_analysis_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(font_analyses, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Font analysis saved to: {output_file}")
    
    return font_analyses

if __name__ == "__main__":
    # Run both CID analysis and font analysis
    analyze_fonts_for_problematic_pdfs()