"""
Convert PDFs to TXT files using the extractor API service
Processes all PDFs in PDF_FOLDER and saves TXT files in TXT_FOLDER
"""
import os
import sys
from pathlib import Path
from constants import PDF_FOLDER, TXT_FOLDER

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.consume_apis.consume_extractor import make_requests_only_text
from utils.colors.colors_terminal import Bcolors

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# API Configuration from environment
EXTRACTOR_TOKEN = os.getenv("EXTRACTOR_TOKEN")
EXTRACTOR_URL = os.getenv("EXTRACTOR_URL", "http://localhost:8001")

def get_pdfs_to_convert():
    """Get list of PDFs that need to be converted to TXT"""
    if not PDF_FOLDER.exists():
        print(f"{Bcolors.FAIL}PDF_FOLDER not found: {PDF_FOLDER}{Bcolors.ENDC}")
        return []
    
    # Get all PDF files
    pdf_files = [f for f in PDF_FOLDER.iterdir() if f.suffix.lower() == '.pdf']
    
    # Create TXT_FOLDER if it doesn't exist
    TXT_FOLDER.mkdir(parents=True, exist_ok=True)
    
    # Filter out PDFs that already have corresponding TXT files
    pdfs_to_convert = []
    
    for pdf_file in pdf_files:
        txt_file = TXT_FOLDER / f"{pdf_file.stem}.txt"
        if not txt_file.exists():
            pdfs_to_convert.append(pdf_file)
    
    print(f"{Bcolors.OKGREEN}Found {len(pdf_files)} PDF files{Bcolors.ENDC}")
    print(f"{Bcolors.OKBLUE}Already converted: {len(pdf_files) - len(pdfs_to_convert)}{Bcolors.ENDC}")
    print(f"{Bcolors.OKBLUE}Need to convert: {len(pdfs_to_convert)}{Bcolors.ENDC}")
    
    return pdfs_to_convert

def convert_pdf_to_txt(pdf_path, normalization=True):
    """Convert a single PDF to TXT using the extractor API"""
    try:
        print(f"Converting: {pdf_path.name}")
        
        # Call the API
        response_text = make_requests_only_text(
            file_path=pdf_path,
            token=EXTRACTOR_TOKEN,
            normalization=normalization,
            host_url=EXTRACTOR_URL
        )
        
        # Save the extracted text
        txt_path = TXT_FOLDER / f"{pdf_path.stem}.txt"
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(response_text)
        
        print(f"{Bcolors.OKGREEN}✓ Converted: {pdf_path.name} -> {txt_path.name}{Bcolors.ENDC}")
        return True
        
    except Exception as e:
        print(f"{Bcolors.FAIL}✗ Error converting {pdf_path.name}: {e}{Bcolors.ENDC}")
        return False

def test_api_connection():
    """Test if the extractor API service is running"""
    import requests
    
    if not EXTRACTOR_TOKEN:
        print(f"{Bcolors.FAIL}✗ EXTRACTOR_TOKEN not found in environment variables{Bcolors.ENDC}")
        return False
    
    try:
        response = requests.get(f"{EXTRACTOR_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"{Bcolors.OKGREEN}✓ Extractor API service is running at {EXTRACTOR_URL}{Bcolors.ENDC}")
            return True
        else:
            print(f"{Bcolors.FAIL}✗ Extractor API service returned status {response.status_code}{Bcolors.ENDC}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"{Bcolors.FAIL}✗ Cannot connect to extractor API service at {EXTRACTOR_URL}: {e}{Bcolors.ENDC}")
        print(f"{Bcolors.WARNING}Make sure the service is running on port 8001{Bcolors.ENDC}")
        return False

def show_conversion_progress():
    """Show progress of PDF to TXT conversion"""
    if not PDF_FOLDER.exists() or not TXT_FOLDER.exists():
        print(f"{Bcolors.WARNING}Folders don't exist yet{Bcolors.ENDC}")
        return
    
    pdf_files = list(PDF_FOLDER.glob("*.pdf"))
    txt_files = list(TXT_FOLDER.glob("*.txt"))
    
    pdf_ids = {f.stem for f in pdf_files}
    txt_ids = {f.stem for f in txt_files}
    
    converted = len(txt_ids)
    total = len(pdf_ids)
    remaining = total - converted
    
    print(f"\n{Bcolors.HEADER}=== Conversion Progress ==={Bcolors.ENDC}")
    print(f"Total PDFs: {total}")
    print(f"Converted: {converted}")
    print(f"Remaining: {remaining}")
    
    if total > 0:
        progress = (converted / total) * 100
        print(f"Progress: {progress:.1f}%")

def main():
    """Main function to convert PDFs to TXT"""
    print(f"{Bcolors.HEADER}=== PDF to TXT Converter ==={Bcolors.ENDC}")
    print(f"Using extractor API at: {EXTRACTOR_URL}")
    print(f"PDF folder: {PDF_FOLDER}")
    print(f"TXT folder: {TXT_FOLDER}")
    
    # Show current progress
    show_conversion_progress()
    
    # Test API connection
    if not test_api_connection():
        print(f"\n{Bcolors.FAIL}Cannot proceed without API service!{Bcolors.ENDC}")
        print(f"{Bcolors.WARNING}To start the extractor service:{Bcolors.ENDC}")
        print(f"  cd /home/nahuel/Documents/tesis/api/app/extractor_service")
        print(f"  ./run_extractor_temp.sh")
        return
    
    # Get PDFs to convert
    pdfs_to_convert = get_pdfs_to_convert()
    
    if not pdfs_to_convert:
        print(f"{Bcolors.OKGREEN}All PDFs already converted!{Bcolors.ENDC}")
        return
    
    # Confirm conversion
    print(f"\n{Bcolors.WARNING}About to convert {len(pdfs_to_convert)} PDF files to TXT.{Bcolors.ENDC}")
    response = input("Continue? (y/N): ")
    
    if response.lower() not in ['y', 'yes']:
        print(f"{Bcolors.OKBLUE}Conversion cancelled.{Bcolors.ENDC}")
        return
    
    # Convert files
    print(f"\n{Bcolors.HEADER}=== Starting Conversion ==={Bcolors.ENDC}")
    
    successful = 0
    failed = 0
    
    for i, pdf_path in enumerate(pdfs_to_convert, 1):
        print(f"\n{Bcolors.HEADER}[{i}/{len(pdfs_to_convert)}]{Bcolors.ENDC}")
        
        if convert_pdf_to_txt(pdf_path):
            successful += 1
        else:
            failed += 1
    
    # Show final results
    print(f"\n{Bcolors.HEADER}=== Conversion Summary ==={Bcolors.ENDC}")
    print(f"{Bcolors.OKGREEN}Successful: {successful}{Bcolors.ENDC}")
    print(f"{Bcolors.FAIL}Failed: {failed}{Bcolors.ENDC}")
    print(f"{Bcolors.OKBLUE}Total processed: {len(pdfs_to_convert)}{Bcolors.ENDC}")
    
    # Show final progress
    show_conversion_progress()

if __name__ == "__main__":
    main()