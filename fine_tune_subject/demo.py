"""
Simple Demo for Subject Classification
Test the trained model on new text
"""
import joblib
from utils.colors.colors_terminal import Bcolors
from constants import TXT_FOLDER
import os
import random

def load_models():
    """Load trained models"""
    try:
        models = {
            'classifier': joblib.load('subject_classifier.pkl'),
            'vectorizer': joblib.load('vectorizer.pkl'),
            'label_encoder': joblib.load('label_encoder.pkl')
        }
        print(f"{Bcolors.OKGREEN}Models loaded successfully!{Bcolors.ENDC}")
        return models
    except FileNotFoundError as e:
        print(f"{Bcolors.FAIL}Models not found: {e}{Bcolors.ENDC}")
        print(f"{Bcolors.WARNING}Run train.py first!{Bcolors.ENDC}")
        return None

def preprocess_text(text):
    """Same preprocessing as training"""
    if not text:
        return ""
    return " ".join(text.split()).lower()

def predict_subject(text, models):
    """Predict subject for text"""
    processed_text = preprocess_text(text)
    X = models['vectorizer'].transform([processed_text])
    prediction = models['classifier'].predict(X)[0]
    subject = models['label_encoder'].inverse_transform([prediction])[0]
    
    # Get confidence
    probabilities = models['classifier'].predict_proba(X)[0]
    confidence = max(probabilities)
    
    return subject, confidence

def test_random_documents(models, num_tests=5):
    """Test on random txt files"""
    if not TXT_FOLDER.exists():
        print(f"{Bcolors.FAIL}TXT_FOLDER not found{Bcolors.ENDC}")
        return
    
    txt_files = [f for f in os.listdir(TXT_FOLDER) if f.endswith('.txt')]
    if not txt_files:
        print(f"{Bcolors.FAIL}No txt files found{Bcolors.ENDC}")
        return
    
    random_files = random.sample(txt_files, min(num_tests, len(txt_files)))
    
    print(f"\n{Bcolors.HEADER}=== Testing on Random Documents ==={Bcolors.ENDC}")
    
    for txt_file in random_files:
        doc_id = txt_file.replace('.txt', '')
        txt_path = TXT_FOLDER / txt_file
        
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            subject, confidence = predict_subject(content, models)
            
            print(f"\n{Bcolors.OKBLUE}Document: {doc_id}{Bcolors.ENDC}")
            print(f"Predicted subject: {Bcolors.OKGREEN}{subject}{Bcolors.ENDC}")
            print(f"Confidence: {confidence:.3f}")
            print(f"First 200 chars: {content[:200]}...")
            
        except Exception as e:
            print(f"Error reading {txt_file}: {e}")

def interactive_demo(models):
    """Interactive prediction demo"""
    print(f"\n{Bcolors.HEADER}=== Interactive Demo ==={Bcolors.ENDC}")
    print("Enter text to classify (or 'quit' to exit):")
    
    while True:
        text = input(f"\n{Bcolors.OKBLUE}Enter text: {Bcolors.ENDC}")
        
        if text.lower() in ['quit', 'exit', 'q']:
            break
            
        if not text.strip():
            print("Please enter some text.")
            continue
        
        subject, confidence = predict_subject(text, models)
        
        print(f"Predicted subject: {Bcolors.OKGREEN}{subject}{Bcolors.ENDC}")
        print(f"Confidence: {confidence:.3f}")

if __name__ == "__main__":
    print(f"{Bcolors.HEADER}=== Subject Classification Demo ==={Bcolors.ENDC}")
    
    # Load models
    models = load_models()
    if not models:
        exit(1)
    
    print(f"Available classes: {len(models['label_encoder'].classes_)}")
    print(f"Classes: {list(models['label_encoder'].classes_)[:10]}...")  # Show first 10
    
    # Test on random documents
    test_random_documents(models)
    
    # Interactive demo
    interactive_demo(models)