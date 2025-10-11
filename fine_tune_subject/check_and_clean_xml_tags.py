"""
Check and clean specific HTML tags from TXT files: <h1>, <h2>, <p>
These tags were added during special text extraction
"""
import os
import re
from pathlib import Path
from collections import Counter
from constants import TXT_FOLDER
from utils.colors.colors_terminal import Bcolors

def find_specific_tags(text):
    """Find specific HTML tags: h1, h2, p (opening and closing)"""
    # Only look for the specific tags we added during extraction
    tags_found = []
    
    # Check for each specific tag (opening and closing)
    specific_tags = ['h1', 'h2', 'p']
    
    for tag in specific_tags:
        # Opening tags like <h1>, <h2>, <p>
        opening_pattern = f'<{tag}[^>]*>'
        opening_matches = re.findall(opening_pattern, text)
        tags_found.extend(opening_matches)
        
        # Closing tags like </h1>, </h2>, </p>
        closing_pattern = f'</{tag}>'
        closing_matches = re.findall(closing_pattern, text)
        tags_found.extend(closing_matches)
    
    return tags_found

def analyze_txt_files_for_specific_tags():
    """Analyze TXT files for specific HTML tags: h1, h2, p"""
    print(f"{Bcolors.HEADER}=== Checking TXT Files for <h1>, <h2>, <p> Tags ==={Bcolors.ENDC}")
    
    if not TXT_FOLDER.exists():
        print(f"{Bcolors.FAIL}TXT_FOLDER not found: {TXT_FOLDER}{Bcolors.ENDC}")
        return
    
    txt_files = [f for f in os.listdir(TXT_FOLDER) if f.endswith('.txt')]
    print(f"{Bcolors.OKBLUE}Found {len(txt_files)} TXT files to check{Bcolors.ENDC}")
    
    files_with_tags = []
    files_without_tags = []
    tag_counts = Counter()
    sample_files = []
    
    for i, txt_file in enumerate(txt_files):
        if i % 1000 == 0:
            print(f"Processing {i:,}/{len(txt_files):,} files...")
        
        file_path = TXT_FOLDER / txt_file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find specific tags in this file
            tags_in_file = find_specific_tags(content)
            
            if tags_in_file:
                files_with_tags.append(txt_file)
                
                # Count tags
                for tag in tags_in_file:
                    tag_counts[tag] += 1
                
                # Keep first 3 files with tags for examples
                if len(sample_files) < 3:
                    sample_files.append((txt_file, content[:800]))  # First 800 chars
                    
            else:
                files_without_tags.append(txt_file)
                
        except Exception as e:
            print(f"Error reading {txt_file}: {e}")
            continue
    
    # Print results
    print(f"\n{Bcolors.HEADER}=== Analysis Results ==={Bcolors.ENDC}")
    print(f"Total TXT files checked: {len(txt_files):,}")
    print(f"{Bcolors.OKGREEN}Files WITHOUT <h1>, <h2>, <p> tags: {len(files_without_tags):,} ({len(files_without_tags)/len(txt_files)*100:.1f}%){Bcolors.ENDC}")
    print(f"{Bcolors.WARNING}Files WITH <h1>, <h2>, <p> tags: {len(files_with_tags):,} ({len(files_with_tags)/len(txt_files)*100:.1f}%){Bcolors.ENDC}")
    
    if files_with_tags:
        print(f"\n{Bcolors.HEADER}=== Tags Found ==={Bcolors.ENDC}")
        for tag, count in tag_counts.most_common():
            print(f"  {tag}: {count:,} occurrences")
        
        print(f"\n{Bcolors.HEADER}=== Examples of Files with Tags ==={Bcolors.ENDC}")
        for i, (filename, sample_content) in enumerate(sample_files):
            print(f"\n{Bcolors.OKBLUE}Example {i+1}: {filename}{Bcolors.ENDC}")
            print("Sample content:")
            print("-" * 60)
            print(sample_content)
            print("-" * 60)
    
    return files_with_tags, tag_counts

