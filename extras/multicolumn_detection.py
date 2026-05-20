"""
Multi-column layout detector for PDF documents.

Two complementary methods:
  A) Char-gap method   — groups characters by y-coordinate (line), then looks
     for a significant x-gap in the middle zone of each line.  Works directly
     on raw character positions so it doesn't depend on pdfplumber's layout=True.
  B) X-histogram method — bins word x-centers across the page width and looks
     for a low-density "valley" in the middle (the gutter between columns).

Known multi-column docs (from validation analysis):
  2-col: 10915-117917, 10915-117661, 10915-117660, 10915-117729,
         10915-117224, 10915-117443, 10915-145097, 10915-145103
  3-col: 10915-117806

Known single-column docs (negative examples):
  10915-156531, 10915-135626, 10915-150991, 10915-146678,
  10915-155878, 10915-115887, 10915-161334
"""

from collections import defaultdict
from pathlib import Path

import pdfplumber

PDF_DIR = Path("/home/nahuel/Documents/document_extraction_llm/data/sedici/pdfs")

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
    "10915-150991",  # table/structured multi-col
]

SINGLE_COLUMN_DOCS = [
    "10915-156531",
    "10915-135626",
    "10915-146678",
    "10915-155878",
    "10915-115887",
    "10915-161334",
]


# ── Method A: character-gap per line ─────────────────────────────────────────

def detect_columns_char_gap(page,
                             min_gap_pts: float = 12.0,
                             min_line_ratio: float = 0.35) -> dict:
    """
    Group characters by their vertical position (y) into text lines.
    For each line wide enough to span multiple columns, check whether
    there is a horizontal gap >= min_gap_pts in the middle 25-75% zone.
    If >= min_line_ratio of qualifying lines have such a gap → multi-column.
    """
    chars = page.chars
    if not chars:
        return {"columns": 1, "confidence": 0.0, "method": "A"}

    page_width = page.width

    # Guard: right-margin annotation spike (line numbers, page numbers, etc.)
    # If >5% of chars sit in a narrow band beyond 75% of page width, those are
    # right-margin annotations that create fake mid-line gaps — don't fire.
    all_x0s = [c["x0"] for c in chars]
    right_thresh = page_width * 0.75
    right_x0s = [x for x in all_x0s if x >= right_thresh]
    if len(right_x0s) / max(len(all_x0s), 1) > 0.05:
        x_span = max(right_x0s) - min(right_x0s)
        if x_span < page_width * 0.10:
            return {"columns": 1, "confidence": 0.0, "method": "A"}

    # Group chars into lines using 2-pt y-buckets
    line_map: dict[int, list] = defaultdict(list)
    for c in chars:
        y_key = round(c["top"] / 2) * 2
        line_map[y_key].append(c["x0"])

    gap_lines   = 0
    total_lines = 0

    for xs_unsorted in line_map.values():
        xs = sorted(xs_unsorted)
        if len(xs) < 8:
            continue
        line_span = xs[-1] - xs[0]
        # Only consider lines that span at least 40 % of page width
        if line_span < page_width * 0.40:
            continue
        total_lines += 1

        # Scan consecutive x-positions for a gap in the middle 25-75 % zone
        for i in range(len(xs) - 1):
            gap      = xs[i + 1] - xs[i]
            rel_pos  = (xs[i] - xs[0]) / line_span
            if gap >= min_gap_pts and 0.25 <= rel_pos <= 0.75:
                gap_lines += 1
                break

    # Require at least 3 qualifying lines — sparse pages give noisy ratios
    if total_lines < 3:
        return {"columns": 1, "confidence": 0.0, "method": "A"}

    ratio = gap_lines / total_lines
    return {"columns": 2 if ratio >= min_line_ratio else 1, "confidence": round(ratio, 2), "method": "A"}


# ── Method B: x-histogram valley detection ───────────────────────────────────

def detect_columns_histogram(page,
                              n_bins: int = 20,
                              valley_threshold: float = 0.35) -> dict:
    """
    Bin word x-centers across the page width.
    A two-column page has two dense clusters separated by a low-density valley.
    If the minimum bin in the middle 30-70 % zone is < valley_threshold * max_bin
    AND both sides of the valley have substantial word counts → multi-column.
    """
    words = page.extract_words()
    if len(words) < 25:
        return {"columns": 1, "confidence": 0.0, "method": "B", "split_x": None}

    page_width = page.width
    bin_width  = page_width / n_bins

    bins = [0] * n_bins
    for w in words:
        x_center  = (w["x0"] + w["x1"]) / 2
        bin_idx   = min(int(x_center / bin_width), n_bins - 1)
        bins[bin_idx] += 1

    max_count = max(bins)
    if max_count == 0:
        return {"columns": 1, "confidence": 0.0, "method": "B", "split_x": None}

    # Guard: right-margin annotation spike (line numbers, page numbers, etc.)
    # If ≥10 words are in the rightmost 30% and >60% of them sit in a single bin,
    # that's a narrow margin column, not a real text column — skip this page.
    right_zone_start = int(n_bins * 0.70)
    right_zone_bins  = bins[right_zone_start:]
    right_zone_total = sum(right_zone_bins)
    if right_zone_total >= 10 and max(right_zone_bins) / right_zone_total > 0.60:
        # Expose the spike so detect_page_columns can also suppress Method A
        return {"columns": 1, "confidence": 0.0, "method": "B", "split_x": None, "right_spike": True}

    mid_start = int(n_bins * 0.30)
    mid_end   = int(n_bins * 0.70)
    mid_bins  = bins[mid_start:mid_end]
    min_val   = min(mid_bins)
    valley_bin = mid_start + mid_bins.index(min_val)
    valley_ratio = min_val / max_count

    if valley_ratio < valley_threshold:
        split_x     = (valley_bin + 0.5) * bin_width
        left_words  = sum(bins[:valley_bin])
        right_words = sum(bins[valley_bin + 1:])

        if left_words >= 10 and right_words >= 10:
            confidence = round(1.0 - valley_ratio, 2)
            return {
                "columns":      2,
                "confidence":   confidence,
                "method":       "B",
                "split_x":      round(split_x, 1),
                "valley_ratio": round(valley_ratio, 2),
            }

    return {
        "columns":      1,
        "confidence":   round(valley_ratio, 2),
        "method":       "B",
        "split_x":      None,
        "valley_ratio": round(valley_ratio, 2),
    }


