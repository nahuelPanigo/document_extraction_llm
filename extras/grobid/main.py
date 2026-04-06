"""
Grobid extraction — processes the same 80-doc subset used in abstract/keywords
validation, calls the Grobid service for each PDF, saves TEI XML, then parses
abstract and keywords into results.csv.

Run from repo root:
    python extras/grobid/main.py

Requirements:
    - Grobid service running at GROBID_SERVICE (default http://localhost:8070)
      Start with: docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.2
    - pip install requests beautifulsoup4 lxml

Steps:
    1. Load 80-doc subset IDs from abstract_extraction/results.csv
    2. For each ID: send PDF to Grobid processHeaderDocument (faster, focused
       on title/abstract/keywords), save XML to extras/grobid/xml/
       (skips if XML already exists)
    3. Parse every XML: extract abstract + keywords
    4. Save extras/grobid/results.csv
"""

import csv
import re
import sys
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).parent.parent.parent))
from constants import PDF_FOLDER, GROBID_SERVICE

# ── Config ────────────────────────────────────────────────────────────────────
XML_FOLDER    = Path(__file__).parent / "xml"
RESULTS_CSV   = Path(__file__).parent / "results.csv"
SUBSET_CSV    = Path(__file__).parent.parent / "abstract_extraction" / "results.csv"
GROBID_URL    = f"{GROBID_SERVICE}/api/processFulltextDocument"
REQUEST_DELAY = 1.0   # seconds between requests (be kind to the service)