def clean_specific_tags(text):
    """Remove specific HTML tags: h1, h2, p"""
    # Remove <h1>, </h1>, <h2>, </h2>, <p>, </p>
    clean_text = text
    
    # Remove opening and closing tags for h1, h2, p
    specific_tags = ['h1', 'h2', 'p']
    
    for tag in specific_tags:
        # Remove opening tags (with any attributes)
        clean_text = re.sub(f'<{tag}[^>]*>', '', clean_text)
        # Remove closing tags
        clean_text = re.sub(f'</{tag}>', '', clean_text)
    
    # Clean up extra whitespaces and newlines
    clean_text = re.sub(r'\n\s*\n', '\n', clean_text)  # Multiple newlines to single
    clean_text = re.sub(r'[ \t]+', ' ', clean_text)    # Multiple spaces to single
    clean_text = clean_text.strip()
    
    return clean_text

def clean_files_with_specific_tags(files_with_tags):
    """Clean specific HTML tags from files"""
    print(f"\n{Bcolors.HEADER}=== Cleaning <h1>, <h2>, <p> Tags ==={Bcolors.ENDC}")
    
    # Create backup directory
    backup_dir = TXT_FOLDER.parent / "txt_backup_before_tag_cleanup"
    backup_dir.mkdir(exist_ok=True)
    print(f"{Bcolors.OKBLUE}Creating backups in: {backup_dir}{Bcolors.ENDC}")
    
    cleaned_count = 0
    error_count = 0
    
    for i, txt_file in enumerate(files_with_tags):
        if i % 100 == 0:
            print(f"Cleaning {i:,}/{len(files_with_tags):,} files...")
        
        file_path = TXT_FOLDER / txt_file
        
        try:
            # Read original content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Create backup
            backup_path = backup_dir / txt_file
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # Clean specific tags
            cleaned_content = clean_specific_tags(original_content)
            
            # Write cleaned content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            cleaned_count += 1
            
        except Exception as e:
            print(f"Error cleaning {txt_file}: {e}")
            error_count += 1
            continue
    
    print(f"\n{Bcolors.OKGREEN}Cleaning complete!{Bcolors.ENDC}")
    print(f"Successfully cleaned: {cleaned_count:,} files")
    if error_count > 0:
        print(f"{Bcolors.WARNING}Errors: {error_count:,} files{Bcolors.ENDC}")
    print(f"{Bcolors.OKBLUE}Backups saved to: {backup_dir}{Bcolors.ENDC}")

def main():
    """Main function"""
    print(f"{Bcolors.HEADER}=== Specific HTML Tag Checker (<h1>, <h2>, <p>) ==={Bcolors.ENDC}")
    
    # Step 1: Check for specific tags
    files_with_tags, tag_counts = analyze_txt_files_for_specific_tags()
    
    if not files_with_tags:
        print(f"\n{Bcolors.OKGREEN}Great! No <h1>, <h2>, or <p> tags found in any TXT files.{Bcolors.ENDC}")
        print(f"{Bcolors.OKGREEN}All files are clean and ready for training.{Bcolors.ENDC}")
        return
    
    # Step 2: Ask user if they want to clean
    print(f"\n{Bcolors.WARNING}Found {len(files_with_tags):,} files with <h1>, <h2>, or <p> tags.{Bcolors.ENDC}")
    print(f"{Bcolors.OKBLUE}Do you want to remove these specific tags?{Bcolors.ENDC}")
    
    while True:
        response = input(f"{Bcolors.OKBLUE}Clean tags? (y/n): {Bcolors.ENDC}").lower().strip()
        if response in ['y', 'yes']:
            clean_files_with_specific_tags(files_with_tags)
            print(f"\n{Bcolors.OKGREEN}Tag cleanup completed! Files are now ready for training.{Bcolors.ENDC}")
            break
        elif response in ['n', 'no']:
            print(f"{Bcolors.OKBLUE}Skipping cleanup. Files remain unchanged.{Bcolors.ENDC}")
            break
        else:
            print(f"{Bcolors.WARNING}Please enter 'y' or 'n'{Bcolors.ENDC}")

if __name__ == "__main__":
    main()