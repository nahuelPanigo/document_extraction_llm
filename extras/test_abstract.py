"""
test_abstract.py — Abstract extraction comparison: baseline vs multicolumn-aware.

Loop 1 (baseline)  : every doc → extractor API (current behaviour)
Loop 2 (smart)     : multi-column docs → local column extraction
                     single-column docs → extractor API (same as baseline)

At the end, prints a side-by-side scorecard and highlights per-doc improvements.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import pdfplumber

sys.path.append(str(Path(__file__).parent.parent))
from constants import PDF_FOLDER
from utils.consume_apis.consume_extractor import make_requests_only_text

from multicolumn_detection import detect_pdf_columns, detect_page_columns, detect_columns_histogram

TOKEN = "f85b060e12171336480486d98b694bcb0b6c1c826938c7e6916277d6676bae8c"
FINAL_JSON_PATH = Path(
    "/home/nahuel/Documents/document_extraction_llm/validation/result/final_to_compare_original.json"
)
PER_DOC_JSON_PATH = Path(
    "/home/nahuel/Documents/document_extraction_llm/validation/result/abstract_multiline_comparison_by_id.json"
)


# ── Abstract extraction patterns ──────────────────────────────────────────────

_ABSTRACT_WORDS = r"(resumen|abstract|summary|resumo|abstracto|r[eé]sum[eé]|resúmen)"
_SPANISH_ABSTRACT_WORDS = r"(resumen|abstracto|resúmen)"
_NUM_PREFIX     = r"(?:\d{1,2}\s*[\.\-–—]\s*)?"

_ABSTRACT_HEADINGS = re.compile(
    r"^" + _NUM_PREFIX + _ABSTRACT_WORDS + r"[.:\-–—]?\s*$",
    re.IGNORECASE,
)
_ABSTRACT_INLINE = re.compile(
    r"^" + _NUM_PREFIX + _ABSTRACT_WORDS + r"\s*[.:\-–—]?\s+(.*)",
    re.IGNORECASE | re.DOTALL,
)
_SPANISH_ABSTRACT_HEADINGS = re.compile(
    r"^" + _NUM_PREFIX + _SPANISH_ABSTRACT_WORDS + r"[.:\-–—]?\s*$",
    re.IGNORECASE,
)
_SPANISH_ABSTRACT_INLINE = re.compile(
    r"^" + _NUM_PREFIX + _SPANISH_ABSTRACT_WORDS + r"\s*[.:\-–—]?\s+(.*)",
    re.IGNORECASE | re.DOTALL,
)
_ABSTRACT_STOP_HEADINGS = {
    "introducción", "introduction", "introdução", "introducao",
    "índice", "indice", "index", "contenido", "contents", "tabla de contenidos",
    "capítulo 1", "chapter 1", "1. introducción", "1. introduction",
    "objetivos", "objectives", "metodología", "methodology",
    "materiales y métodos", "materials and methods",
    "agradecimientos", "acknowledgements", "acknowledgments",
    "referencias", "references", "bibliografía", "bibliography",
    "palabras clave", "palabras claves", "palabras-clave",
    "keywords", "key words", "mots clés",
    "summary", "resumo",
    "fundamentación", "fundamentacion",
    "justificación", "justificacion",
    "marco teórico", "marco teorico", "marco conceptual",
    "antecedentes",
    "desarrollo",
    "planteamiento", "planteamiento del problema",
    "conclusión", "conclusiones", "conclusion", "conclusions",
    "anexos", "anexo", "apéndice", "apendice",
}
_PAGE_MARKER      = re.compile(r"^(x{0,3})(ix|iv|v?i{0,3})\s*$|^\d{1,4}\s*$", re.IGNORECASE)
_NUMBERED_SECTION = re.compile(r"^\d{1,2}(?:\.\d{1,2})*[\.\-–—]?\s*(.*)", re.UNICODE)
_KEYWORDS_PREFIX  = re.compile(
    r"^(palabras?\s*claves?|keywords?|key\s+words?|mots[- ]cl[eé]s?)\s*[:\-–]",
    re.IGNORECASE,
)
_TOC_INLINE = re.compile(
    r"^[\s\.……\-]*[\d ivxlcdmIVXLCDM]*[\s\.…]*$|^\(cid:",
    re.IGNORECASE,
)
_MAX_ABSTRACT_CHARS = 6000
_REPOSITORY_METADATA_LINE = re.compile(
    r"^(multimedia)$|https?://|www\.|sedici\.unlp",
    re.IGNORECASE,
)


def _is_numbered_section_stop(line: str) -> bool:
    m = _NUMBERED_SECTION.match(line)
    if not m:
        return False
    after = m.group(1).strip().lower()
    if after in _ABSTRACT_STOP_HEADINGS:
        return True
    for h in _ABSTRACT_STOP_HEADINGS:
        if after.startswith(h + " ") or after.startswith(h + ":"):
            return True
    return bool(_KEYWORDS_PREFIX.match(after))


def _collect_after_heading(lines: list, start_idx: int) -> str:
    parts = []
    total = 0
    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped:
            if parts and parts[-1] == "":
                break
            parts.append("")
            continue
        if _PAGE_MARKER.match(stripped):
            last_text = next((p for p in reversed(parts) if p), "")
            if not last_text or last_text[-1] in ".!?:;":
                continue
            if last_text[-1].isalpha():
                for idx in range(len(parts) - 1, -1, -1):
                    if parts[idx]:
                        parts[idx] += stripped
                        total += len(stripped)
                        break
                continue
        if stripped.lower() in _ABSTRACT_STOP_HEADINGS:
            break
        if _is_numbered_section_stop(stripped):
            break
        if _KEYWORDS_PREFIX.match(stripped):
            break
        parts.append(stripped)
        total += len(stripped)
        if total >= _MAX_ABSTRACT_CHARS:
            break
    return " ".join(p for p in parts if p).strip()


def _is_toc_match(first_part: str) -> bool:
    return not first_part or bool(_TOC_INLINE.match(first_part))


def _is_heading_text(text: str) -> bool:
    words = [w for w in text.split() if w.isalpha()]
    return len(words) >= 2 and all(w.isupper() for w in words)


def _starts_with_uppercase(text: str) -> bool:
    for ch in text:
        if ch.isalpha():
            return ch.isupper()
    return True


def _try_extract(lines: list, heading_re, inline_re) -> str:
    for i, line in enumerate(lines):
        m = inline_re.match(line.strip())
        if m:
            first_part = m.group(2).strip()
            if _is_toc_match(first_part) or _is_heading_text(first_part):
                continue
            rest = _collect_after_heading(lines, i + 1)
            result = (first_part + " " + rest).strip()
            if not _starts_with_uppercase(result):
                continue
            if result:
                return result
    for i, line in enumerate(lines):
        if heading_re.match(line.strip()):
            result = _collect_after_heading(lines, i + 1)
            if not _starts_with_uppercase(result):
                continue
            if result:
                return result
    return ""


def extract_abstract(text: str) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    result = _try_extract(lines, _SPANISH_ABSTRACT_HEADINGS, _SPANISH_ABSTRACT_INLINE)
    if result:
        return result
    return _try_extract(lines, _ABSTRACT_HEADINGS, _ABSTRACT_INLINE)


# ── Text extraction strategies ────────────────────────────────────────────────

def _api_text(pdf_path: Path) -> str:
    """Call extractor API and return plain text."""
    raw = make_requests_only_text(file_path=pdf_path, token=TOKEN, normalization=True, ocr=False)
    try:
        return json.loads(raw).get("data", {}).get("text", "") or ""
    except Exception:
        return raw or ""


def _multicolumn_text(pdf_path: Path) -> str:
    """Extract text column-by-column using pdfplumber."""
    page_texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            result = detect_page_columns(page)
            n_cols = result["columns"]
            if n_cols > 1:
                split_x = result["method_b"].get("split_x")
                text = _extract_page_columns(page, split_x, n_cols)
            else:
                text = page.extract_text() or ""
            page_texts.append(text)
    return "\n\n".join(page_texts)


def _extract_page_columns(page, split_x, n_cols: int) -> str:
    """
    Sort words into lines (2pt y-buckets), assign each word to a column by
    x-center, build one text list per column, then concat col1 + col2 + ...
    """
    words = page.extract_words(extra_attrs=["fontname", "size"])
    if not words:
        return page.extract_text() or ""

    if not split_x:
        # Fallback: evenly divide
        split_xs = [page.width * i / n_cols for i in range(1, n_cols)]
    else:
        split_xs = [split_x] if n_cols == 2 else [page.width * i / n_cols for i in range(1, n_cols)]

    boundaries = [0.0] + split_xs + [float(page.width)]
    body_size = _dominant_body_font_size(words, page)

    line_map: dict[int, list] = defaultdict(list)
    for w in words:
        y_key = round(w["top"] / 2) * 2
        line_map[y_key].append(w)

    col_lines: list[list[str]] = [[] for _ in range(n_cols)]

    for y_key in sorted(line_map):
        line_words = sorted(line_map[y_key], key=lambda w: w["x0"])
        line_text = " ".join(w["text"] for w in line_words)
        if _skip_non_abstract_layout_line(line_text, line_words, page, body_size):
            continue
        if _is_full_width_line(line_words, page, split_xs):
            col_lines[0].append(line_text)
            continue

        col_word_groups: list[list[str]] = [[] for _ in range(n_cols)]
        for w in line_words:
            x_center = (w["x0"] + w["x1"]) / 2
            col_idx = n_cols - 1
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


def _dominant_body_font_size(words: list, page) -> float | None:
    candidates = []
    for w in words:
        text = w["text"].strip()
        if not text or _REPOSITORY_METADATA_LINE.search(text):
            continue
        if w["top"] < page.height * 0.08 or w["bottom"] > page.height * 0.92:
            continue
        size = w.get("size")
        if size:
            candidates.append(round(float(size) * 2) / 2)
    if not candidates:
        return None
    return Counter(candidates).most_common(1)[0][0]


def _is_abstract_control_line(text: str) -> bool:
    stripped = text.strip()
    lowered = stripped.lower()
    return (
        bool(_ABSTRACT_HEADINGS.match(stripped))
        or bool(_ABSTRACT_INLINE.match(stripped))
        or lowered in _ABSTRACT_STOP_HEADINGS
        or _is_numbered_section_stop(stripped)
        or bool(_KEYWORDS_PREFIX.match(stripped))
    )


def _skip_non_abstract_layout_line(text: str, words: list, page, body_size: float | None) -> bool:
    stripped = text.strip()
    if not stripped:
        return False

    top = min(w["top"] for w in words)
    bottom = max(w["bottom"] for w in words)
    if bottom >= page.height * 0.94:
        return True
    if _REPOSITORY_METADATA_LINE.search(stripped):
        return True
    if _is_abstract_control_line(stripped):
        return False

    if body_size is None:
        return False

    avg_size = sum(float(w.get("size") or body_size) for w in words) / len(words)
    word_count = len([w for w in words if w["text"].strip()])
    return (
        top > page.height * 0.35
        and word_count <= 4
        and avg_size >= body_size + 2.0
    )


def _is_full_width_line(words: list, page, split_xs: list[float]) -> bool:
    if not split_xs or len(words) < 2:
        return False

    min_x = min(w["x0"] for w in words)
    max_x = max(w["x1"] for w in words)
    crosses_split = any(min_x < split_x < max_x for split_x in split_xs)
    if not crosses_split:
        return False

    sorted_words = sorted(words, key=lambda w: w["x0"])
    column_gap_threshold = max(20.0, page.width * 0.035)
    for left, right in zip(sorted_words, sorted_words[1:]):
        gap = right["x0"] - left["x1"]
        if gap >= column_gap_threshold and any(left["x1"] <= split_x <= right["x0"] for split_x in split_xs):
            return False

    return True


def _smart_text(pdf_path: Path, detection_cache: dict) -> str:
    """
    Route extraction based on layout detection:
      multi-column → local column extraction
      single-column → extractor API
    """
    doc_id = pdf_path.stem
    if doc_id not in detection_cache:
        detection_cache[doc_id] = detect_pdf_columns(pdf_path)
    det = detection_cache[doc_id]

    if det["is_multicolumn"]:
        return _multicolumn_text(pdf_path)
    return _api_text(pdf_path)


# ── Scoring ───────────────────────────────────────────────────────────────────

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.strip(), b.strip()).ratio()


def score_result(gt: str, extracted: str) -> str:
    gt_null  = not gt
    ext_null = not extracted
    if gt_null and ext_null:
        return "null-null"
    if gt_null and not ext_null:
        return "false-pos"
    if not gt_null and ext_null:
        return "false-neg"
    sim = similarity(gt, extracted)
    if gt.strip() == extracted.strip():
        return "exact"
    if sim >= 0.8:
        return "high"
    if sim >= 0.5:
        return "close"
    return "poor"


SCORE_ORDER = ["null-null", "exact", "high", "close", "poor", "false-neg", "false-pos"]
SCORE_LABEL = {
    "null-null":  "Both null (correct)       ",
    "exact":      "Exact match               ",
    "high":       "High  (0.8 ≤ sim < 1.0)  ",
    "close":      "Close (0.5 ≤ sim < 0.8)  ",
    "poor":       "Poor  (sim < 0.5)         ",
    "false-neg":  "Missed (GT has, we got '') ",
    "false-pos":  "False pos (we got, GT null)",
}
GOOD_SCORES = {"null-null", "exact", "high"}


def tally(scores: dict[str, str]) -> dict[str, int]:
    counts: dict[str, int] = {k: 0 for k in SCORE_ORDER}
    for s in scores.values():
        counts[s] = counts.get(s, 0) + 1
    return counts


def _rounded_similarity(gt: str, extracted: str) -> float:
    return round(similarity(gt, extracted), 4)


def write_per_doc_json(
    ids: list[str],
    data: dict,
    baseline_results: dict[str, dict],
    smart_results: dict[str, dict],
    detection_cache: dict,
) -> None:
    rows = []
    baseline_sims = []
    smart_sims = []

    for doc_id in ids:
        gt = data[doc_id].get("abstract") or ""
        baseline = baseline_results.get(doc_id, {})
        smart = smart_results.get(doc_id, {})
        baseline_abstract = baseline.get("abstract", "")
        smart_abstract = smart.get("abstract", "")
        baseline_similarity = _rounded_similarity(gt, baseline_abstract)
        smart_similarity = _rounded_similarity(gt, smart_abstract)

        baseline_sims.append(baseline_similarity)
        smart_sims.append(smart_similarity)

        rows.append({
            "id": doc_id,
            "is_multicolumn": detection_cache.get(doc_id, {}).get("is_multicolumn", False),
            "abstract_original": gt,
            "abstract_without_multiline": baseline_abstract,
            "abstract_with_multiline": smart_abstract,
            "similarity_without_multiline": baseline_similarity,
            "similarity_with_multiline": smart_similarity,
            "avg_without_multiline_with_original": baseline_similarity,
            "avg_with_multiline_with_original": smart_similarity,
            "avg_similarity_with_original": round((baseline_similarity + smart_similarity) / 2, 4),
            "score_without_multiline": baseline.get("score", "skip"),
            "score_with_multiline": smart.get("score", "skip"),
        })

    payload = {
        "summary": {
            "n": len(rows),
            "avg_similarity_without_multiline": round(sum(baseline_sims) / len(baseline_sims), 4) if baseline_sims else 0.0,
            "avg_similarity_with_multiline": round(sum(smart_sims) / len(smart_sims), 4) if smart_sims else 0.0,
        },
        "items": rows,
    }

    PER_DOC_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PER_DOC_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# ── Loop runner ───────────────────────────────────────────────────────────────

def run_loop(ids: list[str], data: dict, extract_fn, label: str, detection_cache: dict | None = None) -> dict[str, dict]:
    """
    Run one extraction loop over all doc IDs.
    Returns a dict of {doc_id: {score, abstract}}.
    """
    print(f"\n{'='*70}")
    print(f"LOOP: {label}")
    print(f"{'='*70}")

    results: dict[str, dict] = {}
    for doc_id in ids:
        pdf_path = PDF_FOLDER / f"{doc_id}.pdf"
        if not pdf_path.exists():
            print(f"  [SKIP] {doc_id} — PDF not found")
            results[doc_id] = {"score": "skip", "abstract": ""}
            continue

        if detection_cache is not None:
            text = extract_fn(pdf_path, detection_cache)
        else:
            text = extract_fn(pdf_path)

        abstract  = extract_abstract(text)
        gt        = data[doc_id].get("abstract") or ""
        score     = score_result(gt, abstract)
        results[doc_id] = {"score": score, "abstract": abstract}

        tag = "[OK]  " if score in GOOD_SCORES else "[MISS]"
        if score == "false-pos":
            tag = "[FP]  "
        preview = (abstract or text)[:100].replace("\n", " ")
        print(f"  {tag} {doc_id} ({score}): {preview}")

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with open(FINAL_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    ids = list(data.keys())
    print(f"Documents: {len(ids)}")

    # Pre-compute layout detection once (shared between loops)
    print("\nDetecting layout for all documents...")
    detection_cache: dict = {}
    multi_ids = []
    for doc_id in ids:
        pdf_path = PDF_FOLDER / f"{doc_id}.pdf"
        if pdf_path.exists():
            det = detect_pdf_columns(pdf_path)
            detection_cache[doc_id] = det
            if det["is_multicolumn"]:
                multi_ids.append(doc_id)
    print(f"Multi-column docs detected: {len(multi_ids)}/{len(ids)}  {multi_ids}")

    # Loop 1: baseline — API for everything
    baseline_results = run_loop(ids, data, _api_text, "BASELINE (API for all docs)")
    scores_baseline = {doc_id: row["score"] for doc_id, row in baseline_results.items()}

    # Loop 2: smart — column extraction for multi-col, API for single-col
    smart_results = run_loop(
        ids, data,
        _smart_text,
        "SMART (column extraction for multi-col docs)",
        detection_cache=detection_cache,
    )
    scores_smart = {doc_id: row["score"] for doc_id, row in smart_results.items()}

    write_per_doc_json(ids, data, baseline_results, smart_results, detection_cache)
    print(f"\nPer-doc JSON written to: {PER_DOC_JSON_PATH}")

    # ── Side-by-side scorecard ────────────────────────────────────────────────
    total   = len(ids)
    t_base  = tally(scores_baseline)
    t_smart = tally(scores_smart)

    good_base  = sum(t_base[s]  for s in GOOD_SCORES)
    good_smart = sum(t_smart[s] for s in GOOD_SCORES)

    print(f"\n{'='*70}")
    print(f"SCORECARD  (n={total})")
    print(f"{'='*70}")
    print(f"{'Category':<30} {'Baseline':>10} {'Smart':>10} {'Delta':>8}")
    print(f"{'-'*30} {'-'*10} {'-'*10} {'-'*8}")
    for s in SCORE_ORDER:
        b = t_base[s]
        sm = t_smart[s]
        delta = sm - b
        sign  = "+" if delta > 0 else ""
        print(f"  {SCORE_LABEL[s]} {b:>8}   {sm:>8}   {sign}{delta:>5}")
    print(f"{'-'*30} {'-'*10} {'-'*10} {'-'*8}")
    b_pct  = good_base  / total * 100
    sm_pct = good_smart / total * 100
    print(f"  {'GOOD (null+exact+high)':<28} {good_base:>8}   {good_smart:>8}   "
          f"{'+' if good_smart >= good_base else ''}{good_smart - good_base:>5}")
    print(f"  {'  %':<28} {b_pct:>7.1f}%  {sm_pct:>7.1f}%")

    # ── Per-doc deltas ────────────────────────────────────────────────────────
    improved  = []
    regressed = []

    def _rank(s: str) -> int:
        return SCORE_ORDER.index(s) if s in SCORE_ORDER else len(SCORE_ORDER)

    for doc_id in ids:
        b  = scores_baseline.get(doc_id, "skip")
        sm = scores_smart.get(doc_id, "skip")
        if b == sm:
            continue
        rb, rs = _rank(b), _rank(sm)
        if rs < rb:
            improved.append((doc_id, b, sm))
        elif rs > rb:
            regressed.append((doc_id, b, sm))

    if improved:
        print(f"\nIMPROVED by multicolumn extraction ({len(improved)} docs):")
        for doc_id, before, after in improved:
            is_multi = detection_cache.get(doc_id, {}).get("is_multicolumn", False)
            print(f"  {doc_id}  {'[multi]' if is_multi else '[single]'}  {before} → {after}")

    if regressed:
        print(f"\nREGRESSED ({len(regressed)} docs):")
        for doc_id, before, after in regressed:
            is_multi = detection_cache.get(doc_id, {}).get("is_multicolumn", False)
            print(f"  {doc_id}  {'[multi]' if is_multi else '[single]'}  {before} → {after}")

    if not improved and not regressed:
        print("\nNo per-doc changes between baseline and smart extraction.")
