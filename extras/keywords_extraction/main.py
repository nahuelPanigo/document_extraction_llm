"""
Keywords extraction test — compares five strategies:
  A. Regex    — find explicit 'Keywords:' / 'Palabras clave:' section.
  B. YAKE     — unsupervised statistical keyphrase extraction.
  C. KeyBERT  — semantic keyphrase ranking using MiniLM.
  D. TF-IDF   — PMI-filtered vocabulary + raw in-doc TF scoring.
               Pipeline (run once, cached):
               1. Unigrams: remove stopwords + len≤2
               2. Bigrams:  PMI collocation finder (meaningful phrases only)
               3. Custom vocabulary = unigrams + PMI bigrams
               4. TF-IDF scored on that vocabulary
               5. Per-doc: drop unigrams already covered by a selected bigram
  E. RAKE     — Rapid Automatic Keyword Extraction (multi-word phrases).

Run from repo root:
    python extras/keywords_extraction/main.py
"""

import csv
import pickle
import re
import sys
from pathlib import Path
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))
from constants import TXT_NO_TAGS_FOLDER, CSV_FOLDER
from abstract_extraction.main import strategy_b_inline, strategy_a_standalone

# ── Config ─────────────────────────────────────────────────────────────────────
N_PER_TYPE     = 20
CSV_TYPES      = CSV_FOLDER / "types.csv"
CSV_MAIN       = CSV_FOLDER / "sedici.csv"
TYPES          = ["Libro", "Tesis", "Articulo", "Objeto de conferencia"]
TOP_N_YAKE     = 10
TOP_N_KEYBERT  = 10
TOP_N_TFIDF    = 10
TOP_N_RAKE     = 10
BIGRAM_BOOST   = 1.7  # multiplier applied to bigram raw-TF when ranking
TFIDF_CACHE    = Path(__file__).parent / "tfidf_vectorizer.pkl"
RESULTS_CSV    = Path(__file__).parent / "results.csv"
MAX_TEXT_CHARS = 3000   # fallback chars fed to YAKE/KeyBERT when no abstract found

# PMI bigram settings
PMI_MIN_FREQ   = 3      # bigram must appear at least this many times
PMI_TOP        = 20000  # take top N bigrams by PMI

# ── Optional imports ───────────────────────────────────────────────────────────
try:
    import yake as _yake
    YAKE_AVAILABLE = True
except ImportError:
    YAKE_AVAILABLE = False
    print("[WARN] yake not installed — skipping B.  pip install yake")

try:
    from keybert import KeyBERT as _KeyBERT
    KEYBERT_AVAILABLE = True
except ImportError:
    KEYBERT_AVAILABLE = False
    print("[WARN] keybert not installed — skipping C.  pip install keybert")

try:
    from sentence_transformers import SentenceTransformer as _ST
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

try:
    from rake_nltk import Rake as _Rake
    RAKE_AVAILABLE = True
except ImportError:
    RAKE_AVAILABLE = False
    print("[WARN] rake-nltk not installed — skipping E.  pip install rake-nltk")

try:
    import spacy as _spacy
    _nlp = _spacy.load("es_core_news_sm")
    NER_AVAILABLE = True
except Exception:
    NER_AVAILABLE = False
    _nlp = None
    print("[WARN] spacy/es_core_news_sm not available — NER filter disabled.")
    print("       pip install spacy && python -m spacy download es_core_news_sm")

import nltk
from difflib import SequenceMatcher
from nltk.collocations import BigramAssocMeasures, BigramCollocationFinder
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

_STEMMER = SnowballStemmer("spanish")

# Download required NLTK data silently if missing
for _pkg in ("stopwords", "punkt", "punkt_tab"):
    try:
        nltk.data.find(f"tokenizers/{_pkg}" if "punkt" in _pkg else f"corpora/{_pkg}")
    except LookupError:
        nltk.download(_pkg, quiet=True)

from nltk.corpus import stopwords as _nltk_sw

# Combined Spanish + English stopwords
_STOPWORDS = set(_nltk_sw.words("spanish")) | set(_nltk_sw.words("english"))
print(f"[INFO] Stopwords loaded: {len(_STOPWORDS)} total "
      f"(es={len(set(_nltk_sw.words('spanish')))}, "
      f"en={len(set(_nltk_sw.words('english')))})")
