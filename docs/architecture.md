# Architecture

## End-to-End Pipeline

The project follows a sequential pipeline from raw data to deployed API:

```mermaid
flowchart TB
    subgraph Phase1["1. Data Preparation"]
        A1[SEDICI CSV] --> A2[Filter & Map\nMetadata]
        A2 --> A3[Download PDFs]
        A3 --> A4[Extract Text\n+ OCR]
        A4 --> A5[Clean Metadata\nRegex rules for ISSN, ISBN,\nrights, exact attrs\n+ Cloud LLM validation\nGemini or OpenAI]
        A5 --> A6[Final Dataset\nJSON]
    end

    subgraph Phase2["2. Training"]
        B1[Fine-Tune LLM\nLED / LLAMA / GEMMA]
        B2[Train Type\nClassifier]
        B3[Train Subject\nClassifier SVM]
    end

    subgraph Phase3["3. API Deployment"]
        C1[Orchestrator\n:8000]
        C2[Extractor\n:8001]
        C3[LLM Service - Fine-tuned\n:8002]
        C4[LLM Service - DeepAnalyze\n:8003\nOptional, extensible]
    end

    subgraph Phase4["4. Validation"]
        D1[Test Dataset] --> D2[Compare\nPredictions vs\nGround Truth]
        D2 --> D3[Metrics &\nDashboard]
    end

    A6 --> B1
    A6 --> B2
    A6 --> B3
    B1 --> C3
    B2 --> C1
    B3 --> C1
    C1 --> Phase4
```

## API Microservices Architecture

When a user uploads a PDF, the Orchestrator coordinates the services:

```mermaid
sequenceDiagram
    participant Client
    participant Orchestrator as Orchestrator :8000
    participant Extractor as Extractor :8001
    participant LLM as LLM Service :8002
    participant Deep as LLM Service - DeepAnalyze :8003

    Client->>Orchestrator: POST /upload (PDF)
    Orchestrator->>Extractor: POST /extract (PDF)
    Extractor-->>Orchestrator: plain_text + xml_text

    Note over Orchestrator: Classify document type<br/>(TF-IDF + sklearn model)
    Note over Orchestrator: Classify subject<br/>(SVM model)

    Orchestrator->>LLM: POST /consume-llm (text + type prompt)
    LLM-->>Orchestrator: extracted metadata JSON

    opt DeepAnalyze enabled
        Orchestrator->>Deep: POST /consume-llm (metadata for validation)
        Deep-->>Orchestrator: validated/refined metadata
    end

    Orchestrator-->>Client: Final metadata JSON
```

!!! info "Extensible LLM Services"
    The LLM Service structure is reusable. DeepAnalyze runs as a separate instance of the same service on port 8003, using a larger non-fine-tuned model to validate results. New LLM services can be added following the same pattern.

## Data Flow Through the System

```mermaid
flowchart LR
    PDF[PDF Document] --> EXT[Text Extraction\npdfplumber + EasyOCR]
    EXT --> TYPE[Type Classification\nTF-IDF + sklearn]
    EXT --> SUBJ[Subject Classification\nSVM]
    EXT --> LLM[LLM Extraction\nFine-tuned LED]

    TYPE --> MERGE[Merge Results]
    SUBJ --> MERGE
    LLM --> MERGE
    MERGE --> JSON[Structured\nMetadata JSON]
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI + Uvicorn |
| Containerization | Docker + Docker Compose |
| Text Extraction | pdfplumber, PyMuPDF, EasyOCR |
| LLM Fine-Tuning | HuggingFace Transformers, PEFT, LoRA |
| Base Models | LED (primary), LLAMA, GEMMA, Mistral |
| Classification | scikit-learn, XGBoost |
| Data Cleaning | Google Gemini API / OpenAI API + regex rules |
| Frontend (Metrics) | React + TypeScript + Recharts |
