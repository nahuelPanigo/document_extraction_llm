"""
Script to balance dataset by downloading more PDFs for underrepresented classes
Target: 200 samples per class
"""
import pandas as pd
import os
from collections import Counter
from constants import TXT_FOLDER, CSV_FOLDER, CSV_FORD_SUBJECTS
from utils.colors.colors_terminal import Bcolors

def analyze_current_distribution():
    """Analyze current distribution from TXT files"""
    print(f"{Bcolors.HEADER}=== Analyzing Current Distribution ==={Bcolors.ENDC}")
    
    # Load FORD subjects CSV
    csv_path = CSV_FOLDER / CSV_FORD_SUBJECTS
    df = pd.read_csv(csv_path)
    
    # Create subject mapping
    subject_mapping = {}
    for _, row in df.iterrows():
        doc_id = str(row['id'])
        subject = row['subject']
        if pd.notna(subject) and subject:
            subject_mapping[doc_id] = subject
    
    print(f"{Bcolors.OKGREEN}Loaded {len(subject_mapping)} documents with subjects from CSV{Bcolors.ENDC}")
    
    # Get current TXT files
    if not TXT_FOLDER.exists():
        print(f"{Bcolors.FAIL}TXT_FOLDER not found: {TXT_FOLDER}{Bcolors.ENDC}")
        return {}, {}
    
    txt_files = [f for f in os.listdir(TXT_FOLDER) if f.endswith('.txt')]
    current_ids = [f.replace('.txt', '') for f in txt_files]
    
    print(f"{Bcolors.OKBLUE}Found {len(current_ids)} TXT files{Bcolors.ENDC}")
    
    # Map current IDs to subjects
    current_subjects = []
    current_id_to_subject = {}
    
    for doc_id in current_ids:
        if doc_id in subject_mapping:
            subject = subject_mapping[doc_id]
            current_subjects.append(subject)
            current_id_to_subject[doc_id] = subject
    
    # Count current distribution
    current_distribution = Counter(current_subjects)
    
    print(f"\n{Bcolors.OKGREEN}Current distribution:{Bcolors.ENDC}")
    for subject, count in current_distribution.most_common():
        print(f"  {subject}: {count}")
    
    return current_distribution, current_id_to_subject

def find_classes_needing_samples(current_distribution, target=200, min_threshold=50):
    """Find classes that need more samples to reach target (filter out classes with < min_threshold)"""
    print(f"\n{Bcolors.HEADER}=== Classes Needing More Samples (target: {target}, min: {min_threshold}) ==={Bcolors.ENDC}")
    
    classes_needing_samples = {}
    filtered_classes = []
    
    for subject, current_count in current_distribution.items():
        if current_count < min_threshold:
            filtered_classes.append(subject)
            print(f"  {Bcolors.WARNING}FILTERED OUT: {subject} ({current_count} < {min_threshold}){Bcolors.ENDC}")
        elif current_count < target:
            needed = target - current_count
            classes_needing_samples[subject] = needed
            print(f"  {subject}: {current_count} -> needs {needed} more")
    
    if filtered_classes:
        print(f"\n{Bcolors.WARNING}Filtered out {len(filtered_classes)} classes with < {min_threshold} documents{Bcolors.ENDC}")
    
    print(f"\n{Bcolors.OKBLUE}Total classes needing samples: {len(classes_needing_samples)}{Bcolors.ENDC}")
    
    return classes_needing_samples

