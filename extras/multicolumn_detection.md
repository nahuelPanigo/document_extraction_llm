# Multi-column PDF Detection

## Overview

`multicolumn_detection.py` detects whether a PDF page uses a multi-column layout
(two-column academic papers, tables, structured thesis documents, etc.).

Accuracy on the validation set: **16/16 (100%)** — 10 multi-column, 6 single-column.

---

## How it works

Two independent methods vote at the page level. If either fires, the page is
flagged as multi-column. A document is called multi-column if **> 60% of the
first 5 pages** are flagged.

### Method A — Character-gap per line

Uses raw character positions (`page.chars`) — no layout reconstruction needed.

1. Groups characters into text lines by bucketing their `top` (y) coordinate into 2 pt bands.
2. For each line spanning ≥ 40% of page width with ≥ 8 chars, sorts all character x-positions.
3. Looks for a consecutive x-jump ≥ 12 pt in the middle 25–75% zone → that jump is the column gutter.
4. If ≥ 35% of qualifying lines have such a gap → **page is multi-column**.

**Best at:** Documents where text lines physically span both columns (WICC conference format, tables).  
**Weakness:** Misses pages where columns are short or mostly images (EBEC graphical abstract pages).

### Method B — X-histogram valley detection

Uses word bounding boxes (`page.extract_words()`).

1. Divides page width into 20 bins (~5% each) and counts words per bin by x-center.
2. Finds the minimum bin in the middle 30–70% zone (the gutter candidate).
3. If `valley / max_bin < 0.35` AND both sides have ≥ 5 words → **page is multi-column**.
4. `B_conf = 1 − valley_ratio` (deeper valley = higher confidence).

**Best at:** Bimodal word distributions (EBEC two-column format, most standard two-column papers).  
**Weakness:** Sparse pages (few words) can create fake valleys → filtered by the 60% document threshold.

### Key thresholds

| Parameter | Value | Reason |
|---|---|---|
| `valley_threshold` | 0.35 | Catches shallow gutters (EBEC docs have valley ≈ 0.25–0.33) |
| `min_gap_pts` (A) | 12 pt | ~4 mm — minimum gutter width |
| `min_line_ratio` (A) | 0.35 | 35% of lines must show the gap |
| `min_side_words` (B) | 5 | At least 5 words on each side of the valley |
| Document ratio | > 0.60 | > 60% of pages must be multi-column |
| `max_pages` | 5 | Only analyse first 5 pages |

---

## Known document types

| Format | Columns | Detection |
|---|---|---|
| EBEC UNLP "Investigación Joven" | 2 | Method B (bimodal word distribution) |
| WICC workshop papers | 2 | Both A and B |
| Thesis/TIF structured with tables | multi | Method A (char gaps in table rows) |
| 3-column newsletter/journal | 3 | Method B |

---

## TODO

### Column normalization (next step)

Once a page is detected as multi-column, the extracted text needs to be
**re-ordered** so that downstream processing (abstract extraction, metadata
extraction) reads the columns in the correct logical order instead of getting
interleaved lines from both columns.

**Approach:**

1. Detect the column split point(s) using `detect_pdf_columns()` — the
   histogram valley gives the `split_x` coordinate.
2. For each multi-column page, crop into column slices using `pdfplumber`'s
   `page.crop(bbox)`:
   ```
   left_col  = page.crop((0,      0, split_x,     page.height))
   right_col = page.crop((split_x, 0, page.width,  page.height))
   ```
3. Extract text from each slice independently (left column first, then right).
4. Concatenate: `left_text + "\n\n" + right_text`.
5. For 3+ columns, repeat with multiple split points.

**Where to integrate:**

- In `pdf_reader_strategy.py` → `_process_page_plain()` and
  `extract_text_with_xml_tags()` in the extractor service.
- Call `detect_page_columns(page)` before extracting; if multi-column, use
  the crop approach instead of `page.extract_text()` / `page.extract_words()`.
- The `split_x` from Method B (`detect_columns_histogram`) can be used directly
  as the crop boundary.

**Expected impact:** Fixes abstract extraction for all two-column docs currently
in the poor-match bucket (10915-117917, 10915-117661, 10915-117660,
10915-117729, 10915-117224, 10915-117443, 10915-145097, 10915-145103).
