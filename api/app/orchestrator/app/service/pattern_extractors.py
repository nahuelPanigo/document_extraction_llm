"""
Pattern-based extraction of abstract and keywords from plain text.

Strategies:
  extract_abstract(text)              — regex heading detection (strategy_b_regex)
  extract_keywords_regex(text)        — explicit 'Keywords:' section regex
  extract_keywords_tfidf(text, vec)   — PMI-vocabulary TF-IDF ranking
  load_vectorizer(path)               — load pickled TfidfVectorizer
"""

import pickle
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher
from pathlib import Path

# ── Optional sklearn / nltk imports ──────────────────────────────────────────

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from nltk.stem import SnowballStemmer
    import nltk
    for _pkg in ("stopwords", "punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{_pkg}" if "punkt" in _pkg else f"corpora/{_pkg}")
        except LookupError:
            nltk.download(_pkg, quiet=True)
    from nltk.corpus import stopwords as _nltk_sw
    _STOPWORDS = set(_nltk_sw.words("spanish")) | set(_nltk_sw.words("english"))
    _STOPWORDS.update({
        "también", "así", "través", "puede", "pueden", "debe", "deben",
        "este", "esta", "estos", "estas", "dicho", "dichos", "dicha", "dichas",
        "mismo", "misma", "mismos", "mismas", "solo", "sólo", "siendo", "sido",
        "según", "cada", "todo", "toda", "todos", "todas",
    })
    _STEMMER = SnowballStemmer("spanish")
    NLTK_AVAILABLE = True
except Exception:
    NLTK_AVAILABLE = False
    _STOPWORDS = set()
    _STEMMER = None


# ═══════════════════════════════════════════════════════════════════════════════
# ABSTRACT EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

_ABSTRACT_WORDS = r"(resumen|abstract|summary|resumo|abstracto|r[eé]sum[eé]|resúmen)"
_NUM_PREFIX     = r"(?:\d{1,2}\s*[\.\-–—]\s*)?"

