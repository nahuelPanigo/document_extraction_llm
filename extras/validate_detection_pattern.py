import os
import json
import fitz
import subprocess
from pathlib import Path
import sys

# Add parent directory to path to import constants
sys.path.append(str(Path(__file__).parent.parent))
from constants import PDF_FOLDER, JSON_FOLDER, DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED

def extract_pdf_metadata_and_fonts(pdf_path):
    """Extract creator and font info from a PDF"""
    try:
        doc = fitz.open(str(pdf_path))
        
        # Get metadata
        metadata = doc.metadata
        creator = metadata.get('creator', 'Unknown')
        producer = metadata.get('producer', 'Unknown')
        
        # Get fonts from first page
        fonts = []
        try:
            font_list = doc.get_page_fonts(0) if len(doc) > 0 else []
            for font in font_list:
                fonts.append({
                    'basefont': font[3] if len(font) > 3 else 'Unknown',
                    'type': font[2] if len(font) > 2 else 'Unknown',
                    'encoding': font[4] if len(font) > 4 else 'Unknown'
                })
        except Exception as e:
            fonts = [{'error': str(e)}]
        
        doc.close()
        
        return {
            'creator': creator,
            'producer': producer,
            'fonts': fonts
        }
        
    except Exception as e:
        return {
            'creator': 'Error',
            'producer': 'Error', 
            'fonts': [{'error': str(e)}],
            'extraction_error': str(e)
        }

