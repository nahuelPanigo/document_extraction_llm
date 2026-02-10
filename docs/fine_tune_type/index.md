# Document Type Classifier

!!! warning "Work in progress"
    This module is still being modified. Documentation will be completed once changes are finalized.

Trains a classifier to identify the type of an academic document from its text content. The trained model is used by the Orchestrator API to select the correct type-specific prompt.

Run with:

```bash
./run_modules.sh fine_tune_type
```

## Classification Target

| Type | Spanish |
|------|---------|
| Thesis | Tesis |
| Book | Libro |
| Article | Articulo |
| Conference Object | Objeto de conferencia |