_ABSTRACT_HEADINGS = re.compile(
    r"^" + _NUM_PREFIX + _ABSTRACT_WORDS + r"[.:\-–—]?\s*$",
    re.IGNORECASE,
)
_ABSTRACT_INLINE = re.compile(
    r"^" + _NUM_PREFIX + _ABSTRACT_WORDS + r"\s*[.:\-–—]?\s+(.*)",
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
_PAGE_MARKER = re.compile(r"^(x{0,3})(ix|iv|v?i{0,3})\s*$|^\d{1,4}\s*$", re.IGNORECASE)
_NUMBERED_SECTION = re.compile(r"^\d{1,2}(?:\.\d{1,2})*[\.\-–—]?\s*(.*)", re.UNICODE)
_KEYWORDS_PREFIX = re.compile(
    r"^(palabras?\s*claves?|keywords?|key\s+words?|mots[- ]cl[eé]s?)\s*[:\-–]",
    re.IGNORECASE,
)
_TOC_INLINE = re.compile(
    r"^[\s\.…\u2026\-]*[\d ivxlcdmIVXLCDM]*[\s\.…]*$"
    r"|^\(cid:",
    re.IGNORECASE,
)
_MAX_ABSTRACT_CHARS = 4000


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


def extract_abstract(text: str) -> str:
    """
    Extract abstract from plain text using regex heading detection.
    Returns empty string if not found.
    """
    if not text:
        return ""
    lines = text.splitlines()
    # Try inline heading first
    for i, line in enumerate(lines):
        m = _ABSTRACT_INLINE.match(line.strip())
        if m:
            first_part = m.group(2).strip()
            if _is_toc_match(first_part):
                continue
            rest = _collect_after_heading(lines, i + 1)
            return (first_part + " " + rest).strip()
    # Fallback: standalone heading
    for i, line in enumerate(lines):
        if _ABSTRACT_HEADINGS.match(line.strip()):
            result = _collect_after_heading(lines, i + 1)
            if result:
                return result
    return ""


# ═══════════════════════════════════════════════════════════════════════════════
# KEYWORDS — REGEX
# ═══════════════════════════════════════════════════════════════════════════════

_KW_HEADING = re.compile(
    r"^(keywords?|palabras?\s+claves?|key\s+words?|mots[- ]cl[eé]s?|"
    r"parole\s+chiave|palavras?[- ]chave)\s*[:\-–—]?\s*(.*)",
    re.IGNORECASE,
)
_BILINGUAL_SUFFIX = re.compile(
    r"^(keywords?|palabras?\s+claves?|key\s+words?|conclusiones?|"
    r"resumen|abstract|summary|resumo)\s*$",
    re.IGNORECASE,
)
_KW_STOP_HEADINGS = {
    "abstract", "resumen", "summary", "resumo",
    "introducción", "introduction", "introdução",
    "1.", "references", "referencias",
}
_KW_SPLIT = re.compile(r"[,;|•·]|\s[-/]\s|\.\s+")


def extract_keywords_regex(text: str) -> list:
    """
    Extract keywords from an explicit 'Keywords:' / 'Palabras clave:' section.
    Returns list of keyword strings, or empty list if not found.
    """
    if not text:
        return []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = _KW_HEADING.match(line.strip())
        if not m:
            continue
        first = m.group(2).strip()
        if first and _BILINGUAL_SUFFIX.match(first):
            first = ""
        if first and len(first) <= 120:
            raw = first
        else:
            collected = []
            for follow in lines[i + 1: i + 6]:
                stripped = follow.strip()
                if not stripped:
                    break
                if stripped.lower().rstrip(".:") in _KW_STOP_HEADINGS:
                    break
                if len(stripped) > 120:
                    break
                collected.append(stripped)
            raw = " ".join(collected)
        if not raw:
            continue
        terms = [t.strip() for t in _KW_SPLIT.split(raw) if t.strip()]
        terms = [t for t in terms if 1 <= len(t.split()) <= 6 and len(t) <= 80]
        if terms:
            return terms
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# KEYWORDS — TF-IDF
# ═══════════════════════════════════════════════════════════════════════════════

_TOP_N_TFIDF = 10
_BIGRAM_BOOST = 1.7
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_TOK_RE = re.compile(r"(?u)\b[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{4,}\b")


def _strip_urls(text: str) -> str:
    return _URL_RE.sub(" ", text)


def _stem(term: str) -> str:
    if _STEMMER is None:
        return term.lower()
    return " ".join(_STEMMER.stem(w) for w in term.lower().split())


def extract_keywords_tfidf(text: str, vectorizer) -> list:
    """
    Extract keywords using pre-built TF-IDF vectorizer with PMI vocabulary.
    Returns list of up to 10 keyword strings.
    Requires sklearn + nltk to be available.
    """
    if not text or vectorizer is None or not SKLEARN_AVAILABLE or not NLTK_AVAILABLE:
        return []
    try:
        clean = _strip_urls(text)
        vec = vectorizer.transform([clean])
        names = vectorizer.get_feature_names_out()
        scores = vec.toarray()[0]

        words_in_doc = _TOK_RE.findall(clean.lower())
        raw_tf = Counter(words_in_doc)
        bigram_tf = Counter(zip(words_in_doc, words_in_doc[1:]))
        MIN_DOC_FREQ = 2

        def _raw_count(term: str) -> int:
            parts = term.split()
            if len(parts) == 1:
                return raw_tf.get(term, 0)
            return bigram_tf.get((parts[0], parts[1]), 0)

        def _boosted_count(term: str) -> float:
            cnt = _raw_count(term)
            return cnt * _BIGRAM_BOOST if len(term.split()) == 2 else float(cnt)

        present = [(names[i], _boosted_count(names[i])) for i in range(len(names)) if scores[i] > 0]
        ranked = [term for term, _ in sorted(present, key=lambda x: -x[1])]

        word_to_bigrams: dict = defaultdict(list)
        for term, _ in present:
            if len(term.split()) == 2:
                for w in term.split():
                    word_to_bigrams[w].append(term)

        selected: list = []
        selected_stems: list = []

        def _try_add(term: str) -> bool:
            stem = _stem(term)
            if stem in selected_stems:
                return False
            if any(SequenceMatcher(None, term, s).ratio() > 0.70 for s in selected):
                return False
            selected.append(term)
            selected_stems.append(stem)
            return True

        for term in ranked:
            if len(selected) >= _TOP_N_TFIDF:
                break
            words = term.split()
            if _raw_count(term) < MIN_DOC_FREQ:
                continue
            if len(words) == 1:
                candidates = word_to_bigrams.get(words[0], [])
                candidates = [b for b in candidates if _raw_count(b) >= MIN_DOC_FREQ]
                if candidates:
                    best = max(candidates, key=_boosted_count)
                    if _stem(best) not in selected_stems:
                        _try_add(best)
                    continue
            _try_add(term)

        return selected
    except Exception:
        return []


def load_vectorizer(path: str):
    """Load a pickled TfidfVectorizer. Returns None if path doesn't exist or load fails."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        with open(p, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None
