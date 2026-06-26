# Docs Expert Memory

last_commit: 96b9cfd7659cfe5e7b2c5634681f757af3ad83a6
last_run: 2026-06-21

## Last Run Summary

First run. Reviewed all docs/ against 5 unreviewed commits (176f2aa..96b9cfd) covering: multicolumn PDF abstract extraction, orchestrator pattern_extractors (regex/TF-IDF abstract+keywords, post-processing pipeline), a fine_tune_subject/fine_tune_type refactor that moved all ML training strategies (SVM/XGBoost/RandomForest/embeddings/embeddings_knn/neural/minilm) into a new shared `utils/ml_strategies/` package, constants.py changes (date format dd-mm-yyyy → yyyy/mm/dd, model/provider defaults, new model-folder constants), dataset/HuggingFace repo rename, and new validation scripts (`run_comparison.py`, `benchmark_extraction.py`).

Changes made:
- `docs/api/extractor.md` — documented `max_words`/`multicolumn`/`strip_footers` params, `is_multicolumn` response field, new Multi-Column Detection section (methods A/B voting), easyocr+poppler-utils requirement.
- `docs/api/orchestrator.md` — documented automatic multicolumn re-fetch for abstract, new `pattern_extractors.py` module (abstract regex extraction, keywords regex+TF-IDF — LLM never extracts these), full post-processing pipeline (honorifics/dedup/normalize/validate-formats/validate-in-text), added missing Environment Variables section.
- `docs/api/llm_service.md` — minor: `transformers==4.41.2` → unpinned `transformers`.
- `docs/fine_tune_subject/index.md` and `docs/fine_tune_type/index.md` — fully rewritten (removed stale "WIP" banners); both now documented as sharing `utils/ml_strategies/` strategy classes, each with module structure tables.
- `docs/utils/index.md` — added `ml_strategies/` section, expanded normalization function table (fix_unicode_escapes, fix_ocr_accents, remove_accents), noted pdf_reader.py has no multicolumn support (API's pdf_reader_strategy.py does).
- `docs/data.md` — updated CLEAN_PROVIDER_TO_USE/GENAI_MODEL/OPENAI_MODEL defaults, added model-folder constants, noted date format change and PROMPT_CLOUD_LLM_VALIDATOR (separate from PROMPT_CLEANER_METADATA), renamed final dataset filename/HF repo.
- `docs/validation/index.md` — added `run_comparison.py` and `benchmark_extraction.py`, updated ground-truth filename, noted GROBID/langsmith now track per-doc timing stats.
- `docs/architecture.md` — updated sequence diagram (multicolumn re-fetch, post-processing, pattern extraction) and data-flow diagram (pattern extraction node).
- `docs/index.md` — added "ML training strategies" to the utils/ description for consistency with README.md.

Not touched: the `graphs/*.drawio.xml` files (api_architecture, api_services, pipeline_*) — these are visual diagrams, likely graph-expert's responsibility, not mkdocs content.

## Docs Registry
| File/Section | Covers | Last Updated |
|---|---|---|
| `docs/index.md` | Project overview | 2026-06-21 |
| `docs/architecture.md` | System architecture | 2026-06-21 |
| `docs/api/orchestrator.md` | Orchestrator API | 2026-06-21 |
| `docs/api/extractor.md` | Extractor Service | 2026-06-21 |
| `docs/api/llm_service.md` | LLM Service | 2026-06-21 |
| `docs/download_prepare_clean_normalize_sedici_dataset/` | Data pipeline | — (not reviewed this run) |
| `docs/fine_tunning/` | General fine-tuning | — (not reviewed this run) |
| `docs/fine_tune_type/` | Type classifier | 2026-06-21 |
| `docs/fine_tune_subject/` | Subject classifier | 2026-06-21 |
| `docs/validation/` | Validation | 2026-06-21 |
| `docs/utils/` | Utilities | 2026-06-21 |
| `docs/data.md` | Data & constants | 2026-06-21 |
| `docs/scripts.md` | Run scripts | 2026-06-21 (checked, no changes needed) |