XML_FOLDER.mkdir(parents=True, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_grobid() -> bool:
    try:
        r = requests.get(f"{GROBID_SERVICE}/api/isalive", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def load_ids() -> list[str]:
    """Load the 80-doc subset IDs from abstract_extraction results."""
    with open(SUBSET_CSV, encoding="utf-8") as f:
        return [row["fileid"] for row in csv.DictReader(f)]


def send_to_grobid(pdf_path: Path) -> str | None:
    """Send a PDF to Grobid and return the TEI XML string, or None on error."""
    try:
        with open(pdf_path, "rb") as fh:
            r = requests.post(
                GROBID_URL,
                files={"input": fh},
                timeout=120,
            )
        if r.status_code == 200:
            return r.text
        print(f"  [HTTP {r.status_code}] {pdf_path.name}")
    except Exception as e:
        print(f"  [ERROR] {pdf_path.name}: {e}")
    return None


# ── XML parsing ───────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Collapse whitespace."""
    return re.sub(r"\s+", " ", text).strip()


_BIBTEX_FIELD = re.compile(
    r'^\s+(\w[\w.]*)\s*=\s*\{(.*)\},?\s*$',
    re.DOTALL,
)


def _parse_bibtex(text: str) -> dict:
    """
    Minimal BibTeX parser — extracts abstract and keywords fields.
    Grobid sometimes returns BibTeX instead of TEI XML (e.g. processHeaderDocument).
    """
    abstract = ""
    keywords: list[str] = []

    # Join continuation lines: BibTeX values can span multiple lines
    # Strategy: split on field boundaries  "  fieldname = {"
    field_re = re.compile(r'\n\s{2,}(\w[\w.]*)\s*=\s*\{', re.IGNORECASE)
    parts = field_re.split(text)
    # parts alternates: [preamble, fieldname, value, fieldname, value, ...]
    i = 1
    while i + 1 < len(parts):
        fname = parts[i].strip().lower()
        raw = parts[i + 1]
        # Strip trailing "},\n" or "}\n@" introduced by the split
        raw = re.sub(r'\},?\s*$', '', raw).strip()
        if fname == "abstract":
            abstract = _clean(raw)
        elif fname in ("keywords", "keyword"):
            keywords = [k.strip() for k in re.split(r"[,;|•·]", raw) if k.strip()]
        i += 2

    return {"abstract": abstract, "keywords": " | ".join(keywords)}


def parse_xml(xml_path: Path) -> dict:
    """
    Parse a Grobid output file and return:
      {abstract: str, keywords: str}
    Keywords are joined with ' | '.
    Handles both TEI XML (processFulltextDocument) and BibTeX
    (sometimes returned by processHeaderDocument).
    """
    text = xml_path.read_text(encoding="utf-8", errors="ignore")

    # Detect BibTeX format (starts with @misc, @article, etc.)
    if text.lstrip().startswith("@"):
        return _parse_bibtex(text)

    try:
        soup = BeautifulSoup(text, "lxml-xml")
    except Exception as e:
        print(f"  [PARSE ERROR] {xml_path.name}: {e}")
        return {"abstract": "", "keywords": ""}

    # ── Abstract ──────────────────────────────────────────────────────────────
    abstract = ""
    abs_tag = soup.find("abstract")
    if abs_tag:
        abstract = _clean(abs_tag.get_text(" ", strip=True))

    # ── Keywords ─────────────────────────────────────────────────────────────
    # Grobid can place keywords in several spots:
    #   <keywords> under <profileDesc>
    #   <term> elements inside <keywords>
    #   <note type="keywords"> (fallback)
    keywords: list[str] = []

    kw_tag = soup.find("keywords")
    if kw_tag:
        # If <term> children exist, use them individually
        terms = kw_tag.find_all("term")
        if terms:
            keywords = [_clean(t.get_text()) for t in terms if t.get_text().strip()]
        else:
            # Plain text — split on common separators
            raw = _clean(kw_tag.get_text(" ", strip=True))
            if raw:
                keywords = [k.strip() for k in re.split(r"[,;|•·]", raw) if k.strip()]

    # Fallback: <note type="keywords">
    if not keywords:
        note = soup.find("note", attrs={"type": "keywords"})
        if note:
            raw = _clean(note.get_text(" ", strip=True))
            keywords = [k.strip() for k in re.split(r"[,;|•·]", raw) if k.strip()]

    return {
        "abstract": abstract,
        "keywords": " | ".join(keywords),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    print("Loading subset IDs…")
    ids = load_ids()
    print(f"  {len(ids)} documents")

    # ── Step 1: send PDFs to Grobid ───────────────────────────────────────────
    grobid_ok = check_grobid()
    if not grobid_ok:
        print(f"\n[WARN] Grobid not reachable at {GROBID_SERVICE}")
        print("       Start it with:")
        print("       docker run --rm -p 8070:8070 lfoppiano/grobid:0.8.0")
        print("       Skipping PDF processing — will parse any existing XMLs.\n")
    else:
        print(f"\nGrobid service OK at {GROBID_SERVICE}")

    missing_pdf   = []
    already_exist = 0
    processed     = 0
    failed        = 0

    for fid in ids:
        xml_path = XML_FOLDER / f"{fid}.xml"

        if xml_path.exists():
            already_exist += 1
            continue

        if not grobid_ok:
            continue

        pdf_path = PDF_FOLDER / f"{fid}.pdf"
        if not pdf_path.exists():
            missing_pdf.append(fid)
            continue

        print(f"  Processing {fid}…", end=" ", flush=True)
        xml = send_to_grobid(pdf_path)
        if xml:
            xml_path.write_text(xml, encoding="utf-8")
            print("OK")
            processed += 1
        else:
            failed += 1
            print("FAILED")

        time.sleep(REQUEST_DELAY)

    print(f"\nPDF processing: {processed} new, {already_exist} cached, "
          f"{failed} failed, {len(missing_pdf)} PDFs missing")
    if missing_pdf:
        print(f"  Missing PDFs: {missing_pdf[:5]}{'…' if len(missing_pdf) > 5 else ''}")

    # ── Step 2: parse XMLs ────────────────────────────────────────────────────
    print("\nParsing XMLs…")
    rows = []
    for fid in ids:
        xml_path = XML_FOLDER / f"{fid}.xml"
        if xml_path.exists():
            parsed = parse_xml(xml_path)
        else:
            parsed = {"abstract": "", "keywords": ""}

        rows.append({
            "fileid":            fid,
            "grobid_abstract":   parsed["abstract"],
            "grobid_keywords":   parsed["keywords"],
            "xml_found":         "yes" if xml_path.exists() else "no",
        })

    # ── Step 3: save CSV ──────────────────────────────────────────────────────
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["fileid", "grobid_abstract",
                                          "grobid_keywords", "xml_found"])
        w.writeheader()
        w.writerows(rows)

    found_abs = sum(1 for r in rows if r["grobid_abstract"])
    found_kw  = sum(1 for r in rows if r["grobid_keywords"])
    print(f"\nSUMMARY")
    print(f"  XMLs parsed:       {sum(1 for r in rows if r['xml_found']=='yes')}/{len(rows)}")
    print(f"  Abstract found:    {found_abs}/{len(rows)}")
    print(f"  Keywords found:    {found_kw}/{len(rows)}")
    print(f"\nSaved → {RESULTS_CSV}")


if __name__ == "__main__":
    run()
