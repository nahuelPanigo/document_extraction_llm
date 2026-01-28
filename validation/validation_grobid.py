import os
import requests
import json
import re
from pathlib import Path
import sys
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).resolve().parents[1]))

from constants import RESULT_FOLDER_VALIDATION, PDF_FOLDER, GROBID_SERVICE, GROBID_FOLDER
from utils.text_extraction.read_and_write_files import read_data_json, write_to_json

def create_grobid_folder():
    """Create GROBID folder if it doesn't exist"""
    GROBID_FOLDER.mkdir(parents=True, exist_ok=True)

def send_pdf_to_grobid(pdf_path):
    """Send PDF to Grobid service and get TEI XML response"""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            files = {'input': pdf_file}
            response = requests.post(
                f"{GROBID_SERVICE}/api/processFulltextDocument",
                files=files
            )
            
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error processing {pdf_path}: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error sending {pdf_path} to Grobid: {str(e)}")
        return None

def save_xml_file(xml_content, doc_id):
    """Save XML content to file"""
    if xml_content:
        xml_filename = GROBID_FOLDER / f"{doc_id}.xml"
        with open(xml_filename, 'w', encoding='utf-8') as xml_file:
            xml_file.write(xml_content)
        print(f"Saved XML for document {doc_id}")
        return True
    return False

def extract_text_around_keyword(text, keyword, max_chars=100):
    """Extract text around a keyword for better context-based extraction"""
    try:
        keyword_pos = text.lower().find(keyword.lower())
        if keyword_pos != -1:
            start = max(0, keyword_pos - 20)
            end = min(len(text), keyword_pos + max_chars)
            return text[start:end]
    except:
        pass
    return ""

def extract_general_metadata(soup, doc_id):
    """Extract common metadata fields present in all document types"""
    metadata = {"id": doc_id}
    
    # Extract title
    try:
        title_elem = soup.find('title', attrs={'level': 'a', 'type': 'main'})
        if title_elem:
            title = title_elem.get_text(strip=True)
            if title and title != "Esta obra está bajo una Licencia Creative Commons":
                metadata["title"] = title
    except Exception as e:
        print(f"Error extracting title from {doc_id}: {e}")
    
    # Extract authors (all types as authors)
    try:
        authors = []
        author_elements = soup.find_all('author')
        
        for author in author_elements:
            persname = author.find('persName')
            if persname:
                surname = persname.find('surname')
                forename = persname.find('forename')
                
                author_name = ""
                if surname:
                    author_name = surname.get_text(strip=True)
                if forename:
                    fname = forename.get_text(strip=True)
                    if author_name:
                        author_name = f"{author_name}, {fname}"
                    else:
                        author_name = fname
                
                if author_name and author_name not in ["Internacional", "Google Maps", "Api"]:
                    authors.append(author_name)
        
        if authors:
            metadata["creator"] = authors if len(authors) > 1 else authors[0]
    except Exception as e:
        print(f"Error extracting authors from {doc_id}: {e}")
    
    # Extract abstract
    try:
        abstract_elem = soup.find('abstract')
        if abstract_elem:
            abstract_text = ""
            paragraphs = abstract_elem.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    abstract_text += text + " "
            
            if abstract_text.strip():
                metadata["abstract"] = abstract_text.strip()
    except Exception as e:
        print(f"Error extracting abstract from {doc_id}: {e}")
    
    # Extract keywords
    try:
        keywords_text = ""
        abstract_elem = soup.find('abstract')
        if abstract_elem:
            keyword_divs = abstract_elem.find_all('div')
            for div in keyword_divs:
                head = div.find('head')
                if head and ('palabra' in head.get_text().lower() or 'keyword' in head.get_text().lower()):
                    p = div.find('p')
                    if p:
                        keywords_text = p.get_text(strip=True)
                        break
        
        if keywords_text:
            keywords_text = keywords_text.replace('Palabras clave', '').replace('Keywords', '').strip()
            keywords = [kw.strip() for kw in re.split(r'[,-]', keywords_text) if kw.strip()]
            if keywords:
                metadata["keywords"] = keywords
    except Exception as e:
        print(f"Error extracting keywords from {doc_id}: {e}")
    
    # Extract language
    try:
        tei_header = soup.find('teiHeader')
        if tei_header and tei_header.get('xml:lang'):
            metadata["language"] = tei_header.get('xml:lang')
        else:
            text_elem = soup.find('text')
            if text_elem and text_elem.get('xml:lang'):
                metadata["language"] = text_elem.get('xml:lang')
    except Exception as e:
        print(f"Error extracting language from {doc_id}: {e}")
    
    # Extract organization/institution
    try:
        org_names = []
        affiliations = soup.find_all('affiliation')
        for aff in affiliations:
            org_elements = aff.find_all('orgName')
            for org in org_elements:
                org_text = org.get_text(strip=True)
                if org_text and len(org_text) > 5:
                    org_names.append(org_text)
        
        if org_names:
            metadata["originPlaceInfo"] = org_names[0]
    except Exception as e:
        print(f"Error extracting organization from {doc_id}: {e}")
    
    return metadata

