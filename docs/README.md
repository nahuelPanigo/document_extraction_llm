# Documentation Site

This project uses [MkDocs Material](https://squidfunnel.github.io/mkdocs-material/) to generate a visual documentation site with Mermaid diagrams, search, and dark/light mode.

## Prerequisites

- Python 3.8+

## Install Dependencies

```bash
pip install mkdocs-material
```

## Run Locally (Development) in root folder!

```bash
mkdocs serve
```

This starts a local server at **http://localhost:8000** with live reload — any changes to the `docs/` folder or `mkdocs.yml` will be reflected automatically.

## Build Static Site in root folder!

```bash
mkdocs build
```

This generates the static site in the `site/` folder. You can open `site/index.html` directly in a browser or deploy it to any static hosting.

## Deploy to GitHub Pages

```bash
mkdocs gh-deploy
```

This builds the site and pushes it to the `gh-pages` branch of the repository, making it available at `https://<username>.github.io/<repo-name>/`.

## Documentation Structure

```
mkdocs.yml                                          # Site configuration and navigation
docs/
├── index.md                                         # Project overview
├── architecture.md                                  # Architecture and diagrams
├── api/
│   ├── index.md                                     # API overview, running options, env vars
│   ├── orchestrator.md                              # Orchestrator endpoints and models
│   ├── extractor.md                                 # Extractor endpoints and strategies
│   └── llm_service.md                               # LLM Service models and config
├── download_prepare_clean_normalize_sedici_dataset/
│   └── index.md                                     # Data pipeline stages
├── fine_tunning/
│   └── index.md                                     # LLM fine-tuning process
├── fine_tune_type/
│   └── index.md                                     # Document type classifier
├── fine_tune_subject/
│   └── index.md                                     # Subject classifier
├── validation/
│   └── index.md                                     # Validation and metric checker
├── utils/
│   └── index.md                                     # Shared utilities
├── data.md                                          # Data folder structure and constants
└── scripts.md                                       # Run scripts and env vars
```

## Adding New Pages

1. Create a new `.md` file inside `docs/`
2. Add it to the `nav` section in `mkdocs.yml`
3. Use standard Markdown with Mermaid diagrams:

````markdown
```mermaid
flowchart LR
    A[Step 1] --> B[Step 2]
```
````
