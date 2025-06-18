from app.services.llms_extraction import ModelExtraction
from app.errors.error import ROUTE_ERRORS as RO_E
from fastapi import APIRouter,HTTPException
from app.middleware.security import verify_bearer_token
from fastapi import Depends
from app.logging_config import logging
from pydantic import BaseModel

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
async def consume_llm(req: LLMRequest):
    if not req.text:
        raise HTTPException(
            status_code=RO_E["CODE_ERROR_NO_INPUT_DATA"],
            detail=RO_E["ERROR_NO_INPUT_DATA"]
        )
    logger.info(f"loading model")
    model_extraction = ModelExtraction()
    logger.info(f"starting model extraction")
    response_ml,error = model_extraction.model_extraction(req.text)
    logger.info(f"respose model extraction: {response_ml}")
    if (error is not None):
        raise HTTPException(status_code=error, detail=response_ml.get("error", "Unknown error during model extraction"))
    return response_ml
