from fastapi import FastAPI
from .router import router

description = """
Description:
api with llm integration
for document parsing and metadata extraction in json format
"""

app = FastAPI(
    title="MetadataDocumentExtraction",
    description=description,
    summary="This API receives a document as a request that can be 'pdf, word, doc or ppt' and extracts the metadata necessary for uploading to the sedici repository.",
    version="0.0.1",
)


app.include_router(router)



