from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from app.service.reader_strategy import Reader
from app.middleware.security import verify_bearer_token
from fastapi import Depends


router = APIRouter()


@router.get("/health")
async def root():
    return {"message-info": "server is up"}


@router.get("/test-integration", dependencies=[Depends(verify_bearer_token)])
async def test_integration():
    return {"message": "Integration tests passed"}


@router.post("/extract", dependencies=[Depends(verify_bearer_token)])
async def extract_text(
    file: UploadFile = File(...),
    normalization: bool = Query(True, description="Apply text normalization")
):
    reader = Reader(file)
    result = reader.get_text(normalization=normalization)

    if not result["success"]:
        raise HTTPException(
            status_code=result["error"]["code"],
            detail=result["error"]["message"]
        )

    return result["data"]

@router.post("/extract-with-tags", dependencies=[Depends(verify_bearer_token)])
async def extract_text_with_tags(
    file: UploadFile = File(...),
    normalization: bool = Query(True, description="Apply text normalization")
):
    reader = Reader(file)
    result = reader.get_text_with_tags(normalization=normalization)

    if not result["success"]:
        raise HTTPException(
            status_code=result["error"]["code"],
            detail=result["error"]["message"]
        )

    return result["data"]