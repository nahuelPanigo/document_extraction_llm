"""
Test script to run the PROMPT_CLEANER_METADATA on a single document via Gemini.
Compares the new cleaned output with the previously cleaned version.
Shows timing + token usage (prompt, completion, total).

Usage: Set DOCUMENT_ID below and run:
    python -m extras.test_clean_prompt_gemini
"""

import json
import os
import time
from dotenv import load_dotenv
from google import genai
from constants import (
    PROMPT_CLEANER_METADATA,
    GENAI_MODEL,
    JSON_FOLDER,
    DATASET_WITH_METADATA_AND_TEXT_DOC,
    DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED,
)
from utils.text_extraction.read_and_write_files import read_data_json

load_dotenv()

# ---- CHANGE THIS ID TO TEST A DIFFERENT DOCUMENT ----
DOCUMENT_ID = "10915-145097"
# ------------------------------------------------------

MODELS_TO_TEST = [GENAI_MODEL]
KEYS_TO_EXCLUDE = {"original_text", "id", "abstract", "keywords", "subject"}


def find_in_splits(data, doc_id):
    """Search for a document ID across training/validation/test splits."""
    for split_name in ["training", "validation", "test"]:
        split_data = data.get(split_name, [])
        for item in split_data:
            if isinstance(item, dict) and item.get("id") == doc_id:
                return item
    return None


def call_gemini(client, model, prompt_input):
    """Call Gemini and return (parsed_result, raw_text, elapsed_seconds, usage_dict)."""
    start = time.time()
    response = client.models.generate_content(
        model=model,
        contents=prompt_input,
    )
    elapsed = time.time() - start
    raw = response.text.strip()

    # Extract token usage from response
    usage = None
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        um = response.usage_metadata
        usage = {
            "prompt_tokens": getattr(um, "prompt_token_count", None),
            "completion_tokens": getattr(um, "candidates_token_count", None),
            "total_tokens": getattr(um, "total_token_count", None),
        }

    text = raw
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None

    return parsed, raw, elapsed, usage


def main():
    if not DOCUMENT_ID:
        print("ERROR: Set DOCUMENT_ID in the script before running.")
        return

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env")
        return

    # Load original dataset (uncleaned, with text)
    original_path = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC
    original_data = read_data_json(original_path, "utf-8")

    if DOCUMENT_ID not in original_data:
        print(f"ERROR: Document ID '{DOCUMENT_ID}' not found in {original_path}")
        return

    document = original_data[DOCUMENT_ID]
    extracted_text = document.get("original_text", "")
    metadata = {k: v for k, v in document.items() if k not in KEYS_TO_EXCLUDE}

    # Build prompt (same as the pipeline does)
    prompt_input = f"""{PROMPT_CLEANER_METADATA}
        - Metadata: {metadata}
        - Text: {extracted_text}"""

    # Print original metadata
    print("=" * 60)
    print("ORIGINAL METADATA (sent to LLM)")
    print("=" * 60)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

    # Call each model
    client = genai.Client(api_key=api_key)
    results = {}

    for model in MODELS_TO_TEST:
        print(f"\nSending document '{DOCUMENT_ID}' to {model}...")
        try:
            parsed, raw, elapsed, usage = call_gemini(client, model, prompt_input)
            results[model] = {"parsed": parsed, "raw": raw, "elapsed": elapsed, "usage": usage}

            print(f"\n{'=' * 60}")
            print(f"RESULT FROM {model} ({elapsed:.2f}s)")
            print(f"{'=' * 60}")
            if usage:
                print(f"  Tokens — prompt: {usage['prompt_tokens']}, completion: {usage['completion_tokens']}, total: {usage['total_tokens']}")
            else:
                print("  Token usage: not available")
            if parsed:
                print(json.dumps(parsed, indent=2, ensure_ascii=False))
            else:
                print("FAILED TO PARSE JSON:")
                print(raw)
        except Exception as e:
            print(f"ERROR with {model}: {e}")
            results[model] = None

    # Load previously cleaned version from the final dataset (has splits)
    checked_path = JSON_FOLDER / DATASET_WITH_METADATA_AND_TEXT_DOC_CHECKED
    checked_data = read_data_json(checked_path, "utf-8")
    previous_cleaned = find_in_splits(checked_data, DOCUMENT_ID)
    if previous_cleaned:
        previous_cleaned = {k: v for k, v in previous_cleaned.items() if k not in {"original_text", "id", "type"}}

    print(f"\n{'=' * 60}")
    print("PREVIOUSLY CLEANED RESULT")
    print("=" * 60)
    if previous_cleaned:
        print(json.dumps(previous_cleaned, indent=2, ensure_ascii=False))
    else:
        print(f"Document '{DOCUMENT_ID}' not found in any split (training/validation/test).")

    # Show differences per model vs previous
    if previous_cleaned:
        for model, result in results.items():
            if result and result["parsed"]:
                print(f"\n{'=' * 60}")
                print(f"DIFFERENCES: {model} vs PREVIOUS")
                print("=" * 60)
                new_parsed = result["parsed"]
                all_keys = set(list(new_parsed.keys()) + list(previous_cleaned.keys()))
                has_diff = False
                for key in sorted(all_keys):
                    new_val = new_parsed.get(key)
                    old_val = previous_cleaned.get(key)
                    if str(new_val) != str(old_val):
                        has_diff = True
                        print(f"  {key}:")
                        print(f"    {model}: {new_val}")
                        print(f"    PREV:     {old_val}")
                if not has_diff:
                    print("  No differences found.")

    # Timing summary
    print(f"\n{'=' * 60}")
    print("TIMING SUMMARY")
    print("=" * 60)
    for model, result in results.items():
        if result:
            usage = result["usage"]
            if usage:
                tokens = f"prompt={usage['prompt_tokens']}, completion={usage['completion_tokens']}, total={usage['total_tokens']}"
            else:
                tokens = "N/A"
            print(f"  {model}: {result['elapsed']:.2f}s ({tokens})")


if __name__ == "__main__":
    main()
