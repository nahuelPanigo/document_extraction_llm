# Subject Classification System

This folder contains a machine learning approach for predicting document subjects from document content only, designed to classify documents into one of 42 possible academic subjects.

## Overview

The system implements a **single-label classification** approach that:

- **Predicts exactly ONE subject per document** (42 possible subjects)
- **Uses only document content** (no title/abstract/keywords needed)
- **Leverages existing data** (CSV + extracted texts, no additional downloads)
- **Employs optimized feature engineering** for academic document content classification

## Files


- `demo.py`: Interactive demo and prediction examples
- `main.py`: Data preparation and subject analysis
- `README.md`: This documentation

## Key Advantages over Transformers

### Speed and Efficiency
- **Fast inference**: No GPU required, instant predictions
- **Low computational cost**: Suitable for production environments
- **Scalable**: Can handle large document volumes efficiently

### Domain Specialization
- **Multi-label support**: Predicts multiple subjects simultaneously
- **Hierarchical mapping**: Maps specific subjects to broader FORD categories
- **Frequency-based filtering**: Focuses on subjects with sufficient training data
- **Feature engineering**: Leverages title, abstract, and keyword information

### Customization
- **Domain-specific**: Trained specifically on your document collection
- **Adjustable thresholds**: Control prediction confidence levels
- **Extensible**: Easy to retrain with new data

## Data Sources

The system uses **existing data only** - no additional downloads required:

1. **Subject Labels**: `data/sedici/csv/sedici_filtered_2019_2024.csv`
   - Column: `sedici.subject.materias` (target to predict)
   - Document IDs for mapping

2. **Document Content**: `texts folder`  
   - Same IDs as CSV for mapping

## Usage

### Main Approach
```bash
# 1. Data preparation (if using complex approach)
python main.py

```


### Demo and Interactive Use
```bash
python demo.py
```
This provides:
- Demonstration on sample texts
- Interactive prediction interface
- Confidence scores for predictions

## Model Architecture

### Simple Classification (Recommended)
- **Algorithm**: Random Forest (single-label)
- **Features**: TF-IDF vectors (up to 15,000 features, 1-2 grams)
- **Labels**: Single subject per document (42 possible classes)
- **Evaluation**: Accuracy, precision, recall, F1-score

### Feature Engineering
- **Text Sources**: Document content only in text
- **Preprocessing**: HTML cleaning, normalization, lowercasing
- **TF-IDF Parameters**: 
  - Max features: 15,000 (more since only using content)
  - N-grams: 1-2 (unigrams + bigrams)
  - Min document frequency: 2
  - Max document frequency: 80%

### Legacy Multi-label Architecture
- **Algorithm**: Random Forest with MultiOutputClassifier
- **Features**: TF-IDF vectors (up to 10,000 features, 1-3 grams)
- **Labels**: Multi-label binary encoding of subjects
- **Text Sources**: Document text + title + abstract + keywords

## Processing Logic (Pseudocode)

### Simple Classification Pipeline
```pseudocode
1. LOAD CSV: sedici_filtered_2019_2024.csv
   - Extract mapping: document_id → subject

2. LOAD TEXT: from text folder
   - Extract mapping: document_id → original_text

3. CREATE DATASET:
   FOR each document_id in CSV:
     IF document_id exists in JSON:
       text = text_from_doc
       subject = CSV[document_id]["sedici.subject.materias"]
       ADD (text, subject) to training_data

4. FILTER by frequency (min 5 documents per subject)

5. PREPROCESSING:
   - Clean HTML tags from text
   - Normalize whitespace
   - Convert to lowercase

6. FEATURE EXTRACTION:
   - TF-IDF vectorization (15K features, 1-2 grams)
   - Only document content, no metadata

7. TRAINING:
   - Random Forest classifier
   - 80/20 train/test split
   - Single-label output (one subject per document)

8. EVALUATION:
   - Accuracy score
   - Classification report per subject
   - Confidence scores for predictions
```

### Key Differences from Legacy
- **Input**: CSV + JSON (existing data) vs complex dataset creation
- **Text**: Document content only vs content + metadata  
- **Output**: Single subject vs multiple subjects array
- **Speed**: No data preparation needed vs multi-step pipeline

## Performance Expectations

### Simple Classification
- **Accuracy**: Expected 0.6-0.85 for single-label classification
- **Speed**: ~2000+ documents/second (no complex preprocessing)
- **Memory**: ~200MB for model and vectorizer
- **Training Time**: 2-5 minutes on standard hardware

### Legacy Multi-label
- **Jaccard Score**: Expected 0.3-0.6 for subject prediction
- **FORD Categories**: Expected 0.5-0.8 for broader categories
- **Speed**: ~1000 documents/second
- **Memory**: ~500MB for model and vectorizer

## When to Use ML vs Transformers

### Use ML Approach When:
- You have sufficient training data for your domain
- Speed and cost are important factors
- You need multi-label predictions
- Your subject vocabulary is relatively stable
- You want production-ready inference

### Use Transformer Approach When:
- You need to discover completely new subjects
- Your documents have complex semantic structures
- You have limited training data
- Subject vocabulary changes frequently
- Accuracy is more important than speed

## Extending the System

### Adding New Subjects
1. Update your training dataset with new subject labels
2. Re-run `main.py` to prepare the updated dataset
3. Re-train models with `classification.py`

### Improving Performance
1. **Increase training data**: More examples per subject
2. **Feature engineering**: Add domain-specific features
3. **Model tuning**: Optimize hyperparameters
4. **Ensemble methods**: Combine multiple algorithms

### Custom FORD Mapping
Edit the `FORD_SEDICI_MATERIAS` dictionary in `constants.py` to customize the hierarchical mapping between specific subjects and broader categories.

## Model Files

### Simple Classification (Recommended)
After running `simple_classification.py`:
- `simple_subject_classifier.pkl`: Single-label Random Forest classifier
- `simple_vectorizer.pkl`: TF-IDF vectorizer for content-only features
- `simple_label_encoder.pkl`: Label encoder for 42 subject classes

### Legacy Multi-label 
After running `classification.py`:
- `modelo_subject_clasificacion.pkl`: Multi-label subject classifier
- `modelo_ford_clasificacion.pkl`: FORD category classifier  
- `vectorizador_subject_tfidf.pkl`: TF-IDF vectorizer
- `mlb_subjects.pkl`: Multi-label binarizer for subjects
- `mlb_ford.pkl`: Multi-label binarizer for FORD categories

## Requirements

The system uses the same dependencies as the main project:
- scikit-learn
- pandas
- numpy
- beautifulsoup4
- joblib

No additional GPU or deep learning libraries required.