"""
Full comparison runner — compares FINETUNNED, CLOUDLLM and GROBID against
the ground truth using the backend metric-checker API (or direct import fallback).

Files used:
  Ground truth : validation/result/final_to_compare_original.json
  FINETUNNED   : validation/result/FINETUNNED/final_to_compare.json
  CLOUDLLM     : validation/result/CLOUDLLM/final_to_compare.json
  GROBID       : validation/result/GROBID/final_to_compare.json

Output:
  validation/result/full_comparison_results.json   — raw per-system metrics
  validation/result/full_comparison_report.txt     — human-readable summary

Usage:
    # With backend running:
    cd validation/backend/metric-checker && python index.py
    python validation/run_comparison.py

    # Without backend (direct import):
    python validation/run_comparison.py
"""

import json
import sys
import unicodedata
import requests
from pathlib import Path

ROOT          = Path(__file__).resolve().parent.parent
RESULT_FOLDER = ROOT / "validation" / "result"
BACKEND_DIR   = ROOT / "validation" / "backend" / "metric-checker"
BACKEND_URL   = "http://localhost:8001/api/metrics"

GROUND_TRUTH  = RESULT_FOLDER / "final_to_compare_original.json"
OUTPUT_JSON   = RESULT_FOLDER / "full_comparison_results.json"
OUTPUT_TXT    = RESULT_FOLDER / "full_comparison_report.txt"

NULL_THRESHOLD = 0.80   # flag fields where >80 % of predictions are null

SYSTEMS = {
    "FINETUNNED": RESULT_FOLDER / "FINETUNNED" / "final_to_compare.json",
    "CLOUDLLM":   RESULT_FOLDER / "CLOUDLLM"   / "final_to_compare.json",
    "GROBID":     RESULT_FOLDER / "GROBID"     / "final_to_compare.json",
}

sys.path.insert(0, str(BACKEND_DIR))


