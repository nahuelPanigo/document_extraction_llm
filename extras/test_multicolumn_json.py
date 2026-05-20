"""
test_multicolumn_json.py — Validate multicolumn detection against all IDs in the
final_to_compare_original.json (same file used by test_abstract.py).

Expected multicolumn IDs (ground truth provided by user):
  10915-145097, 10915-117917, 10915-117661, 10915-117806, 10915-150991,
  10915-94779,  10915-145103, 10915-150873, 10915-117660, 10915-95445,
  10915-117729, 10915-117224, 10915-151398, 10915-117443, 10915-138103

All other IDs in the JSON are expected to be single-column.
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from constants import PDF_FOLDER

from multicolumn_detection import detect_pdf_columns

FINAL_JSON_PATH = Path(
    "/home/nahuel/Documents/document_extraction_llm/validation/result/final_to_compare_original.json"
)

EXPECTED_MULTICOLUMN = {
    "10915-145097",
    "10915-117917",
    "10915-117661",
    "10915-117806",
    "10915-150991",
    "10915-94779",
    "10915-145103",
    "10915-150873",
    "10915-117660",
    "10915-95445",
    "10915-117729",
    "10915-117224",
    "10915-151398",
    "10915-117443",
    "10915-138103",
}


def _fmt(result: dict) -> str:
    d      = result["page_details"][0] if result["page_details"] else {}
    a_conf = d.get("method_a", {}).get("confidence", 0)
    b_conf = d.get("method_b", {}).get("confidence", 0)
    b_vr   = d.get("method_b", {}).get("valley_ratio", "-")
    return (
        f"pages_multi={result['pages_multicolumn']}/{result['pages_checked']}  "
        f"A_conf={a_conf:.2f}  B_conf={b_conf:.2f}  B_valley={b_vr}"
    )


if __name__ == "__main__":
    with open(FINAL_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_ids = list(data.keys())
    print(f"Total documents in JSON: {len(all_ids)}")
    print(f"Expected multi-column:   {len(EXPECTED_MULTICOLUMN)}")
    print(f"Expected single-column:  {len(all_ids) - len(EXPECTED_MULTICOLUMN)}")

    tp = fn = tn = fp = 0
    missing = []
    results = {}

    print(f"\n{'='*75}")
    print("EXPECTED MULTI-COLUMN  (should be MULTI)")
    print(f"{'='*75}")
    for doc_id in sorted(EXPECTED_MULTICOLUMN):
        if doc_id not in data:
            print(f"  ? {doc_id}  [not in JSON]")
            continue
        pdf = PDF_FOLDER / f"{doc_id}.pdf"
        if not pdf.exists():
            print(f"  - {doc_id}  [PDF not found]")
            missing.append(doc_id)
            continue
        res = detect_pdf_columns(pdf)
        results[doc_id] = res
        ok = "✓" if res["is_multicolumn"] else "✗"
        if res["is_multicolumn"]:
            tp += 1
        else:
            fn += 1
        label = "MULTI " if res["is_multicolumn"] else "SINGLE"
        print(f"  {ok} {doc_id}  {label}  {_fmt(res)}")

    print(f"\n{'='*75}")
    print("EXPECTED SINGLE-COLUMN  (should be SINGLE)")
    print(f"{'='*75}")
    single_ids = [d for d in all_ids if d not in EXPECTED_MULTICOLUMN]
    for doc_id in sorted(single_ids):
        pdf = PDF_FOLDER / f"{doc_id}.pdf"
        if not pdf.exists():
            print(f"  - {doc_id}  [PDF not found]")
            missing.append(doc_id)
            continue
        res = detect_pdf_columns(pdf)
        results[doc_id] = res
        ok = "✓" if not res["is_multicolumn"] else "✗"
        if not res["is_multicolumn"]:
            tn += 1
        else:
            fp += 1
        label = "MULTI " if res["is_multicolumn"] else "SINGLE"
        print(f"  {ok} {doc_id}  {label}  {_fmt(res)}")

    total   = tp + fn + tn + fp
    correct = tp + tn
    print(f"\n{'='*75}")
    print("SUMMARY")
    print(f"{'='*75}")
    print(f"  TP (correct multi)   : {tp}")
    print(f"  FN (missed multi)    : {fn}")
    print(f"  TN (correct single)  : {tn}")
    print(f"  FP (false multi)     : {fp}")
    print(f"  Missing PDFs         : {len(set(missing))}")
    if total:
        print(f"  Accuracy             : {correct}/{total}  ({correct/total*100:.1f}%)")
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    print(f"  Precision            : {precision:.3f}")
    print(f"  Recall               : {recall:.3f}")
    print(f"  F1                   : {f1:.3f}")

    if fn:
        print(f"\nFALSE NEGATIVES (expected MULTI, got SINGLE):")
        for doc_id in sorted(EXPECTED_MULTICOLUMN):
            r = results.get(doc_id)
            if r and not r["is_multicolumn"]:
                print(f"  {doc_id}  {_fmt(r)}")

    if fp:
        print(f"\nFALSE POSITIVES (expected SINGLE, got MULTI):")
        for doc_id in sorted(single_ids):
            r = results.get(doc_id)
            if r and r["is_multicolumn"]:
                print(f"  {doc_id}  {_fmt(r)}")
