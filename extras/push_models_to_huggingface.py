"""
Push trained models and fine-tuning dataset to HuggingFace Hub.

Fine-tuned LLM model  → model repo   (Nahpanigo99/fine-tuned-model-led)
Sklearn .pkl models   → dataset repo (Nahpanigo99/sedici-ml-models)
Fine-tuning dataset   → dataset repo (Nahpanigo99/sedici-ml-models)

Token is read from fine_tunning/.env  (TOKEN_HUGGING_FACE)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi, login

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]

LLM_MODEL_DIR    = REPO_ROOT / "api/app/llm_service/app/models/fine-tuned-model-led"
SKL_MODELS_DIR   = REPO_ROOT / "api/app/orchestrator/app/models"
FINETUNING_JSON  = REPO_ROOT / "data/sedici/jsons/sedici_finetunnig_metadata_with_ocr.json"
FINETUNING_JSON_HF_NAME = "sedici_finetuning_dataset.json"

# ---------------------------------------------------------------------------
# HuggingFace config
# ---------------------------------------------------------------------------
HF_USERNAME    = "Nahpanigo99"
LLM_REPO_ID    = f"{HF_USERNAME}/fine-tuned-model-led"
SKL_REPO_ID    = f"{HF_USERNAME}/sedici-ml-models"

GITHUB_REPO    = "https://github.com/nahuelPanigo/document_extraction_llm"
DOCS_URL       = "https://nahuelpanigo.github.io/document_extraction_llm/"
BASE_MODEL     = "allenai/led-base-16384"
BASE_MODEL_URL = "https://huggingface.co/allenai/led-base-16384"

# ---------------------------------------------------------------------------
# Model cards
# ---------------------------------------------------------------------------

LLM_MODEL_CARD = f"""\
---
language:
  - es
license: apache-2.0
base_model: {BASE_MODEL}
tags:
  - text2text-generation
  - summarization
  - metadata-extraction
  - fine-tuned
  - led
  - longformer
  - spanish
---

# fine-tuned-model-led

Fine-tuned version of [{BASE_MODEL}]({BASE_MODEL_URL}) for **automatic metadata extraction from academic documents** (books, theses, journal articles, conference papers) in Spanish, developed as part of a thesis project at SEDICI (Servicio de Difusión de la Creación Intelectual — UNLP).

## What it does

Given the plain text of an academic document (PDF), the model extracts structured metadata fields such as title, authors, date, abstract, keywords, subject, document type, and more — returning a JSON object.

## Base model

This model is a fine-tune of [`{BASE_MODEL}`]({BASE_MODEL_URL}) (Longformer Encoder-Decoder), which supports sequences up to 16 384 tokens — suitable for full academic document texts.

## Usage

This model is designed to run as part of the full extraction pipeline. See the project repository and documentation for setup instructions:

- **Code & full pipeline**: {GITHUB_REPO}
- **Documentation**: {DOCS_URL}

## Training data

