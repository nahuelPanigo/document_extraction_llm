"""
Enrich 20_per_type_fine_tunned.json with abstract and keywords
extracted from comparison_test_data.json.

For each matching document ID:
  - abstract  <- pattern_abstract
  - keywords  <- {
        "real":      pattern_regex split by "|" (stripped),
        "suggested": tfidf_keywords split by "|" (stripped)
    }
"""

import json
from pathlib import Path

FINETUNNED_PATH = Path(__file__).parent.parent / "validation/result/FINETUNNED/20_per_type_fine_tunned.json"
COMPARISON_PATH = Path(__file__).parent / "comparison_test_data.json"
OUTPUT_PATH     = Path(__file__).parent.parent / "validation/result/FINETUNNED/20_per_type_fine_tunned_enriched.json"


def split_pipe(value: str) -> list[str]:
    """Split a pipe-separated string into a cleaned list of strings."""
    if not value or not value.strip():
        return []
    return [kw.strip() for kw in value.split("|") if kw.strip()]


def main():
    with open(FINETUNNED_PATH, encoding="utf-8") as f:
        finetunned = json.load(f)

    with open(COMPARISON_PATH, encoding="utf-8") as f:
        comparison = json.load(f)

    enriched = 0
    for doc_id, doc in finetunned.items():
        if doc_id not in comparison:
            continue

        source = comparison[doc_id]

        # abstract
        pattern_abstract = source.get("pattern_abstract", "")
        if pattern_abstract and pattern_abstract.strip():
            doc["abstract"] = pattern_abstract.strip()

        # keywords: real (pattern_regex) + suggested (tfidf_keywords)
        real      = split_pipe(source.get("pattern_regex", ""))
        suggested = split_pipe(source.get("tfidf_keywords", ""))

        if real or suggested:
            doc["keywords"] = {
                "real":      real,
                "suggested": suggested,
            }

        enriched += 1

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(finetunned, f, ensure_ascii=False, indent=2)

    print(f"✅ Enriched {enriched}/{len(finetunned)} documents")
    print(f"💾 Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