def get_pdffonts_info(pdf_path):
    """Get font info using pdffonts command"""
    try:
        result = subprocess.run(['pdffonts', str(pdf_path)], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"
    except Exception as e:
        return f"pdffonts failed: {e}"

def load_cid_analysis():
    """Load the CID analysis results"""
    cid_file = Path(__file__).parent / 'cid_analysis_results.json'
    if cid_file.exists():
        with open(cid_file, 'r') as f:
            return json.load(f)
    return None

def validate_detection_patterns():
    """Check if PDF metadata patterns match CID issues"""
    
    print("🔍 VALIDATING DETECTION PATTERNS")
    print("=" * 60)
    
    # Load dataset to get valid IDs
    dataset_path = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # Extract all document IDs from dataset
    dataset_ids = set()
    for split in ['training', 'validation', 'test']:
        if split in dataset:
            for doc in dataset[split]:
                dataset_ids.add(doc.get('id'))
    
    print(f"📊 Dataset contains {len(dataset_ids)} document IDs")
    
    # Load CID analysis
    cid_data = load_cid_analysis()
    if not cid_data:
        print("❌ No CID analysis found. Run check_pdf_extraction.py first")
        return
    
    # Get problematic document IDs
    problematic_ids = set()
    all_cid_ids = set()
    
    for doc in cid_data.get('all_cid_documents', []):
        all_cid_ids.add(doc['id'])
        if doc.get('is_significant', False):
            problematic_ids.add(doc['id'])
    
    print(f"📊 Found {len(problematic_ids)} problematic IDs in dataset")
    print(f"📊 Found {len(all_cid_ids)} total CID IDs in dataset")
    
    # Filter PDF files to only those in dataset
    all_pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.endswith('.pdf')]
    dataset_pdf_files = []
    
    for pdf_file in all_pdf_files:
        pdf_id = pdf_file.replace('.pdf', '')
        if pdf_id in dataset_ids:
            dataset_pdf_files.append(pdf_file)
    
    print(f"📁 Found {len(all_pdf_files)} total PDF files")
    print(f"📁 Found {len(dataset_pdf_files)} PDF files in dataset")
    
    # Analysis results
    analysis = {
        'total_pdfs': len(dataset_pdf_files),
        'dataset_pdfs': len(dataset_pdf_files),
        'problematic_pdfs_found': 0,
        'pattern_matches': 0,
        'pattern_misses': 0,
        'false_positives': 0,
        'creators': {},
        'font_patterns': {},
        'detailed_results': []
    }
    
    # FONT-ONLY DETECTION - Expanded patterns from misses analysis
    
    # ArialNarrow patterns (any prefix + ArialNarrow)
    arial_narrow_patterns = [
        '+ArialNarrow',           # Any subset ArialNarrow
        'ArialNarrow,Italic',     # ArialNarrow italic variants
        'ArialNarrow'             # Base ArialNarrow
    ]
    
    # Identity-H encoding (common CID issue)
    identity_h_patterns = [
        'Identity-H',             # CID encoding
        'TimesNewRomanPSMT-Identity-H'
    ]
    
    # Type3 fonts with empty names (problematic)
    type3_patterns = [
        "{'basefont': '', 'type': 'Type3'",    # Empty Type3 fonts
        "'type': 'Type3', 'encoding': 'F"     # Type3 with F encoding
    ]
    
    # All suspicious patterns combined
    all_suspicious_patterns = arial_narrow_patterns + identity_h_patterns + type3_patterns
    
    # REMOVED: All creator-based detection (too many false positives)
    
    print("\n🔍 Analyzing dataset PDFs...")
    
    for i, pdf_file in enumerate(dataset_pdf_files):  # Analyze all dataset PDFs
        pdf_id = pdf_file.replace('.pdf', '')
        pdf_path = PDF_FOLDER / pdf_file
        
        if i % 200 == 0:
            print(f"Progress: {i}/{len(dataset_pdf_files)}")
        
        # Extract metadata and fonts
        pdf_info = extract_pdf_metadata_and_fonts(pdf_path)
        pdffonts_output = get_pdffonts_info(pdf_path)
        
        # Check if this PDF has CID issues
        has_cid_issues = pdf_id in problematic_ids
        has_any_cids = pdf_id in all_cid_ids
        
        # EXPANDED FONT-ONLY DETECTION
        fonts_str = str(pdf_info.get('fonts', []))
        pdffonts_str = pdffonts_output
        
        # Check all suspicious patterns
        pattern_matches = []
        for pattern in all_suspicious_patterns:
            if pattern in fonts_str or pattern in pdffonts_str:
                pattern_matches.append(pattern)
        
        # Decision: suspicious if ANY pattern matches
        is_suspicious = len(pattern_matches) > 0
        
        # Track which patterns matched (for debugging)
        detection_reason = pattern_matches if pattern_matches else []
        
        # Track creators
        creator_key = pdf_info.get('creator', 'Unknown')
        if creator_key not in analysis['creators']:
            analysis['creators'][creator_key] = {
                'count': 0, 'cid_issues': 0, 'significant_issues': 0
            }
        analysis['creators'][creator_key]['count'] += 1
        if has_any_cids:
            analysis['creators'][creator_key]['cid_issues'] += 1
        if has_cid_issues:
            analysis['creators'][creator_key]['significant_issues'] += 1
        
        # Validation logic
        if has_cid_issues:
            analysis['problematic_pdfs_found'] += 1
            if is_suspicious:
                analysis['pattern_matches'] += 1
            else:
                analysis['pattern_misses'] += 1
        elif is_suspicious:
            analysis['false_positives'] += 1
        
        # Store detailed result
        result = {
            'pdf_id': pdf_id,
            'has_cid_issues': has_cid_issues,
            'has_any_cids': has_any_cids,
            'pattern_matches': pattern_matches,
            'detection_reason': detection_reason,
            'overall_suspicious': is_suspicious,
            'creator': pdf_info.get('creator', 'Unknown'),
            'fonts_sample': str(pdf_info.get('fonts', []))[:200],
            'pdffonts_sample': pdffonts_str[:200]
        }
        
        analysis['detailed_results'].append(result)
    
    # Print results
    print("\n" + "="*60)
    print("📈 VALIDATION RESULTS")
    print("="*60)
    
    total_analyzed = len(analysis['detailed_results'])
    print(f"Total PDFs analyzed: {total_analyzed}")
    print(f"Problematic PDFs found: {analysis['problematic_pdfs_found']}")
    print(f"Pattern matches: {analysis['pattern_matches']}")
    print(f"Pattern misses: {analysis['pattern_misses']}")
    print(f"False positives: {analysis['false_positives']}")
    
    if analysis['problematic_pdfs_found'] > 0:
        accuracy = (analysis['pattern_matches'] / analysis['problematic_pdfs_found']) * 100
        print(f"Detection accuracy: {accuracy:.1f}%")
    
    print(f"\n📊 TOP CREATORS BY CID ISSUES:")
    print("-" * 60)
    
    # Sort creators by CID issue rate
    creators_sorted = sorted(analysis['creators'].items(), 
                           key=lambda x: x[1]['significant_issues'], reverse=True)
    
    for creator, stats in creators_sorted[:10]:
        if stats['count'] > 0:
            cid_rate = (stats['significant_issues'] / stats['count']) * 100
            print(f"{creator[:40]:<40} | Count: {stats['count']:<3} | CID Issues: {stats['significant_issues']:<3} | Rate: {cid_rate:.1f}%")
    
    # Show examples of pattern matches and misses
    print(f"\n✅ SUCCESSFUL PATTERN MATCHES:")
    matches = [r for r in analysis['detailed_results'] 
              if r['has_cid_issues'] and r['overall_suspicious']][:5]
    for match in matches:
        print(f"  {match['pdf_id']} | Creator: {match['creator'][:30]}")
    
    print(f"\n❌ PATTERN MISSES (CID issues but not detected):")
    misses = [r for r in analysis['detailed_results'] 
             if r['has_cid_issues'] and not r['overall_suspicious']][:10]
    for miss in misses:
        print(f"  {miss['pdf_id']} | Creator: {miss['creator'][:40]}")
        print(f"    Fonts: {miss['fonts_sample'][:100]}")
        print(f"    pdffonts: {miss['pdffonts_sample'][:100]}")
    
    print(f"\n⚠️ FALSE POSITIVES (Detected as suspicious but no CID issues):")
    false_pos = [r for r in analysis['detailed_results'] 
                if not r['has_cid_issues'] and r['overall_suspicious']][:10]
    for fp in false_pos:
        print(f"  {fp['pdf_id']} | Creator: {fp['creator'][:30]} | Patterns: {fp['pattern_matches']}")
        print(f"    Fonts: {fp['fonts_sample'][:100]}")
    
    # Also test against ALL CID documents (not just significant ones)
    print(f"\n🔍 TESTING AGAINST ALL {len(all_cid_ids)} CID DOCUMENTS:")
    all_cid_matches = 0
    all_cid_misses = 0
    for result in analysis['detailed_results']:
        if result['has_any_cids']:  # Any CID issues (not just significant)
            if result['overall_suspicious']:
                all_cid_matches += 1
            else:
                all_cid_misses += 1
    
    if len(all_cid_ids) > 0:
        all_cid_accuracy = (all_cid_matches / len(all_cid_ids)) * 100
        print(f"Detection rate for ALL CID documents: {all_cid_accuracy:.1f}% ({all_cid_matches}/{len(all_cid_ids)})")
        print(f"Missed from ALL CID documents: {all_cid_misses}")
    
    # Ask user which target to optimize for
    print(f"\n❓ OPTIMIZATION TARGET:")
    print(f"Option A: Target 20 SIGNIFICANT CID issues (>5% corruption) - Current accuracy: {accuracy:.1f}%")
    print(f"Option B: Target ALL 41 CID documents (any CID) - Current accuracy: {all_cid_accuracy:.1f}%")
    
    # Save results
    output_file = Path(__file__).parent / 'detection_validation_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    return analysis

if __name__ == "__main__":
    validate_detection_patterns()