# Extra domain noise for academic repos
_STOPWORDS.update({
    "también", "así", "través", "puede", "pueden", "debe", "deben",
    "este", "esta", "estos", "estas", "dicho", "dichos", "dicha", "dichas",
    "mismo", "misma", "mismos", "mismas", "solo", "sólo", "siendo", "sido",
    "según", "cada", "todo", "toda", "todos", "todas",
})

# ── Keyword section regex ──────────────────────────────────────────────────────
KW_HEADING = re.compile(
    r"^(keywords?|palabras?\s+claves?|key\s+words?|mots[- ]cl[eé]s?|"
    r"parole\s+chiave|palavras?[- ]chave)\s*[:\-–—]?\s*(.*)",
    re.IGNORECASE,
)
BILINGUAL_SUFFIX = re.compile(
    r"^(keywords?|palabras?\s+claves?|key\s+words?|conclusiones?|"
    r"resumen|abstract|summary|resumo)\s*$",
    re.IGNORECASE,
)
KW_STOP_HEADINGS = {
    "abstract", "resumen", "summary", "resumo",
    "introducción", "introduction", "introdução",
    "1.", "references", "referencias",
}
KW_SPLIT = re.compile(r"[,;|•·]|\s[-/]\s|\.\s+")

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

def _strip_urls(text: str) -> str:
    """Remove URLs before tokenization so fragments like 'https','sedici','unlp'
    don't appear as fake keywords due to \\b splitting on ':' and '.'."""
    return _URL_RE.sub(" ", text)


# ── Data loading ───────────────────────────────────────────────────────────────

def _clean_subject(raw: str) -> list[str]:
    return [p.split("::")[0].strip().lower()
            for p in raw.split("||") if p.split("::")[0].strip()]


