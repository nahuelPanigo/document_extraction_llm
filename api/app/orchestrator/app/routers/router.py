from app.service.orchestrator import Orchestrator
from app.errors.errors import ROUTE_ERRORS as RO_E
from fastapi import APIRouter,HTTPException,UploadFile,Form,File
from enum import Enum
from app.middleware.security import verify_bearer_token
from fastapi import Depends
import os
import requests
from pydantic import BaseModel
from typing import Optional


router = APIRouter()


class Type(str, Enum):
    articulo = "Articulo"
    libro = "Libro"
    tesis = "Tesis"
    general = "General"
    none = "None"



@router.get("/test-integration", dependencies=[Depends(verify_bearer_token)])
async def test_integration():
    header_led = {"Authorization": f"Bearer {os.getenv('LLM_LED_TOKEN')}"}
    header_extractor = {"Authorization": f"Bearer {os.getenv('EXTRACTOR_TOKEN')}"}
    url_extractor = os.getenv("EXTRACTOR_URL")
    url_led = os.getenv("LLM_LED_URL")
    response_extractor = requests.get(url_extractor + "/test-integration", headers=header_extractor)
    response_led = requests.get(url_led + "/test-integration", headers=header_led)
    if response_extractor.status_code != 200 :
        raise HTTPException(status_code=response_extractor.status_code, detail=response_extractor.text)
    if response_led.status_code != 200 :
        raise HTTPException(status_code=response_led.status_code, detail=response_led.text)
    return {"message": "Integration tests passed"}

@router.get("/health")
async def root():
    return {"message-info": "server is up"}



@router.post('/upload' , dependencies=[Depends(verify_bearer_token)])
async def upload_file(file: UploadFile = File(...),
    normalization: Optional[bool] = Form(True),
    type: Optional[Type] = Form(Type.none)):
    if not file:
        raise HTTPException(status_code=RO_E["CODE_ERROR_NO_INPUT_DATA"], detail=RO_E["ERROR_NO_INPUT_DATA"])
    print(type)
    if type == Type.none:
        dc_type = None
    else:
        dc_type = type.value
    print(dc_type)
    orchestrator = Orchestrator()
    response,error = orchestrator.orchestrate(file=file,normalization=normalization,type=dc_type)
    if(error is not None):
        raise HTTPException(status_code=error, detail=response.get("error", "Unknown error extracting metadata"))
    return response