# ── Page-level combiner ───────────────────────────────────────────────────────

def detect_page_columns(page) -> dict:
    result_a = detect_columns_char_gap(page)
    result_b = detect_columns_histogram(page)

    multi_a = result_a["columns"] > 1 and result_a["confidence"] >= 0.35
    multi_b = result_b["columns"] > 1

    # If Method B found a right-margin annotation spike AND the page is sparse
    # (≤ 250 words), Method A is likely seeing that spike as fake column gaps.
    # Dense pages (> 250 words) produce right-zone concentration naturally from
    # the right text column itself — don't suppress A there.
    if result_b.get("right_spike") and multi_a and not multi_b:
        page_word_count = len(page.extract_words())
        if page_word_count <= 250:
            multi_a = False

    verdict = 2 if (multi_a or multi_b) else 1
    return {"columns": verdict, "method_a": result_a, "method_b": result_b}


def detect_pdf_columns(pdf_path: Path, max_pages: int = 5) -> dict:
    """
    Analyse up to max_pages pages. Majority vote decides the document layout.
    """
    _MIN_WORDS_SPARSE   = 25   # pages below this are cover/blank
    _LONG_DOC_THRESHOLD = 50   # threshold for "very long" docs (theses, books)

    page_results = []
    word_counts  = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for page in pdf.pages[:max_pages]:
            wc = len(page.extract_words())
            word_counts.append(wc)
            page_results.append(detect_page_columns(page))

    sparse_initial = sum(1 for wc in word_counts if wc < _MIN_WORDS_SPARSE)

    # For very long documents (theses/books) whose initial sample contains
    # >= 2 sparse pages (cover, blank, ToC), vote only on content pages.
    # Rationale: adding more scanned pages doesn't help because blank pages
    # appear throughout (chapter separators etc.), keeping the ratio below 60%.
    # Short papers (≤ 50 pages) or docs with only 1 sparse cover page are
    # not affected — their original 5-page denominator works correctly.
    if sparse_initial >= 2 and total_pages > _LONG_DOC_THRESHOLD:
        content_results = [r for r, wc in zip(page_results, word_counts)
                           if wc >= _MIN_WORDS_SPARSE]
        vote_results = content_results if content_results else page_results
    else:
        vote_results = page_results

    multi_pages = sum(1 for r in vote_results if r["columns"] > 1)
    n           = max(len(vote_results), 1)
    # Short docs (1-2 pages): majority vote — if any page is multi, the doc is.
    # Longer docs: > 60 % of pages must be multi-column (robustness against
    # cover pages or appendix pages that look like a different layout).
    is_multi    = multi_pages >= 1 if n <= 2 else multi_pages / n > 0.60

    return {
        "is_multicolumn":    is_multi,
        "columns":           2 if is_multi else 1,
        "pages_checked":     len(page_results),
        "pages_multicolumn": multi_pages,
        "page_details":      page_results,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def _fmt(result: dict) -> str:
    d      = result["page_details"][0] if result["page_details"] else {}
    a_conf = d.get("method_a", {}).get("confidence", 0)
    b_conf = d.get("method_b", {}).get("confidence", 0)
    b_vr   = d.get("method_b", {}).get("valley_ratio", "-")
    return (
        f"{'MULTI' if result['is_multicolumn'] else 'SINGLE':6s}  "
        f"pages_multi={result['pages_multicolumn']}/{result['pages_checked']}  "
        f"A_conf={a_conf:.2f}  B_conf={b_conf:.2f}  B_valley={b_vr}"
    )


if __name__ == "__main__":
    print("=" * 75)
    print("KNOWN MULTI-COLUMN DOCS  (expected: MULTI)")
    print("=" * 75)
    tp = fn = 0
    for doc_id in MULTICOLUMN_DOCS:
        pdf = PDF_DIR / f"{doc_id}.pdf"
        if not pdf.exists():
            print(f"  {doc_id}  [PDF not found]")
            continue
        res = detect_pdf_columns(pdf)
        ok  = "✓" if res["is_multicolumn"] else "✗"
        if res["is_multicolumn"]:
            tp += 1
        else:
            fn += 1
        print(f"  {ok} {doc_id}  {_fmt(res)}")

    print()
    print("=" * 75)
    print("KNOWN SINGLE-COLUMN DOCS  (expected: SINGLE)")
    print("=" * 75)
    tn = fp = 0
    for doc_id in SINGLE_COLUMN_DOCS:
        pdf = PDF_DIR / f"{doc_id}.pdf"
        if not pdf.exists():
            print(f"  {doc_id}  [PDF not found]")
            continue
        res = detect_pdf_columns(pdf)
        ok  = "✓" if not res["is_multicolumn"] else "✗"
        if not res["is_multicolumn"]:
            tn += 1
        else:
            fp += 1
        print(f"  {ok} {doc_id}  {_fmt(res)}")

    total   = tp + fn + tn + fp
    correct = tp + tn
    print()
    print(f"Accuracy: {correct}/{total}  ({correct/total*100:.0f}%)  —  "
          f"TP={tp}  FN={fn}  TN={tn}  FP={fp}")
