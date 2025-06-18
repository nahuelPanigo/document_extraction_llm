from fastapi import FastAPI
from app.routers.router import router

description = """
Orchestrator for document parsing and metadata extraction in json format
conneted extractor service (to extract text in multiple formats)
and to llm service (to extract metadata in json format)
"""

app = FastAPI(
    title="MetadataDocumentExtraction",
    description=description,
    summary="This API receives a document as a request that can be 'pdf, docx or ods' and extracts the metadata necessary for uploading to the sedici repository.",
    version="0.0.1",
)


app.include_router(router)