def find_additional_ids(classes_needing_samples, current_id_to_subject):
    """Find additional IDs from CSV for each class that needs more samples"""
    print(f"\n{Bcolors.HEADER}=== Finding Additional IDs from CSV ==={Bcolors.ENDC}")
    
    # Load FORD subjects CSV
    csv_path = CSV_FOLDER / CSV_FORD_SUBJECTS
    df = pd.read_csv(csv_path)
    
    # Get current IDs (already have TXT files)
    current_ids = set(current_id_to_subject.keys())
    
    # Group by subject
    subject_to_all_ids = {}
    for _, row in df.iterrows():
        doc_id = str(row['id'])
        subject = row['subject']
        
        if pd.notna(subject) and subject:
            if subject not in subject_to_all_ids:
                subject_to_all_ids[subject] = []
            subject_to_all_ids[subject].append(doc_id)
    
    # Find additional IDs needed for each class
    additional_ids_needed = {}
    
    for subject, needed_count in classes_needing_samples.items():
        if subject in subject_to_all_ids:
            all_ids_for_subject = subject_to_all_ids[subject]
            # Get IDs we don't have yet
            available_ids = [id for id in all_ids_for_subject if id not in current_ids]
            
            # Take what we need (up to what's available)
            ids_to_download = available_ids[:needed_count]
            additional_ids_needed[subject] = ids_to_download
            
            print(f"  {subject}:")
            print(f"    Need: {needed_count}")
            print(f"    Available: {len(available_ids)}")
            print(f"    Will download: {len(ids_to_download)}")
            
            if len(ids_to_download) < needed_count:
                print(f"    {Bcolors.WARNING}WARNING: Not enough available IDs for {subject}{Bcolors.ENDC}")
        else:
            print(f"  {Bcolors.FAIL}Subject not found in CSV: {subject}{Bcolors.ENDC}")
            additional_ids_needed[subject] = []
    
    return additional_ids_needed

def save_download_list(additional_ids_needed):
    """Save the list of IDs to download"""
    print(f"\n{Bcolors.HEADER}=== Saving Download Lists ==={Bcolors.ENDC}")
    
    # Create output directory
    output_dir = CSV_FOLDER / "balance_downloads"
    output_dir.mkdir(exist_ok=True)
    
    # Save summary
    summary_data = []
    all_ids_to_download = []
    
    for subject, ids in additional_ids_needed.items():
        summary_data.append({
            'subject': subject,
            'ids_to_download': len(ids),
            'ids_list': ','.join(ids)
        })
        all_ids_to_download.extend(ids)
    
    # Save summary CSV
    summary_df = pd.DataFrame(summary_data)
    summary_path = output_dir / "download_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    
    # Save all IDs to download (one per line)
    all_ids_path = output_dir / "all_ids_to_download.txt"
    with open(all_ids_path, 'w') as f:
        for id in all_ids_to_download:
            f.write(f"{id}\n")
    
    print(f"{Bcolors.OKGREEN}Saved download summary to: {summary_path}{Bcolors.ENDC}")
    print(f"{Bcolors.OKGREEN}Saved all IDs to download to: {all_ids_path}{Bcolors.ENDC}")
    print(f"{Bcolors.OKBLUE}Total IDs to download: {len(all_ids_to_download)}{Bcolors.ENDC}")
    
    return all_ids_to_download

def main():
    """Main function to balance the dataset"""
    print(f"{Bcolors.HEADER}=== Dataset Balancing Tool ==={Bcolors.ENDC}")
    
    # Step 1: Analyze current distribution
    current_distribution, current_id_to_subject = analyze_current_distribution()
    
    if not current_distribution:
        print(f"{Bcolors.FAIL}No valid data found!{Bcolors.ENDC}")
        return
    
    # Step 2: Find classes needing more samples
    classes_needing_samples = find_classes_needing_samples(current_distribution, target=200)
    
    if not classes_needing_samples:
        print(f"{Bcolors.OKGREEN}All classes already have 200+ samples!{Bcolors.ENDC}")
        return
    
    # Step 3: Find additional IDs
    additional_ids_needed = find_additional_ids(classes_needing_samples, current_id_to_subject)
    
    # Step 4: Save download lists
    all_ids_to_download = save_download_list(additional_ids_needed)
    
    print(f"\n{Bcolors.OKGREEN}Balancing analysis complete!{Bcolors.ENDC}")
    print(f"{Bcolors.OKBLUE}Next step: Use the generated download list to fetch PDFs{Bcolors.ENDC}")

if __name__ == "__main__":
    main()