def extract_by_keyword_search(soup, doc_id):
    """Extract metadata using keyword-based search in the full text"""
    metadata = {}
    full_text = soup.get_text()
    
    # Extract ISSN by finding the word "ISSN"
    try:
        issn_context = extract_text_around_keyword(full_text, "ISSN", 50)
        if issn_context:
            issn_pattern = r'(\d{4}-\d{3}[\dX])'
            issn_match = re.search(issn_pattern, issn_context)
            if issn_match:
                metadata["issn"] = issn_match.group(1)
    except Exception as e:
        print(f"Error extracting ISSN from {doc_id}: {e}")
    
    # Extract ISBN by finding the word "ISBN"
    try:
        isbn_context = extract_text_around_keyword(full_text, "ISBN", 50)
        if isbn_context:
            isbn_pattern = r'(\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-[\dX])'
            isbn_match = re.search(isbn_pattern, isbn_context)
            if isbn_match:
                metadata["isbn"] = isbn_match.group(1)
    except Exception as e:
        print(f"Error extracting ISBN from {doc_id}: {e}")
    
    # Extract Volume information
    try:
        vol_context = extract_text_around_keyword(full_text, "Vol", 30)
        if vol_context:
            vol_pattern = r'Vol\.?\s*(\d+)'
            vol_match = re.search(vol_pattern, vol_context, re.IGNORECASE)
            if vol_match:
                metadata["journalVolumeAndIssue"] = f"Vol. {vol_match.group(1)}"
    except Exception as e:
        print(f"Error extracting volume from {doc_id}: {e}")
    
    # Extract Event information
    try:
        event_keywords = ["Congreso", "Conference", "Simposio", "Symposium", "Reunión", "Meeting"]
        for keyword in event_keywords:
            event_context = extract_text_around_keyword(full_text, keyword, 200)
            if event_context:
                metadata["event"] = event_context.strip()
                break
    except Exception as e:
        print(f"Error extracting event from {doc_id}: {e}")
    
    # Extract Compiler/Editor
    try:
        compiler_keywords = ["Compilador", "Compiler", "Compilado por"]
        for keyword in compiler_keywords:
            comp_context = extract_text_around_keyword(full_text, keyword, 100)
            if comp_context:
                metadata["compiler"] = comp_context.strip()
                break
                
        editor_keywords = ["Editor", "Editado por", "Ed."]
        for keyword in editor_keywords:
            ed_context = extract_text_around_keyword(full_text, keyword, 100)
            if ed_context:
                metadata["editor"] = ed_context.strip()
                break
    except Exception as e:
        print(f"Error extracting compiler/editor from {doc_id}: {e}")
    
    return metadata

def extract_tesis_metadata(soup, doc_id):
    """Extract metadata specific to thesis documents"""
    metadata = {}
    full_text = soup.get_text()
    
    # Extract director/codirector (search for these terms)
    try:
        director_keywords = ["Director", "Directora", "Dir.", "Dirigido por"]
        for keyword in director_keywords:
            dir_context = extract_text_around_keyword(full_text, keyword, 100)
            if dir_context:
                metadata["director"] = dir_context.strip()
                break
                
        codirector_keywords = ["Codirector", "Codirectora", "Co-director"]
        for keyword in codirector_keywords:
            codir_context = extract_text_around_keyword(full_text, keyword, 100)
            if codir_context:
                metadata["codirector"] = codir_context.strip()
                break
    except Exception as e:
        print(f"Error extracting director info from {doc_id}: {e}")
    
    # Extract degree information
    try:
        degree_keywords = ["Grado", "Degree", "Título", "Carrera"]
        for keyword in degree_keywords:
            degree_context = extract_text_around_keyword(full_text, keyword, 100)
            if degree_context:
                metadata["degree.name"] = degree_context.strip()
                break
                
        grantor_keywords = ["Universidad", "University", "Facultad", "Institute"]
        for keyword in grantor_keywords:
            grantor_context = extract_text_around_keyword(full_text, keyword, 100)
            if grantor_context:
                metadata["degree.grantor"] = grantor_context.strip()
                break
    except Exception as e:
        print(f"Error extracting degree info from {doc_id}: {e}")
    
    return metadata

def extract_articulo_metadata(soup, doc_id):
    """Extract metadata specific to article documents"""
    metadata = {}
    
    # Extract journal title
    try:
        monogr = soup.find('monogr')
        if monogr:
            title_elem = monogr.find('title', attrs={'level': 'j'})
            if title_elem:
                journal_title = title_elem.get_text(strip=True)
                if journal_title:
                    metadata["journalTitle"] = journal_title
    except Exception as e:
        print(f"Error extracting journal title from {doc_id}: {e}")
    
    return metadata

