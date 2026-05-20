"""
test_extract.py — Multicolumn-aware PDF text extraction.

Single-column docs  → extractor API (localhost:8001)
Multi-column docs   → local pdfplumber extraction, column-by-column order:
                      all lines from col-1, then all lines from col-2, etc.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).parent.parent / "utils" / "consume_apis"))
from consume_extractor import make_requests_only_text

from multicolumn_detection import (
    detect_columns_histogram,
    detect_page_columns,
    detect_pdf_columns,
)

PDF_DIR = Path("/home/nahuel/Documents/document_extraction_llm/data/sedici/pdfs")
TOKEN = "f85b060e12171336480486d98b694bcb0b6c1c826938c7e6916277d6676bae8c"
EXTRACTOR_URL = "http://localhost:8001"

MULTICOLUMN_DOCS = [
    "10915-117917",
    "10915-117661",
    "10915-117660",
    "10915-117729",
    "10915-117224",
    "10915-117443",
    "10915-145097",
    "10915-145103",
    "10915-117806",  # 3-col
]

SINGLE_COLUMN_DOCS = [
    "10915-156531",
    "10915-135626",
    "10915-146678",
    "10915-155878",
    "10915-115887",
    "10915-161334",
]


# ── Column extraction ─────────────────────────────────────────────────────────

def _split_xs_for_page(page, n_cols: int) -> list[float]:
    """Return x-coordinates that split the page into n_cols columns."""
    if n_cols <= 1:
        return []

    result_b = detect_columns_histogram(page)
    split_x = result_b.get("split_x")

    if n_cols == 2 and split_x:
        return [split_x]

    # Fallback: evenly divide the page (covers 3-col or missing split_x)
    return [page.width * i / n_cols for i in range(1, n_cols)]


def extract_page_columns(page, split_xs: list[float]) -> str:
    """
    Extract text from a multi-column page using word-level column assignment.

    1. Group all words into horizontal lines by bucketing their top-y into 2pt bands.
    2. Assign each word to a column by comparing its x-center to split_xs.
    3. Build one list of text lines per column.
    4. Return: col1_text + "\\n\\n" + col2_text + ... (col-by-col order).
    """
    words = page.extract_words()
    if not words:
        return page.extract_text() or ""

    n_cols = len(split_xs) + 1
    boundaries = [0.0] + split_xs + [float(page.width)]

    # Group words by y-position (2pt buckets → same text line)
    line_map: dict[int, list] = defaultdict(list)
    for w in words:
        y_key = round(w["top"] / 2) * 2
        line_map[y_key].append(w)

    col_lines: list[list[str]] = [[] for _ in range(n_cols)]

    for y_key in sorted(line_map):
        line_words = sorted(line_map[y_key], key=lambda w: w["x0"])

        col_word_groups: list[list[str]] = [[] for _ in range(n_cols)]
        for w in line_words:
            x_center = (w["x0"] + w["x1"]) / 2
            col_idx = n_cols - 1  # default: last column
            for i in range(n_cols):
                if boundaries[i] <= x_center < boundaries[i + 1]:
                    col_idx = i
                    break
            col_word_groups[col_idx].append(w["text"])

        for i, group in enumerate(col_word_groups):
            if group:
                col_lines[i].append(" ".join(group))

    parts = ["\n".join(lines) for lines in col_lines if lines]
    return "\n\n".join(parts)


def extract_pdf_multicolumn(pdf_path: Path) -> str:
    """Open the PDF and extract text page by page, respecting column layout."""
    page_texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            result = detect_page_columns(page)
            n_cols = result["columns"]

            if n_cols > 1:
                split_xs = _split_xs_for_page(page, n_cols)
                text = extract_page_columns(page, split_xs)
            else:
                text = page.extract_text() or ""

            page_texts.append(text)

    return "\n\n".join(page_texts)


# ── Main entry point ──────────────────────────────────────────────────────────

def extract_pdf(pdf_path: Path) -> str:
    """
    Detect layout then route to the right extractor:
      - Single-column → extractor API
      - Multi-column  → local pdfplumber column extraction
    """
    detection = detect_pdf_columns(pdf_path)
    is_multi = detection["is_multicolumn"]
    print(
        f"  Layout: {'MULTI' if is_multi else 'SINGLE'}  "
        f"({detection['pages_multicolumn']}/{detection['pages_checked']} pages multi)"
    )

    if is_multi:
        return extract_pdf_multicolumn(pdf_path)

    raw = make_requests_only_text(
        file_path=pdf_path,
        token=TOKEN,
        normalization=True,
        ocr=False,
        host_url=EXTRACTOR_URL,
    )
    try:
        return json.loads(raw).get("text", raw)
    except Exception:
        return raw


# ── CLI ───────────────────────────────────────────────────────────────────────

def _run_batch(doc_ids: list[str], label: str) -> None:
    print("=" * 70)
    print(label)
    print("=" * 70)
    for doc_id in doc_ids:
        pdf = PDF_DIR / f"{doc_id}.pdf"
        if not pdf.exists():
            print(f"  {doc_id}  [PDF not found]")
            continue
        print(f"\n--- {doc_id} ---")
        text = extract_pdf(pdf)
        preview = text[:600].replace("\n", " | ")
        print(f"  Preview : {preview}")
        print(f"  Total   : {len(text)} chars")


if __name__ == "__main__":
    _run_batch(MULTICOLUMN_DOCS, "MULTI-COLUMN DOCS — column-by-column extraction")
    print()
    _run_batch(SINGLE_COLUMN_DOCS, "SINGLE-COLUMN DOCS — extractor API")
