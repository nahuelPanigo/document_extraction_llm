"""
Comparison using validated test data — runs all extractions on the 60-doc
validation set from test_metadata_last_dataset_with_keywords_and_abstract.json.

Since most docs only have PDFs (no pre-extracted txt), text is extracted
on-the-fly using PdfReader.

Output: extras/comparison_test_data.json
  {
    "<id>": {
      "grobid_abstract":  str,
      "grobid_keywords":  str,   # pipe-separated
      "pattern_abstract": str,   # strategy_b_regex result
      "pattern_regex":    str,   # pipe-separated keywords (strategy_a_regex)
      "tfidf_keywords":   str,   # pipe-separated keywords (strategy_d_tfidf)
    },
    ...
  }

Run from repo root:
    python extras/comparison_with_test_data.py

Requirements:
    - Grobid service at GROBID_SERVICE (default http://localhost:8070)
      Start with: docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.2
    - pip install pdfplumber requests beautifulsoup4 lxml
"""

import json
import re
import sys
import time
import requests
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
sys.path.append(str(Path(__file__).parent))

from constants import PDF_FOLDER, TXT_NO_TAGS_FOLDER, GROBID_SERVICE
from abstract_extraction.main import strategy_b_regex
from keywords_extraction.main import strategy_a_regex, strategy_d_tfidf, build_or_load_tfidf
from grobid.main import check_grobid, send_to_grobid, parse_xml

from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────
VALIDATION_JSON = ROOT / "validation" / "result" / "test_metadata_last_dataset_with_keywords_and_abstract.json"
OUTPUT_JSON     = Path(__file__).parent / "comparison_test_data.json"
XML_FOLDER      = Path(__file__).parent / "grobid" / "xml_test"   # separate from 80-doc set
REQUEST_DELAY   = 1.0

XML_FOLDER.mkdir(parents=True, exist_ok=True)


# ── Text extraction ───────────────────────────────────────────────────────────

def _get_text(doc_id: str) -> str:
    """
    Return plain text for a document.
    Priority: pre-existing txt file → PDF extraction via PdfReader.
    """
    txt_path = TXT_NO_TAGS_FOLDER / f"{doc_id}.txt"
    if txt_path.exists():
        return txt_path.read_text(encoding="utf-8", errors="ignore")

    pdf_path = PDF_FOLDER / f"{doc_id}.pdf"
    if not pdf_path.exists():
        print(f"  [MISSING] No txt or PDF for {doc_id}")
        return ""

    try:
        sys.path.append(str(ROOT / "utils" / "text_extraction"))
        from pdf_reader import PdfReader
        reader = PdfReader()
        text = reader.extract_text(str(pdf_path), ocr=False)
        if text:
            txt_path.write_text(text, encoding="utf-8")
            print(f"  [CACHED] {doc_id}.txt saved")
        return text
    except Exception as e:
        print(f"  [PDF ERROR] {doc_id}: {e}")
        return ""


# ── Grobid ────────────────────────────────────────────────────────────────────

def _grobid_for(doc_id: str, grobid_ok: bool) -> dict:
    """Return {abstract, keywords} from Grobid for a document."""
    xml_path = XML_FOLDER / f"{doc_id}.xml"

    if not xml_path.exists():
        if not grobid_ok:
            return {"abstract": "", "keywords": ""}

        pdf_path = PDF_FOLDER / f"{doc_id}.pdf"
        if not pdf_path.exists():
            print(f"  [MISSING PDF] {doc_id}")
            return {"abstract": "", "keywords": ""}

        print(f"  Grobid → {doc_id}…", end=" ", flush=True)
        xml = send_to_grobid(pdf_path)
        if xml:
            xml_path.write_text(xml, encoding="utf-8")
            print("OK")
        else:
            print("FAILED")
            return {"abstract": "", "keywords": ""}

        time.sleep(REQUEST_DELAY)

    parsed = parse_xml(xml_path)
    return {"abstract": parsed["abstract"], "keywords": parsed["keywords"]}


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("Loading validation JSON…")
    with open(VALIDATION_JSON, encoding="utf-8") as f:
        val_data: dict = json.load(f)
    doc_ids = list(val_data.keys())
    print(f"  {len(doc_ids)} documents")

    # ── TF-IDF vectorizer (built from full corpus) ────────────────────────────
    print("\nLoading TF-IDF vectorizer…")
    vectorizer = build_or_load_tfidf()

    # ── Grobid availability ───────────────────────────────────────────────────
    grobid_ok = check_grobid()
    if not grobid_ok:
        print(f"\n[WARN] Grobid not reachable at {GROBID_SERVICE}")
        print("       Start: docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.2")
        print("       Will use cached XMLs only.\n")
    else:
        print(f"\nGrobid OK at {GROBID_SERVICE}")

    # ── Process each document ─────────────────────────────────────────────────
    results: dict = {}
    missing_text = 0

    for i, doc_id in enumerate(doc_ids, 1):
        print(f"\n[{i}/{len(doc_ids)}] {doc_id}")

        # Plain text (for regex/tfidf extractions)
        text = _get_text(doc_id)
        if not text:
            missing_text += 1

        # Abstract (regex)
        pattern_abstract = strategy_b_regex(text) if text else ""

        # Keywords — regex
        pattern_regex = strategy_a_regex(text) if text else []

        # Keywords — TF-IDF
        tfidf_kws = strategy_d_tfidf(text, vectorizer) if text else []

        # Grobid
        gr = _grobid_for(doc_id, grobid_ok)

        ground_truth = val_data[doc_id]
        results[doc_id] = {
            "grobid_abstract":  gr["abstract"],
            "grobid_keywords":  gr["keywords"],
            "pattern_abstract": pattern_abstract,
            "pattern_regex":    " | ".join(pattern_regex),
            "tfidf_keywords":   " | ".join(tfidf_kws),
            "validated_abstract": ground_truth.get("abstract", ""),
            "validated_keywords": ground_truth.get("keywords", []),
        }

    # ── Save ──────────────────────────────────────────────────────────────────
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ── Summary ───────────────────────────────────────────────────────────────
    n = len(results)

    def filled(key):
        return sum(1 for v in results.values() if v[key])

    print(f"\n{'='*60}")
    print(f"SUMMARY  ({n} docs)")
    print(f"  {'Field':<26} {'Filled':>6} / {n}")
    print(f"  {'-'*26} {'-'*6}")
    for key in ["grobid_abstract", "grobid_keywords", "pattern_abstract",
                "pattern_regex", "tfidf_keywords",
                "validated_abstract", "validated_keywords"]:
        print(f"  {key:<26} {filled(key):>6}")
    if missing_text:
        print(f"\n  [WARN] {missing_text} docs had no text source")
    print(f"\nSaved → {OUTPUT_JSON}")


if __name__ == "__main__":
    run()