# ── helpers ───────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_via_api(original: dict, predicted: dict) -> dict:
    orig_bytes = json.dumps(original, ensure_ascii=False).encode("utf-8")
    pred_bytes = json.dumps(predicted, ensure_ascii=False).encode("utf-8")
    r = requests.post(
        BACKEND_URL,
        files={
            "original_file":  ("original.json", orig_bytes, "application/json"),
            "predicted_file": ("predicted.json", pred_bytes, "application/json"),
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


def run_direct(original: dict, predicted: dict) -> dict:
    from run_metrics import run_metric_comparison
    orig_bytes = json.dumps(original, ensure_ascii=False).encode("utf-8")
    pred_bytes = json.dumps(predicted, ensure_ascii=False).encode("utf-8")
    return run_metric_comparison(orig_bytes, pred_bytes)


def normalize_predicted(predicted: dict) -> dict:
    """
    If a document's 'keywords' field is a dict with a 'real' key, replace it
    with that list so the metric checker compares against pattern-extracted keywords.
    """
    result = {}
    for doc_id, doc in predicted.items():
        doc = dict(doc)
        kw = doc.get("keywords")
        if isinstance(kw, dict) and "real" in kw:
            doc["keywords"] = kw["real"] if kw["real"] else None
        result[doc_id] = doc
    return result


def compare(original: dict, predicted: dict) -> dict:
    predicted = normalize_predicted(predicted)
    try:
        return run_via_api(original, predicted)
    except Exception:
        print("    [INFO] Backend not reachable — using direct import.")
        return run_direct(original, predicted)


# ── null / non-null analysis ──────────────────────────────────────────────────

def is_empty(val) -> bool:
    """True when a value should be considered null/missing."""
    if val is None:
        return True
    if isinstance(val, str):
        return val.strip() == ""
    if isinstance(val, (list, dict)):
        return len(val) == 0
    return False


def normalize_str(s: str) -> str:
    """Lowercase + remove accents for simple comparison."""
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def simple_match(gt_val, pred_val) -> bool:
    """Best-effort exact match after normalization (handles str / list)."""
    if is_empty(gt_val) and is_empty(pred_val):
        return True
    if is_empty(gt_val) or is_empty(pred_val):
        return False
    if isinstance(gt_val, list) and isinstance(pred_val, list):
        return sorted(normalize_str(str(x)) for x in gt_val) == \
               sorted(normalize_str(str(x)) for x in pred_val)
    return normalize_str(str(gt_val)) == normalize_str(str(pred_val))


def collect_all_fields(gt: dict, pred: dict) -> set[str]:
    fields: set[str] = set()
    for doc in gt.values():
        fields.update(doc.keys())
    for doc in pred.values():
        fields.update(doc.keys())
    return fields - {"id"}


def compute_null_stats(gt: dict, pred: dict) -> dict[str, dict]:
    """
    For each field return:
      pred_null_count, pred_null_pct, gt_null_count, gt_null_pct, total
    """
    fields = collect_all_fields(gt, pred)
    common_ids = list(set(gt.keys()) & set(pred.keys()))
    total = len(common_ids)
    stats = {}
    for field in sorted(fields):
        pred_nulls = sum(1 for doc_id in common_ids if is_empty(pred[doc_id].get(field)))
        gt_nulls   = sum(1 for doc_id in common_ids if is_empty(gt[doc_id].get(field)))
        stats[field] = {
            "total":          total,
            "pred_null":      pred_nulls,
            "pred_null_pct":  pred_nulls / total if total else 0,
            "gt_null":        gt_nulls,
            "gt_null_pct":    gt_nulls   / total if total else 0,
        }
    return stats


def compute_field_breakdown(gt: dict, pred: dict, null_stats: dict) -> dict[str, dict]:
    """
    For each field where GT null% < NULL_THRESHOLD (field actually exists in dataset)
    but any system predicts null > NULL_THRESHOLD (system is missing it), compute
    per-document breakdown counts:
      null_match    — GT=null  AND pred=null  (both empty, correct absence)
      null_mismatch — GT=value AND pred=null  (system missed the field)
      ok_match      — GT=value AND pred=value AND they match  (correct extraction)
      wrong         — GT=value AND pred=value AND they differ (wrong extraction)
    """
    common_ids = list(set(gt.keys()) & set(pred.keys()))
    result = {}
    for field, stats in null_stats.items():
        # only include fields where GT has real data (< threshold null)
        if stats["gt_null_pct"] >= NULL_THRESHOLD:
            continue
        # only include fields where at least one system over-predicts null
        if stats["pred_null_pct"] <= NULL_THRESHOLD:
            continue
        counts = {"null_match": 0, "null_mismatch": 0, "ok_match": 0, "wrong": 0}
        for doc_id in common_ids:
            gt_empty   = is_empty(gt[doc_id].get(field))
            pred_empty = is_empty(pred[doc_id].get(field))
            if gt_empty and pred_empty:
                counts["null_match"] += 1
            elif not gt_empty and pred_empty:
                counts["null_mismatch"] += 1
            elif not gt_empty and not pred_empty:
                if simple_match(gt[doc_id].get(field), pred[doc_id].get(field)):
                    counts["ok_match"] += 1
                else:
                    counts["wrong"] += 1
            # gt_empty and pred not empty = hallucination, omitted for brevity
        result[field] = counts
    return result


def compute_null_stats_by_type(gt: dict, pred: dict) -> dict[str, dict[str, dict]]:
    """
    Same as compute_null_stats but broken down by document type.
    Returns {doc_type: {field: stats}}.
    """
    # group doc_ids by type (from GT)
    type_groups: dict[str, list[str]] = {}
    common_ids = set(gt.keys()) & set(pred.keys())
    for doc_id in common_ids:
        dtype = (gt[doc_id].get("type") or "unknown").strip().lower().capitalize()
        type_groups.setdefault(dtype, []).append(doc_id)

    result = {}
    for dtype, ids in type_groups.items():
        gt_sub   = {i: gt[i]   for i in ids}
        pred_sub = {i: pred[i] for i in ids}
        result[dtype] = compute_null_stats(gt_sub, pred_sub)
    return result


# ── extraction helpers ────────────────────────────────────────────────────────

def get_field_scores(metrics: dict) -> dict[str, dict]:
    scores: dict[str, dict] = {}
    for entry in metrics.get("detailed_results", []):
        field = entry.get("field_name") or "__overall__"
        mtype = entry.get("metric_type", "")
        if field not in scores:
            scores[field] = {}
        if mtype == "exact_equality":
            scores[field]["exact_accuracy"] = entry.get("accuracy")
        elif mtype == "f1_score":
            scores[field]["f1_score"]  = entry.get("f1_score")
            scores[field]["precision"] = entry.get("precision")
            scores[field]["recall"]    = entry.get("recall")
        elif mtype == "list_percentage_match":
            scores[field]["list_pct"]  = entry.get("average_percentage")
    return scores


def get_type_scores(metrics: dict) -> dict[str, dict]:
    out = {}
    for dtype, data in metrics.get("type_specific_results", {}).items():
        perf = data.get("summary", {}).get("overall_performance", {})
        if perf:
            out[dtype] = perf
    return out


def overall_perf(metrics: dict) -> dict:
    return metrics.get("summary", {}).get("overall_performance", {})


# ── report helpers ────────────────────────────────────────────────────────────

def fmt(val) -> str:
    if val is None:
        return "  N/A  "
    return f"{val:6.3f}"


def fmt_pct(val) -> str:
    if val is None:
        return "  N/A  "
    return f"{val*100:5.1f}%"


def winner(values: dict[str, float | None]) -> str:
    valid = {k: v for k, v in values.items() if v is not None}
    if not valid:
        return "—"
    return max(valid, key=lambda k: valid[k])


def build_report(
    all_metrics:       dict[str, dict],
    all_null_stats:    dict[str, dict[str, dict]],
    all_breakdown:     dict[str, dict[str, dict]],       # {system: {field: {null_match,null_mismatch,ok_match,wrong}}}
    all_null_by_type:  dict[str, dict[str, dict[str, dict]]],
    all_raw:           dict[str, tuple[dict, dict]],
) -> str:
    systems = list(all_metrics.keys())
    lines = []
    W = 90

    def sep(char="─"):
        lines.append(char * W)

    def header(title: str):
        sep("═")
        lines.append(f"  {title}")
        sep("═")

    def col_header():
        row = f"  {'Field':<30}"
        for s in systems:
            row += f"  {s:^12}"
        row += f"  {'WINNER':^12}"
        lines.append(row)
        sep()

    metrics_keys = [
        ("average_exact_accuracy",  "Avg Exact Accuracy"),
        ("average_f1_score",        "Avg F1 Score      "),
        ("average_list_percentage", "Avg List Match %  "),
    ]

    # ── 1. Overall performance ─────────────────────────────────────────────
    header("OVERALL PERFORMANCE")
    for key, label in metrics_keys:
        vals = {s: overall_perf(all_metrics[s]).get(key) for s in systems}
        row = f"  {label:<30}"
        for s in systems:
            row += f"  {fmt(vals[s]):^12}"
        row += f"  {winner(vals):^12}"
        lines.append(row)
    lines.append("")

    # ── 2. Per-field comparison ────────────────────────────────────────────
    header("PER-FIELD COMPARISON")

    all_fields: set[str] = set()
    field_data: dict[str, dict[str, dict]] = {}
    for s in systems:
        fd = get_field_scores(all_metrics[s])
        field_data[s] = fd
        all_fields.update(fd.keys())

    all_fields.discard("__overall__")
    all_fields_sorted = sorted(all_fields)

    for metric_label, metric_key in [
        ("Exact Accuracy", "exact_accuracy"),
        ("F1 Score",       "f1_score"),
        ("List Match %",   "list_pct"),
    ]:
        lines.append(f"\n  [{metric_label}]")
        col_header()
        shown = False
        for field in all_fields_sorted:
            vals = {s: field_data[s].get(field, {}).get(metric_key) for s in systems}
            if all(v is None for v in vals.values()):
                continue
            row = f"  {field:<30}"
            for s in systems:
                row += f"  {fmt(vals[s]):^12}"
            row += f"  {winner(vals):^12}"
            lines.append(row)
            shown = True
        if not shown:
            lines.append("  (no data)")

    lines.append("")

    # ── 3. Prediction confidence (precision & recall) ──────────────────────
    header("PREDICTION CONFIDENCE — PRECISION & RECALL PER FIELD")
    lines.append(
        "  Precision = when the system predicted a value, how often was it correct?\n"
        "  Recall    = out of all values that exist in GT, how many did the system find?\n"
        "  ⚠ = field has GT null% > 80% — precision may be artificially 1.0 (backend edge case).\n"
    )

    # collect flagged fields (high GT null) to mark them
    gt_null_flagged: set[str] = set()
    for s in systems:
        for field, stats in all_null_stats[s].items():
            if stats.get("gt_null_pct", 0) >= NULL_THRESHOLD:
                gt_null_flagged.add(field)

    for metric_label, metric_key in [("Precision", "precision"), ("Recall", "recall")]:
        lines.append(f"\n  [{metric_label}]")
        col_header()
        for field in all_fields_sorted:
            vals = {s: field_data[s].get(field, {}).get(metric_key) for s in systems}
            if all(v is None for v in vals.values()):
                continue
            flag = " ⚠" if field in gt_null_flagged else "  "
            row = f"  {field:<28}{flag}"
            for s in systems:
                row += f"  {fmt(vals[s]):^12}"
            row += f"  {winner(vals):^12}"
            lines.append(row)

    lines.append("")

    # ── 4. Per-type comparison ─────────────────────────────────────────────
    header("PER-DOCUMENT-TYPE COMPARISON")

    all_types: set[str] = set()
    type_data: dict[str, dict[str, dict]] = {}
    for s in systems:
        td = get_type_scores(all_metrics[s])
        type_data[s] = td
        all_types.update(td.keys())

    for dtype in sorted(all_types):
        lines.append(f"\n  Document type: {dtype}")
        col_header()
        for key, label in metrics_keys:
            vals = {s: type_data[s].get(dtype, {}).get(key) for s in systems}
            row = f"  {label:<30}"
            for s in systems:
                row += f"  {fmt(vals[s]):^12}"
            row += f"  {winner(vals):^12}"
            lines.append(row)

    lines.append("")

    # ── 4. Null analysis — overall ─────────────────────────────────────────
    header(f"NULL / MISSING VALUE ANALYSIS  (⚠ = any system > {int(NULL_THRESHOLD*100)}% null)")
    lines.append(
        "  GT null%  = how often the correct answer is empty (same for all systems).\n"
        "  Pred null% = how often each system predicted nothing for this field.\n"
        "  —  means the field never appeared in that system's output (same as 100% null).\n"
    )

    def fmt_null(val) -> str:
        """Format a pred_null_pct; None means the field never appeared → treat as 100%."""
        if val is None:
            return "   —   "
        return fmt_pct(val)

    def render_null_table(fields_sorted, stats_by_system):
        # Single-row-per-field layout:
        # ⚠  Field               GT null%   FINETUNNED   CLOUDLLM   GROBID
        hdr = f"  {'':2} {'Field':<26} {'GT null':>8}"
        for s in systems:
            hdr += f"  {s:>10}"
        lines.append(hdr)
        sep()
        for field in fields_sorted:
            # GT null — take from first system that has data (should be same value)
            gt_pct = next(
                (stats_by_system[s].get(field, {}).get("gt_null_pct")
                 for s in systems if stats_by_system.get(s, {}).get(field)),
                None
            )
            pred_vals = {
                s: stats_by_system.get(s, {}).get(field, {}).get("pred_null_pct")
                for s in systems
            }
            # flag only when GT has real data (< threshold) but a system over-predicts null
            any_flagged = (
                gt_pct is not None and gt_pct < NULL_THRESHOLD and
                any(
                    (v is None or v > NULL_THRESHOLD)
                    for v in pred_vals.values()
                )
            )
            flag = "⚠" if any_flagged else " "
            row = f"  {flag}  {field:<26} {fmt_pct(gt_pct):>8}"
            for s in systems:
                row += f"  {fmt_null(pred_vals[s]):>10}"
            lines.append(row)

    null_fields: set[str] = set()
    for s in systems:
        null_fields.update(all_null_stats[s].keys())

    render_null_table(sorted(null_fields), all_null_stats)
    lines.append("")

    # ── 5. Null analysis — by document type ───────────────────────────────
    header("NULL ANALYSIS BY DOCUMENT TYPE")
    lines.append(
        "  Same columns as above, filtered per document type.\n"
    )

    all_types_null: set[str] = set()
    for s in systems:
        all_types_null.update(all_null_by_type[s].keys())

    for dtype in sorted(all_types_null):
        lines.append(f"\n  ── {dtype} ──")
        type_fields: set[str] = set()
        for s in systems:
            type_fields.update(all_null_by_type[s].get(dtype, {}).keys())
        type_stats = {s: all_null_by_type[s].get(dtype, {}) for s in systems}
        render_null_table(sorted(type_fields), type_stats)

    lines.append("")

    # ── 6. Field extraction breakdown ─────────────────────────────────────
    header("FIELD EXTRACTION BREAKDOWN  (GT null% < 80%, system null% > 80%)")
    lines.append(
        "  Only fields where the correct answer usually EXISTS (GT null < 80%)\n"
        "  but at least one system fails to extract it (pred null > 80%).\n"
        "\n"
        "  null_match    = GT empty  AND pred empty  → correctly left blank\n"
        "  null_mismatch = GT has value BUT pred empty → system MISSED the field\n"
        "  ok_match      = GT has value AND pred has value AND they match\n"
        "  wrong         = GT has value AND pred has value BUT they differ\n"
    )

    # collect all flagged fields across systems
    flagged_fields: set[str] = set()
    for s in systems:
        flagged_fields.update(all_breakdown[s].keys())

    if flagged_fields:
        for field in sorted(flagged_fields):
            lines.append(f"  {field}")
            hdr = f"    {'System':<14} {'null_match':>12} {'null_mismatch':>14} {'ok_match':>10} {'wrong':>7}"
            lines.append(hdr)
            sep()
            for s in systems:
                bd = all_breakdown[s].get(field)
                if bd is None:
                    lines.append(f"    {s:<14} {'—':>12} {'—':>14} {'—':>10} {'—':>7}")
                else:
                    lines.append(
                        f"    {s:<14} {bd['null_match']:>12} {bd['null_mismatch']:>14}"
                        f" {bd['ok_match']:>10} {bd['wrong']:>7}"
                    )
            lines.append("")
    else:
        lines.append("  No fields meet the criteria.")

    lines.append("")

    # ── 7. Final summary ───────────────────────────────────────────────────
    header("FINAL SUMMARY — WINNER TALLY")

    tally: dict[str, int] = {s: 0 for s in systems}

    for metric_key in ["exact_accuracy", "f1_score", "list_pct"]:
        for field in all_fields_sorted:
            vals = {s: field_data[s].get(field, {}).get(metric_key) for s in systems}
            if all(v is None for v in vals.values()):
                continue
            w = winner(vals)
            if w in tally:
                tally[w] += 1

    for dtype in all_types:
        for key, _ in metrics_keys:
            vals = {s: type_data[s].get(dtype, {}).get(key) for s in systems}
            if all(v is None for v in vals.values()):
                continue
            w = winner(vals)
            if w in tally:
                tally[w] += 1

    sep()
    for s, count in sorted(tally.items(), key=lambda x: -x[1]):
        bar = "█" * count
        lines.append(f"  {s:<14}  {count:3d} wins  {bar}")
    sep()
    best = max(tally, key=lambda k: tally[k]) if tally else "—"
    lines.append(f"\n  🏆  Best overall system: {best}")
    lines.append("")

    lines.append("  Best system per metric:")
    for key, label in metrics_keys:
        vals = {s: overall_perf(all_metrics[s]).get(key) for s in systems}
        lines.append(f"    {label.strip():<25}  →  {winner(vals)}")

    lines.append("")
    sep("═")

    return "\n".join(lines)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Full Comparison Runner")
    print("=" * 60)

    if not GROUND_TRUTH.exists():
        print(f"[ERROR] Ground truth not found: {GROUND_TRUTH}")
        sys.exit(1)
    ground_truth = load_json(GROUND_TRUTH)
    print(f"\nGround truth: {GROUND_TRUTH.name}  ({len(ground_truth)} documents)")

    available: dict[str, Path] = {}
    for name, path in SYSTEMS.items():
        if path.exists():
            available[name] = path
            print(f"  ✓ {name:<12} {path.relative_to(ROOT)}")
        else:
            print(f"  ✗ {name:<12} NOT FOUND — {path.relative_to(ROOT)}")

    if not available:
        print("\n[ERROR] No system outputs found.")
        sys.exit(1)

    all_metrics:      dict[str, dict] = {}
    all_null_stats:   dict[str, dict] = {}
    all_breakdown:    dict[str, dict] = {}
    all_null_by_type: dict[str, dict] = {}
    all_raw:          dict[str, tuple] = {}

    for name, path in available.items():
        print(f"\n── {name} ──")
        predicted_raw = load_json(path)
        common = set(predicted_raw.keys()) & set(ground_truth.keys())
        print(f"  IDs: predicted={len(predicted_raw)}  GT={len(ground_truth)}  common={len(common)}")
        if not common:
            print(f"  [WARN] No common IDs — skipping.")
            continue

        pred_filtered = normalize_predicted({k: predicted_raw[k] for k in common})
        gt_filtered   = {k: ground_truth[k] for k in common}

        # metric checker comparison
        try:
            result = compare(gt_filtered, pred_filtered)
            all_metrics[name] = result
            perf = overall_perf(result)
            print(f"  Avg exact accuracy : {perf.get('average_exact_accuracy', 'N/A')}")
            print(f"  Avg F1 score       : {perf.get('average_f1_score', 'N/A')}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            continue

        # null analysis
        ns = compute_null_stats(gt_filtered, pred_filtered)
        all_null_stats[name]   = ns
        all_breakdown[name]    = compute_field_breakdown(gt_filtered, pred_filtered, ns)
        all_null_by_type[name] = compute_null_stats_by_type(gt_filtered, pred_filtered)
        all_raw[name]          = (gt_filtered, pred_filtered)

    if not all_metrics:
        print("\n[ERROR] All comparisons failed.")
        sys.exit(1)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)
    print(f"\nRaw results → {OUTPUT_JSON}")

    report = build_report(all_metrics, all_null_stats, all_breakdown,
                          all_null_by_type, all_raw)
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report      → {OUTPUT_TXT}")

    print()
    print(report)


if __name__ == "__main__":
    main()
