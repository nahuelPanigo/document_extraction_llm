"""
Final comparison CSV — merges abstract extraction, keyword extraction and Grobid
results for the 80-doc validation subset.

Columns:
  fileid
  type
  --- Abstract ---
  abstract_regex       B_regex_extract  (inline + regex end detection)
  abstract_grobid      Grobid TEI <abstract>
  abstract_truth       Ground truth from sedici.csv
  --- Keywords ---
  keywords_regex       regex_finds      (explicit 'Keywords:' section)
  keywords_tfidf       tfidf_predict    (PMI vocab + boosted raw-TF)
  keywords_grobid      Grobid TEI <keywords>
  keywords_truth       sedici_keywords  (dc.subject ground truth)

Run from repo root:
    python extras/comparison.py
"""

import csv
from pathlib import Path

ABSTRACT_CSV = Path(__file__).parent / "abstract_extraction" / "results.csv"
KEYWORDS_CSV = Path(__file__).parent / "keywords_extraction" / "results.csv"
GROBID_CSV   = Path(__file__).parent / "grobid"              / "results.csv"
OUTPUT_CSV   = Path(__file__).parent / "comparison.csv"


def load_index(path: Path, key: str = "fileid") -> dict:
    with open(path, encoding="utf-8") as f:
        return {row[key]: row for row in csv.DictReader(f)}


def run():
    abs_idx = load_index(ABSTRACT_CSV)
    kw_idx  = load_index(KEYWORDS_CSV)
    gr_idx  = load_index(GROBID_CSV)

    # Use keywords CSV as the master ID list (has type column)
    all_ids = list(kw_idx.keys())
    print(f"Merging {len(all_ids)} documents…")

    rows = []
    for fid in all_ids:
        a  = abs_idx.get(fid, {})
        kw = kw_idx.get(fid, {})
        gr = gr_idx.get(fid, {})

        rows.append({
            "fileid":           fid,
            "type":             kw.get("type", ""),
            # Abstract
            "abstract_regex":   a.get("B_regex_extract", ""),
            "abstract_grobid":  gr.get("grobid_abstract", ""),
            "abstract_truth":   a.get("ground_truth", ""),
            # Keywords
            "keywords_regex":   kw.get("regex_finds", ""),
            "keywords_tfidf":   kw.get("tfidf_predict", ""),
            "keywords_grobid":  gr.get("grobid_keywords", ""),
            "keywords_truth":   kw.get("sedici_keywords", ""),
        })

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Quick summary
    def filled(col): return sum(1 for r in rows if r[col].strip())
    print(f"\n  {'Column':<22} {'Filled':>6} / {len(rows)}")
    print(f"  {'-'*22} {'-'*6}")
    for col in ["abstract_regex", "abstract_grobid", "keywords_regex",
                "keywords_tfidf", "keywords_grobid"]:
        print(f"  {col:<22} {filled(col):>6}")

    print(f"\nSaved → {OUTPUT_CSV}")


if __name__ == "__main__":
    run()