def load_ground_truth() -> dict:
    gt = {}
    cols = ["dc.subject", "dc.subject[es]", "dc.subject[en]", "dc.subject[pt]"]
    with open(CSV_MAIN, encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            terms = [t for c in cols for t in _clean_subject(row.get(c, ""))]
            if terms:
                gt[row["id"].strip()] = list(dict.fromkeys(terms))
    return gt


def load_subset() -> list[dict]:
    files = {f.stem for f in TXT_NO_TAGS_FOLDER.iterdir() if f.suffix == ".txt"}
    by_type: dict[str, list] = defaultdict(list)
    with open(CSV_TYPES, encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            fid, t = row["id"].strip(), row["type"].strip()
            if fid in files and t in TYPES:
                by_type[t].append(fid)
    subset = []
    for t in TYPES:
        for fid in by_type[t][:N_PER_TYPE]:
            nid = fid.split("-")[1] if "-" in fid else fid
            subset.append({"id": nid, "full_id": fid, "type": t,
                           "path": TXT_NO_TAGS_FOLDER / f"{fid}.txt"})
    return subset


# ── TF-IDF pipeline (PMI vocabulary) ──────────────────────────────────────────

def _token_pattern():
    # Only letters (including accented Spanish chars), min 4 chars
    # (3-char terms like cbr/clf/brc are almost always noise or abbreviations)
    return r"(?u)\b[a-záéíóúüñA-ZÁÉÍÓÚÜÑ][a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{3,}\b"


def _build_unigram_vocab(corpus_texts: list[str]) -> list[str]:
    """
    Step 1: Count all single words, remove stopwords and short words.
    """
    cv = CountVectorizer(ngram_range=(1, 1), token_pattern=_token_pattern())
    tf = cv.fit_transform(corpus_texts)
    freq = tf.sum(axis=0).A1                      # total count per term
    vocab = cv.get_feature_names_out()

    word_freq = sorted(zip(vocab, freq), key=lambda x: -x[1])

    return [
        w for w, f in word_freq
        if f >= 2
        and w.lower() not in _STOPWORDS
        and len(w) > 2
    ]


def _build_bigram_vocab(corpus_texts: list[str]) -> list[str]:
    """
    Step 2: PMI-based bigram collocations.
    Words that appear together much more than by chance → real phrases.

    NOTE: Spanish articles (las, los, del…) always precede nouns so they get
    artificially high PMI. We guard against this in two layers:
      - apply_word_filter: min length 4, must be letters-only, not a stopword
      - explicit post-filter: double-check neither word is a stopword
    """
    print("    Tokenizing corpus for bigram PMI…")
    tokenized = [word_tokenize(t.lower()) for t in corpus_texts]

    measures = BigramAssocMeasures()
    finder   = BigramCollocationFinder.from_documents(tokenized)

    finder.apply_freq_filter(PMI_MIN_FREQ)
    finder.apply_word_filter(
        lambda w: len(w) < 4                              # catches las/los/por/del/que…
               or len(w) > 20
               or w in _STOPWORDS
               or not re.match(r"^[a-záéíóúüñ]+$", w)    # letters only, no numbers/punct
    )

    bigrams = finder.nbest(measures.pmi, PMI_TOP)

    # Explicit post-filter: guarantee neither word is a stopword
    return [
        f"{w1} {w2}" for w1, w2 in bigrams
        if w1 not in _STOPWORDS and w2 not in _STOPWORDS
    ]


def build_or_load_tfidf() -> TfidfVectorizer:
    if TFIDF_CACHE.exists():
        print(f"  Loading cached TF-IDF vectorizer…")
        with open(TFIDF_CACHE, "rb") as f:
            return pickle.load(f)

    print("  Building PMI vocabulary + TF-IDF (first time, ~1 min)…")
    texts = [_strip_urls(p.read_text(encoding="utf-8", errors="ignore"))
             for p in TXT_NO_TAGS_FOLDER.iterdir() if p.suffix == ".txt"]

    print("    Building unigram vocabulary…")
    uni_vocab   = _build_unigram_vocab(texts)
    print(f"    Unigrams: {len(uni_vocab)}")

    bi_vocab    = _build_bigram_vocab(texts)
    print(f"    PMI bigrams: {len(bi_vocab)}")

    vocabulary  = list(dict.fromkeys(uni_vocab + bi_vocab))  # dedup, order preserved
    print(f"    Combined vocabulary: {len(vocabulary)} terms")

    vectorizer  = TfidfVectorizer(
        vocabulary   = vocabulary,
        analyzer     = "word",
        ngram_range  = (1, 2),
        sublinear_tf = True,
        token_pattern= _token_pattern(),
        min_df       = 2,   # term must appear in ≥2 docs — filters extreme rarities
    )
    vectorizer.fit(texts)

    with open(TFIDF_CACHE, "wb") as f:
        pickle.dump(vectorizer, f)
    print(f"  Saved to {TFIDF_CACHE.name}")
    return vectorizer


def _stem(term: str) -> str:
    """Stem every word in a term (handles both unigrams and bigrams)."""
    return " ".join(_STEMMER.stem(w) for w in term.lower().split())


def strategy_d_tfidf(text: str, vectorizer: TfidfVectorizer) -> list[str]:
    """
    Strategy D — PMI vocabulary + boosted raw-TF ranking, with three dedup layers:

    Ranking: raw in-doc frequency, bigrams multiplied by BIGRAM_BOOST (1.7).
    Substitution: if a unigram's word also appears in a present bigram, the
    bigram is selected instead (the unigram is dropped).

    Dedup:
    1. Stem deduplication (SnowballStemmer Spanish): same stem → keep higher scored.
       e.g. "radiológica" + "radiológicas" → same stem → only one kept.
    2. String similarity (difflib ≥0.70): catches near-duplicates the stemmer misses.
    """
    vec    = vectorizer.transform([_strip_urls(text)])
    names  = vectorizer.get_feature_names_out()
    scores = vec.toarray()[0]

    # Raw in-document frequency — used for RANKING (not TF-IDF, which biases rare corpus terms)
    _tok_re  = re.compile(r"(?u)\b[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{4,}\b")
    from collections import Counter as _Counter
    words_in_doc = _tok_re.findall(_strip_urls(text).lower())
    raw_tf       = _Counter(words_in_doc)
    bigram_tf    = _Counter(zip(words_in_doc, words_in_doc[1:]))
    MIN_DOC_FREQ = 2  # term must appear at least twice in this document

    def _raw_count(term: str) -> int:
        parts = term.split()
        if len(parts) == 1:
            return raw_tf.get(term, 0)
        return bigram_tf.get((parts[0], parts[1]), 0)

    def _boosted_count(term: str) -> float:
        cnt = _raw_count(term)
        return cnt * BIGRAM_BOOST if len(term.split()) == 2 else float(cnt)

    # Keep only vocab terms present in this doc; bigrams get a ×BIGRAM_BOOST advantage
    present = [(names[i], _boosted_count(names[i])) for i in range(len(names)) if scores[i] > 0]
    ranked  = [term for term, _ in sorted(present, key=lambda x: -x[1])]

    # Build word → [bigrams] map for every bigram present in this doc (used for substitution)
    word_to_bigrams: dict[str, list[str]] = defaultdict(list)
    for term, _ in present:
        if len(term.split()) == 2:
            for w in term.split():
                word_to_bigrams[w].append(term)

    # Pass 2 — select with all three deduplication filters
    selected:       list[str] = []
    selected_stems: list[str] = []

    def _try_add(term: str) -> bool:
        """Apply dedup filters and add term if it passes. Returns True if added."""
        stem = _stem(term)
        if stem in selected_stems:
            return False
        if any(SequenceMatcher(None, term, s).ratio() > 0.70 for s in selected):
            return False
        selected.append(term)
        selected_stems.append(stem)
        return True

    for term in ranked:
        if len(selected) >= TOP_N_TFIDF:
            break

        words = term.split()

        # Filter 0: minimum in-document frequency (raw, no boost)
        if _raw_count(term) < MIN_DOC_FREQ:
            continue

        if len(words) == 1:
            # If this unigram is a component of any present bigram, prefer the bigram
            candidates = word_to_bigrams.get(words[0], [])
            candidates = [b for b in candidates if _raw_count(b) >= MIN_DOC_FREQ]
            if candidates:
                # Pick highest boosted-score bigram not yet selected
                best = max(candidates, key=_boosted_count)
                stem_best = _stem(best)
                if stem_best not in selected_stems:
                    _try_add(best)
                # Either way, skip the bare unigram
                continue

        _try_add(term)

    return selected


# ── Abstract-first text helper ─────────────────────────────────────────────────

def _get_best_text(full_text: str) -> str:
    """
    Try to extract the abstract for use as input to YAKE/KeyBERT/RAKE.
    Falls back to first MAX_TEXT_CHARS chars if no abstract found (>100 chars).
    """
    result = strategy_b_inline(full_text)
    if not result or len(result) < 100:
        result = strategy_a_standalone(full_text)
    if result and len(result) >= 100:
        return result
    return full_text[:MAX_TEXT_CHARS]


# ── NER filter ────────────────────────────────────────────────────────────────

def _extract_ner_blacklist(text: str, nlp) -> set[str]:
    """
    Run spaCy NER on the first 2000 chars and return lowercased PER entity
    surface forms (person names to exclude from keyword results).
    Only PER is filtered — ORG entities like "ICRP", "IAEA" are valid keywords.
    """
    doc = nlp(text[:2000])
    return {ent.text.lower() for ent in doc.ents if ent.label_ == "PER"}


def _filter_ner(keywords: list[str], blacklist: set[str]) -> list[str]:
    """Remove keywords whose individual words appear in the NER blacklist."""
    if not blacklist:
        return keywords
    filtered = []
    for kw in keywords:
        words = kw.lower().split()
        if any(w in blacklist for w in words):
            continue
        filtered.append(kw)
    return filtered


# ── Strategies A / B / C / E ──────────────────────────────────────────────────

def _looks_like_keyword_line(text: str) -> bool:
    return len(text) <= 120


def strategy_a_regex(text: str) -> list[str]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = KW_HEADING.match(line.strip())
        if not m:
            continue
        first = m.group(2).strip()
        if first and BILINGUAL_SUFFIX.match(first):
            first = ""
        if first and _looks_like_keyword_line(first):
            raw = first
        else:
            collected = []
            for follow in lines[i + 1: i + 6]:
                stripped = follow.strip()
                if not stripped:
                    break
                if stripped.lower().rstrip(".:") in KW_STOP_HEADINGS:
                    break
                if not _looks_like_keyword_line(stripped):
                    break
                collected.append(stripped)
            raw = " ".join(collected)
        if not raw:
            continue
        terms = [t.strip() for t in KW_SPLIT.split(raw) if t.strip()]
        terms = [t for t in terms if 1 <= len(t.split()) <= 6 and len(t) <= 80]
        if terms:
            return terms
    return []


def strategy_b_yake(text: str, lang: str = "es") -> list[str]:
    if not YAKE_AVAILABLE:
        return []
    extractor = _yake.KeywordExtractor(lan=lang, n=3, dedupLim=0.7, top=TOP_N_YAKE)
    return [kw for kw, _ in extractor.extract_keywords(_get_best_text(text))]


def strategy_c_keybert(text: str, model) -> list[str]:
    if not KEYBERT_AVAILABLE or model is None:
        return []
    try:
        results = model.extract_keywords(
            _get_best_text(text),
            keyphrase_ngram_range=(1, 3),
            stop_words=None,
            top_n=TOP_N_KEYBERT,
            use_mmr=True,
            diversity=0.5,
        )
        return [kw for kw, _ in results]
    except Exception as e:
        print(f"  [KeyBERT error] {e}")
        return []


def strategy_e_rake(text: str) -> list[str]:
    if not RAKE_AVAILABLE:
        return []
    r = _Rake(stopwords=_STOPWORDS, min_length=1, max_length=3)
    r.extract_keywords_from_text(_get_best_text(text))
    return r.get_ranked_phrases()[:TOP_N_RAKE]


# ── Scoring ────────────────────────────────────────────────────────────────────

def loose_overlap(extracted: list[str], truth: list[str]) -> float:
    if not extracted or not truth:
        return 0.0
    hits = sum(1 for kw in extracted
               if any(kw.lower() in t or t in kw.lower() for t in truth))
    return hits / len(extracted)


# ── Main ───────────────────────────────────────────────────────────────────────

def run():
    print("Loading ground truth…")
    gt = load_ground_truth()
    print(f"  {len(gt)} docs with subject labels")

    print("\nBuilding / loading TF-IDF vectorizer…")
    tfidf = build_or_load_tfidf()

    kb_model = None
    if KEYBERT_AVAILABLE and ST_AVAILABLE:
        print("\nLoading KeyBERT…")
        try:
            kb_model = _KeyBERT(model=_ST("all-MiniLM-L6-v2"))
            print("  ready.")
        except Exception as e:
            print(f"  [WARN] {e}")

    if NER_AVAILABLE:
        print("[INFO] NER filter enabled (spaCy es_core_news_sm — PER entities)")
    else:
        print("[INFO] NER filter disabled")

    print(f"\nLoading subset ({N_PER_TYPE}/type × {len(TYPES)} types)…")
    subset = load_subset()
    print(f"  {len(subset)} docs total")

    names    = ["A_regex", "B_yake", "C_keybert", "D_tfidf", "E_rake"]
    found    = {k: 0   for k in names}
    overlaps = {k: []  for k in names}
    rows     = []

    print("\n" + "=" * 90)

    for doc in subset:
        truth = gt.get(doc["id"], [])
        try:
            text = doc["path"].read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # NER blacklist for this document
        blacklist: set[str] = set()
        if NER_AVAILABLE and _nlp is not None:
            blacklist = _extract_ner_blacklist(text, _nlp)

        res = {
            "A_regex":   strategy_a_regex(text),
            "B_yake":    strategy_b_yake(text)              if YAKE_AVAILABLE    else [],
            "C_keybert": strategy_c_keybert(text, kb_model) if KEYBERT_AVAILABLE else [],
            "D_tfidf":   strategy_d_tfidf(text, tfidf),
            "E_rake":    strategy_e_rake(text)              if RAKE_AVAILABLE    else [],
        }

        # Apply NER filter to all strategies
        if blacklist:
            for k in res:
                res[k] = _filter_ner(res[k], blacklist)

        print(f"\n[{doc['type']}] {doc['full_id']}")
        print(f"  truth: {truth[:5]}")
        for n, kws in res.items():
            ov = loose_overlap(kws, truth)
            overlaps[n].append(ov)
            if kws: found[n] += 1
            print(f"  {n:12s}  ov={ov:.2f}  {', '.join(kws[:6]) or '(nothing)'}")

        rows.append({
            "fileid":          doc["full_id"],
            "type":            doc["type"],
            "regex_finds":     " | ".join(res["A_regex"]),
            "yake_predict":    " | ".join(res["B_yake"]),
            "keybert_predict": " | ".join(res["C_keybert"]),
            "tfidf_predict":   " | ".join(res["D_tfidf"]),
            "rake_predict":    " | ".join(res["E_rake"]),
            "sedici_keywords": " | ".join(truth),
        })

    total = len(subset)
    print("\n" + "=" * 90)
    print(f"SUMMARY  ({total} docs)\n")
    print(f"  NOTE: overlap vs SEDICI taxonomy — rough signal only.\n")
    print(f"  {'Strategy':<14} {'Found':>6} {'%':>6}  {'Avg overlap':>12}")
    print(f"  {'-'*14} {'-'*6} {'-'*6}  {'-'*12}")
    for n in names:
        sc = overlaps[n]
        avg = sum(sc)/len(sc) if sc else 0.0
        print(f"  {n:<14} {found[n]:>6} {100*found[n]/total:>5.1f}%  {avg:>12.3f}")
    print()

    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Saved → {RESULTS_CSV}")


if __name__ == "__main__":
    run()
