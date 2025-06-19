from app.services.llms_extraction import ModelExtraction
from app.errors.error import ROUTE_ERRORS as RO_E
from fastapi import APIRouter,HTTPException
from app.middleware.security import verify_bearer_token
from fastapi import Depends, Body
from app.logging_config import logging
from pydantic import BaseModel
from fastapi.responses import JSONResponse

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

logger = logging.getLogger(__name__)
router = APIRouter()

class LLMRequest(BaseModel):
    text: str

@router.get("/health")
async def root():
    return {"message-info": "server is up"}

@router.get("/test-integration", dependencies=[Depends(verify_bearer_token)])
async def test_integration():
    return {"message": "Integration tests passed"}


@router.post('/consume-llm', dependencies=[Depends(verify_bearer_token)])
async def consume_llm(req: LLMRequest = Body(..., media_type="application/json")):
    if not req.text:
        return error_response(
            code=RO_E["CODE_ERROR_NO_INPUT_DATA"],
            message=RO_E["ERROR_NO_INPUT_DATA"]
        )

    logger.info("loading model")
    model_extraction = ModelExtraction()

    logger.info("starting model extraction")
    response_ml, error = model_extraction.model_extraction(req.text)
    logger.info(f"response model extraction: {response_ml}")

    if error is not None:
        return error_response(
            code=error,
            message=response_ml.get("error", "Unknown error during model extraction")
        )

    return success_response(response_ml)