Fine-tuned on a curated dataset of academic documents from the [SEDICI repository](https://sedici.unlp.edu.ar/), with manually validated metadata used as ground truth.
"""

SKL_MODEL_CARD = f"""\
---
language:
  - es
license: apache-2.0
tags:
  - sklearn
  - svm
  - tfidf
  - text-classification
  - document-type
  - subject-classification
  - spanish
---

# sedici-ml-models

Trained scikit-learn models used for **document type and subject classification** of academic documents in Spanish. These are part of the metadata extraction pipeline developed for SEDICI (Servicio de Difusión de la Creación Intelectual — UNLP).

## Files

| File | Description |
|------|-------------|
| `type_svm_classifier.pkl` | SVM classifier — predicts document type (Libro, Tesis, Artículo, Objeto de conferencia) |
| `type_svm_vectorizer.pkl` | TF-IDF vectorizer for document type model |
| `type_svm_label_encoder.pkl` | Label encoder for document type model |
| `subject_svm_classifier.pkl` | SVM classifier — predicts subject area |
| `subject_svm_vectorizer.pkl` | TF-IDF vectorizer for subject model |
| `subject_svm_label_encoder.pkl` | Label encoder for subject model |
| `tfidf_vectorizer.pkl` | Shared TF-IDF vectorizer used by the orchestrator |
| `sedici_finetuning_dataset.json` | Fine-tuning dataset — academic document texts with validated metadata labels |

## Usage

These models are loaded by the orchestrator service of the full extraction pipeline. See the project repository and documentation for setup instructions:

- **Code & full pipeline**: {GITHUB_REPO}
- **Documentation**: {DOCS_URL}

## Training data

Trained on a curated dataset of academic documents from the [SEDICI repository](https://sedici.unlp.edu.ar/).
"""

# ---------------------------------------------------------------------------


def load_token() -> str:
    env_path = REPO_ROOT / "fine_tunning/.env"
    if not env_path.exists():
        print(f"[ERROR] .env not found at {env_path}")
        sys.exit(1)
    load_dotenv(env_path)
    token = os.getenv("TOKEN_HUGGING_FACE")
    if not token:
        print("[ERROR] TOKEN_HUGGING_FACE not set in fine_tunning/.env")
        sys.exit(1)
    return token


def push_llm_model(api: HfApi):
    if not LLM_MODEL_DIR.exists():
        print(f"[SKIP] LLM model dir not found: {LLM_MODEL_DIR}")
        return

    print(f"\n--- Pushing LLM model → {LLM_REPO_ID} ---")
    api.create_repo(repo_id=LLM_REPO_ID, repo_type="model", exist_ok=True, private=False)

    api.upload_folder(
        folder_path=str(LLM_MODEL_DIR),
        repo_id=LLM_REPO_ID,
        repo_type="model",
    )
    api.upload_file(
        path_or_fileobj=LLM_MODEL_CARD.encode(),
        path_in_repo="README.md",
        repo_id=LLM_REPO_ID,
        repo_type="model",
    )
    print(f"[OK] https://huggingface.co/{LLM_REPO_ID}")


def push_sklearn_models(api: HfApi):
    if not SKL_MODELS_DIR.exists():
        print(f"[SKIP] Sklearn models dir not found: {SKL_MODELS_DIR}")
        return

    pkl_files = list(SKL_MODELS_DIR.glob("*.pkl"))
    if not pkl_files:
        print(f"[SKIP] No .pkl files found in {SKL_MODELS_DIR}")
        return

    print(f"\n--- Pushing {len(pkl_files)} sklearn .pkl models → {SKL_REPO_ID} ---")
    api.create_repo(repo_id=SKL_REPO_ID, repo_type="dataset", exist_ok=True, private=False)

    api.upload_folder(
        folder_path=str(SKL_MODELS_DIR),
        repo_id=SKL_REPO_ID,
        repo_type="dataset",
        allow_patterns=["*.pkl"],
    )
    api.upload_file(
        path_or_fileobj=SKL_MODEL_CARD.encode(),
        path_in_repo="README.md",
        repo_id=SKL_REPO_ID,
        repo_type="dataset",
    )
    print(f"[OK] https://huggingface.co/datasets/{SKL_REPO_ID}")


def push_finetuning_dataset(api: HfApi):
    if not FINETUNING_JSON.exists():
        print(f"[SKIP] Fine-tuning dataset not found: {FINETUNING_JSON}")
        return

    print(f"\n--- Pushing fine-tuning dataset → {SKL_REPO_ID}/{FINETUNING_JSON_HF_NAME} ---")
    api.create_repo(repo_id=SKL_REPO_ID, repo_type="dataset", exist_ok=True, private=False)
    api.upload_file(
        path_or_fileobj=str(FINETUNING_JSON),
        path_in_repo=FINETUNING_JSON_HF_NAME,
        repo_id=SKL_REPO_ID,
        repo_type="dataset",
    )
    print(f"[OK] https://huggingface.co/datasets/{SKL_REPO_ID}")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    token = load_token()
    login(token=token)
    print("[OK] Logged in to HuggingFace Hub")

    api = HfApi()
    push_llm_model(api)
    push_sklearn_models(api)
    push_finetuning_dataset(api)

    print("\nAll uploads complete.")
