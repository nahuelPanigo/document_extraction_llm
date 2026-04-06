"""
Benchmark the extractor service on all 60 validation documents.

Measures time for both endpoints:
  /extract           (plain text, no tags)
  /extract-with-tags (text with XML tags)

Usage:
    python validation/benchmark_extraction.py

Requires the extractor service running at EXTRACTOR_URL (default http://localhost:8001).
Set EXTRACTOR_TOKEN in your .env or environment.
"""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).resolve().parents[1]))

from constants import PDF_FOLDER, RESULT_FOLDER_VALIDATION
from utils.text_extraction.read_and_write_files import read_data_json
from utils.consume_apis.consume_extractor import make_requests_only_text, make_requests_xml_text

EXTRACTOR_URL   = os.getenv("EXTRACTOR_URL", "http://localhost:8001")
EXTRACTOR_TOKEN = os.getenv("EXTRACTOR_TOKEN", "")
SLOW_THRESHOLD  = 45.0   # seconds — flag docs above this
TYPES           = ["Libro", "Tesis", "Articulo", "Objeto de conferencia"]

OUTPUT_JSON = Path(__file__).parent / "result" / "extraction_benchmark.json"


def _norm_type(t: str) -> str:
    t = str(t).lower()
    if "tesis" in t:       return "Tesis"
    if "articulo" in t or "artículo" in t: return "Articulo"
    if "libro" in t:       return "Libro"
    if "conferencia" in t: return "Objeto de conferencia"
    return "Other"


def _stats(times: list) -> dict:
    if not times:
        return {"min": None, "max": None, "avg": None, "n": 0}
    return {
        "min": round(min(times), 2),
        "max": round(max(times), 2),
        "avg": round(sum(times) / len(times), 2),
        "n":   len(times),
    }


def _print_stats(label: str, times: list):
    if not times:
        return
    s = _stats(times)
    print(f"   {label} (n={s['n']}): min={s['min']:.2f}s  max={s['max']:.2f}s  avg={s['avg']:.2f}s")


def run():
    json_file = RESULT_FOLDER_VALIDATION / "final_to_compare_original.json"
    data = read_data_json(json_file, "utf-8")
    if not data:
        print("❌ No data found")
        return

    print(f"📋 Benchmarking extractor on {len(data)} documents")
    print(f"   Extractor URL : {EXTRACTOR_URL}")
    print(f"   Slow threshold: {SLOW_THRESHOLD}s")
    print("=" * 70)

    results = {}
    no_tags_times  = []
    with_tags_times = []
    no_tags_type_times  = {t: [] for t in TYPES}
    with_tags_type_times = {t: [] for t in TYPES}
    slow_no_tags  = []
    slow_with_tags = []

    for doc_id, meta in data.items():
        if not doc_id:
            continue

        pdf_path = PDF_FOLDER / f"{doc_id}.pdf"
        if not pdf_path.exists():
            print(f"⚠️  PDF not found: {doc_id}")
            continue

        doc_type = _norm_type(meta.get("type", ""))
        print(f"\n📄 {doc_id}  [{doc_type}]")

        # ── /extract (no tags) ────────────────────────────────────────────────
        try:
            t0 = time.time()
            make_requests_only_text(
                file_path=pdf_path,
                token=EXTRACTOR_TOKEN,
                normalization=True,
                host_url=EXTRACTOR_URL,
                ocr=False,
            )
            t_no_tags = round(time.time() - t0, 2)
        except Exception as e:
            print(f"   ❌ /extract error: {e}")
            t_no_tags = None

        # ── /extract-with-tags ────────────────────────────────────────────────
        try:
            t0 = time.time()
            make_requests_xml_text(
                file_path=pdf_path,
                token=EXTRACTOR_TOKEN,
                normalization=True,
                host_url=EXTRACTOR_URL,
                ocr=False,
            )
            t_with_tags = round(time.time() - t0, 2)
        except Exception as e:
            print(f"   ❌ /extract-with-tags error: {e}")
            t_with_tags = None

        print(f"   no-tags={t_no_tags}s   with-tags={t_with_tags}s", end="")

        flags = []
        if t_no_tags is not None:
            no_tags_times.append(t_no_tags)
            if doc_type in no_tags_type_times:
                no_tags_type_times[doc_type].append(t_no_tags)
            if t_no_tags >= SLOW_THRESHOLD:
                slow_no_tags.append((doc_id, doc_type, t_no_tags))
                flags.append("⚠️ SLOW no-tags")

        if t_with_tags is not None:
            with_tags_times.append(t_with_tags)
            if doc_type in with_tags_type_times:
                with_tags_type_times[doc_type].append(t_with_tags)
            if t_with_tags >= SLOW_THRESHOLD:
                slow_with_tags.append((doc_id, doc_type, t_with_tags))
                flags.append("⚠️ SLOW with-tags")

        if flags:
            print(f"  {', '.join(flags)}", end="")
        print()

        results[doc_id] = {
            "type":        doc_type,
            "no_tags_s":   t_no_tags,
            "with_tags_s": t_with_tags,
        }

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("⏱️  OVERALL STATS")
    print(f"\n  /extract (no tags):")
    _print_stats("All", no_tags_times)
    for t in TYPES:
        _print_stats(t, no_tags_type_times[t])

    print(f"\n  /extract-with-tags:")
    _print_stats("All", with_tags_times)
    for t in TYPES:
        _print_stats(t, with_tags_type_times[t])

    print(f"\n🐢 SLOW DOCS (>= {SLOW_THRESHOLD}s)")
    print(f"\n  /extract (no tags) — {len(slow_no_tags)} slow:")
    for doc_id, doc_type, t in sorted(slow_no_tags, key=lambda x: -x[2]):
        print(f"   {doc_id}  [{doc_type}]  {t:.2f}s")

    print(f"\n  /extract-with-tags — {len(slow_with_tags)} slow:")
    for doc_id, doc_type, t in sorted(slow_with_tags, key=lambda x: -x[2]):
        print(f"   {doc_id}  [{doc_type}]  {t:.2f}s")

    # ── Save JSON ─────────────────────────────────────────────────────────────
    output = {
        "threshold_s": SLOW_THRESHOLD,
        "overall": {
            "no_tags":   _stats(no_tags_times),
            "with_tags": _stats(with_tags_times),
        },
        "by_type": {
            t: {
                "no_tags":   _stats(no_tags_type_times[t]),
                "with_tags": _stats(with_tags_type_times[t]),
            }
            for t in TYPES
        },
        "slow_no_tags":  [{"id": i, "type": tp, "time_s": t} for i, tp, t in slow_no_tags],
        "slow_with_tags": [{"id": i, "type": tp, "time_s": t} for i, tp, t in slow_with_tags],
        "per_doc": results,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Results saved to: {OUTPUT_JSON}")


if __name__ == "__main__":
    run()