def extract_libro_metadata(soup, doc_id):
    """Extract metadata specific to book documents"""
    metadata = {}
    full_text = soup.get_text()
    
    # Extract publisher
    try:
        publisher_keywords = ["Editorial", "Publisher", "Publicado por", "Press"]
        for keyword in publisher_keywords:
            pub_context = extract_text_around_keyword(full_text, keyword, 100)
            if pub_context:
                metadata["publisher"] = pub_context.strip()
                break
    except Exception as e:
        print(f"Error extracting publisher from {doc_id}: {e}")
    
    return metadata

def extract_metadata_from_xml(xml_path, doc_id, doc_type="general"):
    """Extract metadata from Grobid XML using type-specific strategies"""
    try:
        with open(xml_path, 'r', encoding='utf-8') as xml_file:
            xml_content = xml_file.read()
        
        soup = BeautifulSoup(xml_content, 'xml')
        
        # Start with general metadata
        metadata = extract_general_metadata(soup, doc_id)
        
        # Add keyword-based extraction
        keyword_metadata = extract_by_keyword_search(soup, doc_id)
        metadata.update(keyword_metadata)
        
        # Apply type-specific extraction
        if doc_type == "tesis":
            tesis_metadata = extract_tesis_metadata(soup, doc_id)
            metadata.update(tesis_metadata)
        elif doc_type == "articulo" or doc_type == "objeto_conferencia":
            articulo_metadata = extract_articulo_metadata(soup, doc_id)
            metadata.update(articulo_metadata)
        elif doc_type == "libro":
            libro_metadata = extract_libro_metadata(soup, doc_id)
            metadata.update(libro_metadata)
        
        print(f"✅ Extracted {len(metadata) - 1} metadata fields from {doc_id} (type: {doc_type})")
        return metadata
        
    except Exception as e:
        print(f"❌ Error processing XML for {doc_id}: {str(e)}")
        return {"id": doc_id, "error": str(e)}

def extract_metadata_from_xmls(data):
    """
    Extract metadata from all XML files in GROBID folder
    
    Args:
        data: Dictionary with document data including metadata
        
    Returns:
        Dictionary with extracted metadata for all documents
    """
    print("\n🔍 Starting XML metadata extraction...")
    extracted_metadata = {}
    
    # Get all XML files in GROBID folder
    xml_files = list(GROBID_FOLDER.glob("*.xml"))
    print(f"Found {len(xml_files)} XML files to process")
    
    for xml_file in xml_files:
        doc_id = xml_file.stem  # Get filename without extension
        
        # Get document type from original metadata if available
        doc_type = "general"
        if doc_id in data and "dc.type" in data[doc_id]:
            original_type = data[doc_id]["dc.type"].lower()
            if "tesis" in original_type:
                doc_type = "tesis"
            elif "articulo" in original_type:
                doc_type = "articulo"
            elif "libro" in original_type:
                doc_type = "libro"
            elif "conferencia" in original_type:
                doc_type = "objeto_conferencia"
        
        print(f"Processing {doc_id} as {doc_type}...")
        
        # Extract metadata from XML
        metadata = extract_metadata_from_xml(xml_file, doc_id, doc_type)
        extracted_metadata[doc_id] = metadata
    
    # Save results
    results_file = GROBID_FOLDER / "extracted_metadata.json"
    try:
        write_to_json(results_file, extracted_metadata, 'utf-8')
        print(f"💾 Metadata extraction results saved to: {results_file}")
    except Exception as e:
        print(f"❌ Error saving results: {str(e)}")
    
    print(f"\n✅ XML metadata extraction completed!")
    print(f"📊 Processed {len(extracted_metadata)} documents")
    
    return extracted_metadata

def main():
    # Create GROBID folder
    create_grobid_folder()
    
    # Read JSON file
    json_file_path = RESULT_FOLDER_VALIDATION / "result_test_original_metadata-with-object-conference1.json"
    
    try:
        data = read_data_json(json_file_path, 'utf-8')
    except Exception as e:
        print(f"Error reading JSON file: {str(e)}")
        return
    
    if not data:
        print("No data found in JSON file")
        return
    
    print(f"📋 Processing {len(data)} documents...")
    
    # Process each document
    for doc_id, metadata in data.items():
        if not doc_id:
            continue
            
        # Construct PDF filename
        pdf_filename = f"{doc_id}.pdf"
        pdf_path = PDF_FOLDER / pdf_filename
        
        if not pdf_path.exists():
            print(f"PDF file not found: {pdf_path}")
            continue
        
        # Check if XML already exists
        xml_filename = GROBID_FOLDER / f"{doc_id}.xml"
        
        if xml_filename.exists():
            print(f"✓ XML already exists for document {doc_id}, skipping Grobid processing")
        else:
            print(f"Processing document {doc_id} with Grobid...")
            
            # Send PDF to Grobid service
            xml_content = send_pdf_to_grobid(pdf_path)
            
            # Save XML to GROBID folder
            save_xml_file(xml_content, doc_id)
    
    # Extract metadata from all XMLs
    print("\n" + "="*60)
    extracted_metadata = extract_metadata_from_xmls(data)
    
    print(f"\n🎉 Processing completed!")
    print(f"📊 Total documents processed: {len(extracted_metadata)}")

if __name__ == "__main__":
    main()