"""
Abstract extraction — compares strategies on plain text scored against
CSV ground truth (dc.description.abstract).

Strategies:
  A_standalone — heading alone on its own line, regex end detection.
  B_regex      — inline or standalone heading, regex stop-words end detection.
  B_ml         — inline or standalone heading, semantic (MiniLM) end detection.
                 Splits text into paragraphs; stops when cosine similarity to
                 the first paragraph drops below ML_THRESHOLD.

Run from repo root:
    python extras/abstract_extraction/main.py
"""

import csv
import re
import sys
from pathlib import Path
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent.parent))
from constants import TXT_NO_TAGS_FOLDER, CSV_FOLDER

# ── Config ────────────────────────────────────────────────────────────────────
N_PER_TYPE    = 20
CSV_TYPES     = CSV_FOLDER / "types.csv"
CSV_MAIN      = CSV_FOLDER / "sedici.csv"
TYPES         = ["Libro", "Tesis", "Articulo", "Objeto de conferencia"]
RESULTS_CSV   = Path(__file__).parent / "results.csv"
PREVIEW_CHARS = None        # None = full text saved in CSV (no truncation)
ML_THRESHOLD  = 0.30        # cosine similarity below this → new section detected
ML_DEBUG      = True        # print similarity score per paragraph (set False after tuning)
ML_MODEL_NAME = "all-MiniLM-L6-v2"

# ── Optional ML import ────────────────────────────────────────────────────────
try:
    from sentence_transformers import SentenceTransformer as _ST
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    print("[WARN] sentence-transformers not installed — B_ml will be skipped.")

# ── Abstract heading patterns ─────────────────────────────────────────────────
_ABSTRACT_WORDS = r"(resumen|abstract|summary|resumo|abstracto|r[eé]sum[eé]|resúmen)"
_NUM_PREFIX     = r"(?:\d{1,2}\s*[\.\-–—]\s*)?"   # optional "1- " / "1. " / "2- " etc.

ABSTRACT_HEADINGS = re.compile(
    r"^" + _NUM_PREFIX + _ABSTRACT_WORDS + r"[.:\-–—]?\s*$",
    re.IGNORECASE,
)

ABSTRACT_INLINE = re.compile(
    r"^" + _NUM_PREFIX + _ABSTRACT_WORDS + r"\s*[.:\-–—]?\s+(.*)",
    re.IGNORECASE | re.DOTALL,
)

# ── Stop headings (regex strategy only) ──────────────────────────────────────
STOP_HEADINGS = {
    "introducción", "introduction", "introdução", "introducao",
    "índice", "indice", "index", "contenido", "contents", "tabla de contenidos",
    "capítulo 1", "chapter 1", "1. introducción", "1. introduction",
    "objetivos", "objectives", "metodología", "methodology",
    "materiales y métodos", "materials and methods",
    "agradecimientos", "acknowledgements", "acknowledgments",
    "referencias", "references", "bibliografía", "bibliography",
    "palabras clave", "palabras claves", "palabras-clave",
    "keywords", "key words", "mots clés",
    "summary", "resumo",   # bilingual docs: Spanish abstract followed by English/Portuguese
    # Common Spanish academic section headings that follow the abstract
    "fundamentación", "fundamentacion",
    "justificación", "justificacion",
    "marco teórico", "marco teorico", "marco conceptual",
    "antecedentes",
    "desarrollo",
    "planteamiento", "planteamiento del problema",
    "conclusión", "conclusiones", "conclusion", "conclusions",
    "anexos", "anexo", "apéndice", "apendice",
}

PAGE_MARKER = re.compile(r"^(x{0,3})(ix|iv|v?i{0,3})\s*$|^\d{1,4}\s*$", re.IGNORECASE)

# Captures text after the number: "1 Introduction", "2-Intro", "3. Title"
# [\.\-–—]? allows dot, dash or em-dash as separator (with optional surrounding spaces)
NUMBERED_SECTION = re.compile(r"^\d{1,2}(?:\.\d{1,2})*[\.\-–—]?\s*(.*)", re.UNICODE)

def _is_numbered_section_stop(line: str) -> bool:
    """
    Returns True only when line is a numbered heading AND the text after the
    number matches a known stop heading.
    e.g. "1 Introduction" → True,  "1.2 students surveyed" → False
    """
    m = NUMBERED_SECTION.match(line)
    if not m:
        return False
    after = m.group(1).strip().lower()
    if after in STOP_HEADINGS:
        return True
    for h in STOP_HEADINGS:
        if after.startswith(h + " ") or after.startswith(h + ":"):
            return True
    if KEYWORDS_PREFIX.match(after):
        return True
    return False

# Keywords heading even when inline: "Palabras Clave: ...", "Keywords: ..."
KEYWORDS_PREFIX = re.compile(
    r"^(palabras?\s*claves?|keywords?|key\s+words?|mots[- ]cl[eé]s?)\s*[:\-–]",
    re.IGNORECASE,
)

