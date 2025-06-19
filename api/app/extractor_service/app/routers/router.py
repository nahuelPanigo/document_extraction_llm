from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.service.reader_strategy import Reader
from app.middleware.security import verify_bearer_token
from fastapi import Depends
from fastapi.responses import JSONResponse
import os
from typing import List, Optional
from app.constants.constant import FILETYPES

def success_response(data):
    return {
        "success": True,
        "data": data,
        "error": None
    }

def error_response(code: int, message: str):
    return JSONResponse(
        status_code=code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message
            }
        }
    )

def is_valid_filetype(filename: str, allowed_types: List[str]) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_types

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
    normalization: Optional[bool] = Form(True, description="Apply text normalization")
):
    
    if not is_valid_filetype(file.filename, FILETYPES):
        return error_response(
            code=415,
            message=f"Unsupported file type. Allowed types are: {', '.join(FILETYPES)}"
        )
    reader = Reader(file)
    result = reader.get_text(normalization=normalization)

    if not result["success"]:
        return error_response(
            code=result["error"]["code"],
            message=result["error"]["message"]
        )

    return success_response(result["data"])


@router.post("/extract-with-tags", dependencies=[Depends(verify_bearer_token)])
async def extract_text_with_tags(
    file: UploadFile = File(...),
    normalization: Optional[bool] = Form(True, description="Apply text normalization")
):
    if not is_valid_filetype(file.filename, FILETYPES):
        return error_response(
            code=415,
            message=f"Unsupported file type. Allowed types are: {', '.join(FILETYPES)}"
    )
    reader = Reader(file)
    result = reader.get_text_with_tags(normalization=normalization)

    if not result["success"]:
        return error_response(
            code=result["error"]["code"],
            message=result["error"]["message"]
        )

    return success_response(result["data"])