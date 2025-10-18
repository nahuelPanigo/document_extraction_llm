import requests
from pathlib import Path
import os
from utils.text_extraction.read_and_write_files import read_data_json,write_to_json
from utils.consume_apis.consume_orchestrator import upload_file
from constants import URL_SERVICES_EXTRACTION,PDF_FOLDER,JSON_FOLDER,RESULT_FOLDER_VALIDATION,DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED,SUBJECT_MODEL_FOLDERS
import time
from dotenv import load_dotenv
import joblib



unused_fields = ["dc.uri","sedici.uri","keywords","original_text"]


def remove_unused_fields(data):
    final_data = {}
    for inner_dict in data:
        cleaned_dict = {k: v for k, v in inner_dict.items() if k not in unused_fields}
        final_data[inner_dict["id"]] = cleaned_dict
    return final_data

def load_svm_model():
    """Load SVM model for subject prediction"""
    try:
        model_folder = SUBJECT_MODEL_FOLDERS["svm_linear"]
        classifier = joblib.load(model_folder / 'svm_classifier.pkl')
        vectorizer = joblib.load(model_folder / 'svm_vectorizer.pkl') 
        label_encoder = joblib.load(model_folder / 'svm_label_encoder.pkl')
        print("✅ SVM model loaded successfully!")
        return classifier, vectorizer, label_encoder
    except Exception as e:
        print(f"❌ Error loading SVM model: {e}")
        return None, None, None

def predict_subject_svm(text, classifier, vectorizer, label_encoder):
    """Predict subject using SVM model"""
    if not all([classifier, vectorizer, label_encoder]):
        return None
    try:
        text_features = vectorizer.transform([text])
        prediction_encoded = classifier.predict(text_features)[0]
        predicted_subject = label_encoder.inverse_transform([prediction_encoded])[0]
        return predicted_subject
    except Exception as e:
        print(f"❌ Error predicting subject: {e}")
        return None


def download_pdf(id):
    host_url="http://192.168.100.15:9000"
    final_url = f"{host_url}/{id}.pdf"
    
    try:
        response = requests.get(final_url)
        if response.status_code == 200:
            pdf_path = PDF_FOLDER / f"{id}.pdf"
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Downloaded: {id}.pdf")
            return pdf_path
        else:
            print(f"❌ Failed to download {id}.pdf - Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error downloading {id}.pdf: {e}")
        return None



load_dotenv()

# Load SVM model once at startup
print("🔄 Loading SVM model...")
svm_classifier, svm_vectorizer, svm_label_encoder = load_svm_model()

original_metadata = {}
final_dict_deepanalyze = {}
final_dict = {}
svm_predictions = {}
comparison_results = {}
times_with_deepanalyze = []
times = []

metadatas = read_data_json(JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED,"utf-8")
validation_original_metadata = remove_unused_fields(metadatas["validation"][:50])


for id, metadata in validation_original_metadata.items():
    filename = PDF_FOLDER / f"{id}.pdf"
    
    # Download PDF only if it doesn't exist
    if not filename.exists():
        print(f"📥 Downloading {id}.pdf...")
        download_pdf(id)
    else:
        print(f"✅ PDF already exists: {id}.pdf")
    
    print(f"🔄 Processing ID: {id}")
    # Get original text for SVM prediction
    original_text = None
    for item in metadatas["validation"][:50]:
        if item["id"] == id and "original_text" in item:
            original_text = item["original_text"]
            break
    
    # Predict subject using SVM model
    svm_subject = None
    if original_text and svm_classifier:
        svm_subject = predict_subject_svm(original_text, svm_classifier, svm_vectorizer, svm_label_encoder)
        svm_predictions[id] = svm_subject
        print(f"🤖 SVM predicted subject: {svm_subject}")
    
    # Call fine-tuned metadata extraction
    try:
        response = upload_file(filename, os.getenv("ORCHESTRATOR_TOKEN"), True, "None", deepanalyze=False, host_url="http://192.168.100.15:8000")
        if response["error"] is None:
            extracted_data = response["data"]
            final_dict[id] = extracted_data
            
            # Extract subject from fine-tuned response
            finetune_subject = extracted_data.get("subject", None)
            print(f"🎯 Fine-tune extracted subject: {finetune_subject}")
            
            # Compare results
            original_subject = metadata.get("subject", None)
            comparison_results[id] = {
                "original_subject": original_subject,
                "svm_prediction": svm_subject,
                "finetune_extraction": finetune_subject,
                "svm_vs_original": svm_subject == original_subject if svm_subject and original_subject else None,
                "finetune_vs_original": finetune_subject == original_subject if finetune_subject and original_subject else None,
                "svm_vs_finetune": svm_subject == finetune_subject if svm_subject and finetune_subject else None
            }
            
            print(f"📊 Original: {original_subject}")
            print(f"🎯 Comparison - SVM correct: {comparison_results[id]['svm_vs_original']}")
            print(f"🎯 Comparison - Fine-tune correct: {comparison_results[id]['finetune_vs_original']}")
            print(f"🎯 Comparison - SVM vs Fine-tune match: {comparison_results[id]['svm_vs_finetune']}")
            
            # Save progress
            write_to_json(RESULT_FOLDER_VALIDATION / "results-object-conference.json", final_dict, "utf-8")
            write_to_json(RESULT_FOLDER_VALIDATION / "svm_predictions.json", svm_predictions, "utf-8")
            write_to_json(RESULT_FOLDER_VALIDATION / "subject_comparison_results.json", comparison_results, "utf-8")
            
    except Exception as e:
        print(f"❌ Problem with ID {id}: {e}")

# Save final results
write_to_json(RESULT_FOLDER_VALIDATION / "result_test_original_metadata-with-object-conference.json", validation_original_metadata, "utf-8")

# Print summary
print(f"\n📈 SUMMARY RESULTS:")
print(f"Total processed: {len(comparison_results)}")

svm_correct = sum(1 for r in comparison_results.values() if r['svm_vs_original'] == True)
finetune_correct = sum(1 for r in comparison_results.values() if r['finetune_vs_original'] == True)
both_correct = sum(1 for r in comparison_results.values() if r['svm_vs_original'] == True and r['finetune_vs_original'] == True)
agreement = sum(1 for r in comparison_results.values() if r['svm_vs_finetune'] == True)

if len(comparison_results) > 0:
    print(f"🤖 SVM correct: {svm_correct}/{len(comparison_results)} ({svm_correct/len(comparison_results)*100:.1f}%)")
    print(f"🎯 Fine-tune correct: {finetune_correct}/{len(comparison_results)} ({finetune_correct/len(comparison_results)*100:.1f}%)")
    print(f"✅ Both correct: {both_correct}/{len(comparison_results)} ({both_correct/len(comparison_results)*100:.1f}%)")
    print(f"🤝 SVM vs Fine-tune agreement: {agreement}/{len(comparison_results)} ({agreement/len(comparison_results)*100:.1f}%)")
else:
    print("❌ No results to analyze - all processing failed")