# TOC entry: heading followed by dots/spaces/page number/roman numeral/cid artifacts
# e.g. "Resumen …………. 4", "Resumen ii", "RESUMEN (cid:171)..."
TOC_INLINE = re.compile(
    r"^[\s\.…\u2026\-]*[\d ivxlcdmIVXLCDM]*[\s\.…]*$"   # dots + optional page
    r"|^\(cid:",                                            # PDF encoding artifact
    re.IGNORECASE,
)

MAX_ABSTRACT_CHARS = 4000


# ── Scoring ───────────────────────────────────────────────────────────────────

def token_overlap(pred: str, truth: str) -> float:
    """ROUGE-1 recall: fraction of truth tokens present in prediction."""
    if not truth or not pred:
        return 0.0
    pred_tok  = set(re.findall(r"\w+", pred.lower()))
    truth_tok = set(re.findall(r"\w+", truth.lower()))
    if not truth_tok:
        return 0.0
    return len(pred_tok & truth_tok) / len(truth_tok)


# ── Data loading ──────────────────────────────────────────────────────────────

def load_ground_truth() -> dict:
    gt = {}
    abstract_cols = [
        "dc.description.abstract",
        "dc.description.abstract[es]",
        "dc.description.abstract[en]",
        "dc.description.abstract[pt]",
    ]
    with open(CSV_MAIN, encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            for col in abstract_cols:
                val = row.get(col, "").strip()
                if val:
                    gt[row["id"].strip()] = val
                    break
    return gt


def load_subset() -> list[dict]:
    files = {f.stem for f in TXT_NO_TAGS_FOLDER.iterdir() if f.suffix == ".txt"}
    by_type: dict[str, list] = defaultdict(list)
    with open(CSV_TYPES, encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            full_id  = row["id"].strip()
            doc_type = row["type"].strip()
            if full_id in files and doc_type in TYPES:
                by_type[doc_type].append(full_id)
    subset = []
    for doc_type in TYPES:
        for full_id in by_type[doc_type][:N_PER_TYPE]:
            numeric_id = full_id.split("-")[1] if "-" in full_id else full_id
            subset.append({
                "id":      numeric_id,
                "full_id": full_id,
                "type":    doc_type,
                "path":    TXT_NO_TAGS_FOLDER / f"{full_id}.txt",
            })
    return subset


# ── Regex collector (line by line, STOP_HEADINGS) ────────────────────────────

def _collect_after_heading_regex(lines: list[str], start_idx: int) -> str:
    """
    Collect lines until a STOP_HEADING, double blank line, or MAX_ABSTRACT_CHARS.
    Used by A_standalone and B_regex.
    """
    parts = []
    total = 0
    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped:
            if parts and parts[-1] == "":
                break
            parts.append("")
            continue
        if PAGE_MARKER.match(stripped):
            continue
        if stripped.lower() in STOP_HEADINGS:
            break
        if _is_numbered_section_stop(stripped):
            break
        if KEYWORDS_PREFIX.match(stripped):
            break
        parts.append(stripped)
        total += len(stripped)
        if total >= MAX_ABSTRACT_CHARS:
            break
    return " ".join(p for p in parts if p).strip()


# ── ML collector (paragraph by paragraph, semantic coherence) ─────────────────

def _lines_to_paragraphs(lines: list[str], start_idx: int) -> list[str]:
    """Split lines into paragraph strings, skipping page markers."""
    paragraphs = []
    current: list[str] = []
    for line in lines[start_idx:]:
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
        elif not PAGE_MARKER.match(stripped):
            current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def _collect_after_heading_ml(lines: list[str], start_idx: int,
                               model, threshold: float) -> str:
    """
    Paragraph-level semantic collection:
    1. Encode the first paragraph as the anchor.
    2. For each following paragraph compute cosine similarity to the anchor.
    3. Stop when similarity < threshold (topic shifted → new section).

    Does NOT use STOP_HEADINGS — the ML signal drives everything.
    """
    from numpy import dot as _dot
    from numpy.linalg import norm as _norm

    paragraphs = _lines_to_paragraphs(lines, start_idx)
    if not paragraphs:
        return ""

    anchor_emb = model.encode([paragraphs[0]])[0]
    selected   = [paragraphs[0]]
    total      = len(paragraphs[0])

    for para in paragraphs[1:]:
        cand_emb = model.encode([para])[0]
        a, c     = anchor_emb, cand_emb
        sim      = float(_dot(a, c) / (_norm(a) * _norm(c) + 1e-8))
        if ML_DEBUG:
            preview = para[:60].replace("\n", " ")
            print(f"    [ML sim={sim:.3f} thr={threshold:.2f}] {preview}")
        if sim < threshold:
            break
        selected.append(para)
        total += len(para)
        if total >= MAX_ABSTRACT_CHARS:
            break

    return " ".join(selected)


# ── Strategies ────────────────────────────────────────────────────────────────

def strategy_a_standalone(text: str) -> str:
    """Standalone heading on its own line + regex end detection."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if ABSTRACT_HEADINGS.match(line.strip()):
            result = _collect_after_heading_regex(lines, i + 1)
            if result:
                return result
    return ""


def _is_toc_match(first_part: str) -> bool:
    """Returns True if the text after the abstract heading looks like a TOC entry."""
    return not first_part or bool(TOC_INLINE.match(first_part))


def strategy_b_regex(text: str) -> str:
    """Inline or standalone heading + regex (STOP_HEADINGS) end detection.
    Skips TOC entries where the heading is followed by dots/page numbers."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = ABSTRACT_INLINE.match(line.strip())
        if m:
            first_part = m.group(2).strip()
            if _is_toc_match(first_part):
                continue   # skip TOC entry, keep searching
            rest = _collect_after_heading_regex(lines, i + 1)
            return (first_part + " " + rest).strip()
    return strategy_a_standalone(text)


def strategy_b_ml(text: str, model, threshold: float = ML_THRESHOLD) -> str:
    """
    Inline or standalone heading + semantic (MiniLM) end detection.
    The first paragraph after the heading is the anchor; each subsequent
    paragraph is compared to it — collection stops when similarity drops.
    """
    if model is None:
        return ""
    lines = text.splitlines()

    # Try inline heading first
    for i, line in enumerate(lines):
        m = ABSTRACT_INLINE.match(line.strip())
        if m:
            first_part = m.group(2).strip()
            if _is_toc_match(first_part):
                continue   # skip TOC entry, keep searching
            # Prepend first_part so it becomes part of the first paragraph
            remaining = ([first_part] if first_part else []) + list(lines[i + 1:])
            return _collect_after_heading_ml(remaining, 0, model, threshold)

    # Fallback: standalone heading
    for i, line in enumerate(lines):
        if ABSTRACT_HEADINGS.match(line.strip()):
            result = _collect_after_heading_ml(lines, i + 1, model, threshold)
            if result:
                return result
    return ""


# ── Main ──────────────────────────────────────────────────────────────────────

STRATEGY_NAMES = ["A_standalone", "B_regex", "B_ml"]


def run():
    print("Loading ground truth from sedici.csv…")
    gt = load_ground_truth()
    print(f"  Ground truth abstracts loaded: {len(gt)}")

    ml_model = None
    if ST_AVAILABLE:
        print(f"\nLoading sentence model ({ML_MODEL_NAME})…")
        try:
            ml_model = _ST(ML_MODEL_NAME)
            print("  ready.")
        except Exception as e:
            print(f"  [WARN] {e}")

    print(f"\nLoading subset ({N_PER_TYPE} per type × {len(TYPES)} types)…")
    subset = load_subset()
    print(f"  Total docs: {len(subset)}")

    scores_by_strategy: dict[str, list[float]] = {k: [] for k in STRATEGY_NAMES}
    found_by_strategy:  dict[str, int]         = {k: 0  for k in STRATEGY_NAMES}
    rows: list[dict] = []

    print("\n" + "=" * 90)

    for doc in subset:
        truth = gt.get(doc["id"], "")
        try:
            text = doc["path"].read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        results = {
            "A_standalone": strategy_a_standalone(text),
            "B_regex":      strategy_b_regex(text),
            "B_ml":         strategy_b_ml(text, ml_model),
        }

        print(f"\n[{doc['type']}] {doc['full_id']}  (truth: {len(truth)} chars)")

        row:    dict = {"fileid": doc["full_id"], "type": doc["type"]}
        scores: dict = {}
        for name in STRATEGY_NAMES:
            extracted = results[name]
            score_val = round(token_overlap(extracted, truth), 3)
            scores_by_strategy[name].append(score_val)
            if extracted:
                found_by_strategy[name] += 1
            preview = extracted[:120].replace("\n", " ") if extracted else "(nothing)"
            print(f"  {name:15s}  score={score_val:.3f}  preview: {preview}")
            row[f"{name}_extract"] = (
                extracted if PREVIEW_CHARS is None else extracted[:PREVIEW_CHARS]
            ).replace("\n", " ")
            scores[f"{name}_score"] = score_val

        row["ground_truth"] = (
            truth if PREVIEW_CHARS is None else truth[:PREVIEW_CHARS]
        ).replace("\n", " ")
        row.update(scores)
        rows.append(row)

    # ── Summary ───────────────────────────────────────────────────────────────
    total = len(subset)
    print("\n" + "=" * 90)
    print(f"SUMMARY  ({total} docs, {N_PER_TYPE}/type)\n")
    print(f"  {'Strategy':<18} {'Found':>6} {'Found%':>7} {'Avg ROUGE-1 recall':>20}")
    print(f"  {'-'*18} {'-'*6} {'-'*7} {'-'*20}")
    for name in STRATEGY_NAMES:
        sc  = scores_by_strategy[name]
        avg = sum(sc) / len(sc) if sc else 0.0
        pct = 100 * found_by_strategy[name] / total if total else 0
        print(f"  {name:<18} {found_by_strategy[name]:>6} {pct:>6.1f}% {avg:>20.3f}")
    print()

    # ── Save CSV ──────────────────────────────────────────────────────────────
    if rows:
        with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"Saved → {RESULTS_CSV}")


# Alias for backwards-compatible imports (keywords_extraction uses this name)
strategy_b_inline = strategy_b_regex


if __name__ == "__main__":
    run()
