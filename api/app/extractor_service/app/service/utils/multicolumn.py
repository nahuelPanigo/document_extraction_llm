"""
Column-layout detection for PDF pages.

Two complementary methods vote per page:
  A) Char-gap  — groups characters by y-coordinate, looks for x-gap in the middle zone.
  B) Histogram — bins word x-centers, looks for a low-density valley in the middle zone.

A document is considered multi-column when > 60% of the first 5 content pages
(or any page in a 1-2 page doc) are flagged as multi-column.
"""

from collections import defaultdict

_MIN_WORDS_FOR_VOTE = 25


def detect_columns_char_gap(page, min_gap_pts: float = 12.0, min_line_ratio: float = 0.35) -> dict:
    chars = page.chars
    if not chars:
        return {"columns": 1, "confidence": 0.0, "method": "A"}

    page_width = page.width

    all_x0s = [c["x0"] for c in chars]
    right_thresh = page_width * 0.75
    right_x0s = [x for x in all_x0s if x >= right_thresh]
    if len(right_x0s) / max(len(all_x0s), 1) > 0.05:
        x_span = max(right_x0s) - min(right_x0s)
        if x_span < page_width * 0.10:
            return {"columns": 1, "confidence": 0.0, "method": "A"}

    line_map: dict[int, list] = defaultdict(list)
    for c in chars:
        y_key = round(c["top"] / 2) * 2
        line_map[y_key].append(c["x0"])

    gap_lines = 0
    total_lines = 0

    for xs_unsorted in line_map.values():
        xs = sorted(xs_unsorted)
        if len(xs) < 8:
            continue
        line_span = xs[-1] - xs[0]
        if line_span < page_width * 0.40:
            continue
        total_lines += 1

        for i in range(len(xs) - 1):
            gap = xs[i + 1] - xs[i]
            rel_pos = (xs[i] - xs[0]) / line_span
            if gap >= min_gap_pts and 0.25 <= rel_pos <= 0.75:
                gap_lines += 1
                break

    if total_lines < 3:
        return {"columns": 1, "confidence": 0.0, "method": "A"}

    ratio = gap_lines / total_lines
    return {"columns": 2 if ratio >= min_line_ratio else 1, "confidence": round(ratio, 2), "method": "A"}


def detect_columns_histogram(page, n_bins: int = 20, valley_threshold: float = 0.35) -> dict:
    words = page.extract_words()
    if len(words) < 25:
        return {"columns": 1, "confidence": 0.0, "method": "B", "split_x": None}

    page_width = page.width
    bin_width = page_width / n_bins

    bins = [0] * n_bins
    for w in words:
        x_center = (w["x0"] + w["x1"]) / 2
        bin_idx = min(int(x_center / bin_width), n_bins - 1)
        bins[bin_idx] += 1

    max_count = max(bins)
    if max_count == 0:
        return {"columns": 1, "confidence": 0.0, "method": "B", "split_x": None}

    right_zone_start = int(n_bins * 0.70)
    right_zone_bins = bins[right_zone_start:]
    right_zone_total = sum(right_zone_bins)
    if right_zone_total >= 10 and max(right_zone_bins) / right_zone_total > 0.60:
        return {"columns": 1, "confidence": 0.0, "method": "B", "split_x": None, "right_spike": True}

    mid_start = int(n_bins * 0.30)
    mid_end = int(n_bins * 0.70)
    mid_bins = bins[mid_start:mid_end]
    min_val = min(mid_bins)
    valley_bin = mid_start + mid_bins.index(min_val)
    valley_ratio = min_val / max_count

    if valley_ratio < valley_threshold:
        split_x = (valley_bin + 0.5) * bin_width
        left_words = sum(bins[:valley_bin])
        right_words = sum(bins[valley_bin + 1:])

        if left_words >= 10 and right_words >= 10:
            return {
                "columns": 2,
                "confidence": round(1.0 - valley_ratio, 2),
                "method": "B",
                "split_x": round(split_x, 1),
                "valley_ratio": round(valley_ratio, 2),
            }

    return {
        "columns": 1,
        "confidence": round(valley_ratio, 2),
        "method": "B",
        "split_x": None,
        "valley_ratio": round(valley_ratio, 2),
    }


def detect_page_columns(page) -> dict:
    result_a = detect_columns_char_gap(page)
    result_b = detect_columns_histogram(page)

    multi_a = result_a["columns"] > 1 and result_a["confidence"] >= 0.35
    multi_b = result_b["columns"] > 1

    if result_b.get("right_spike") and multi_a and not multi_b:
        if len(page.extract_words()) <= 250:
            multi_a = False

    verdict = 2 if (multi_a or multi_b) else 1
    return {"columns": verdict, "method_a": result_a, "method_b": result_b}
