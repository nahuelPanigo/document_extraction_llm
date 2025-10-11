from app.service.orchestrator import Orchestrator
from app.errors.errors import ROUTE_ERRORS as RO_E
from fastapi import APIRouter,HTTPException,UploadFile,Form,File
from enum import Enum
from app.middleware.security import verify_bearer_token
from fastapi import Depends
import os
import requests
from typing import Optional
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

router = APIRouter()


class Type(str, Enum):
    articulo = "Articulo"
    libro = "Libro"
    tesis = "Tesis"
    general = "General"
    objeto_conferencia = "Objeto de conferencia"
    none = "None"



@router.get("/test-integration", dependencies=[Depends(verify_bearer_token)])
async def test_integration():
    header_led = {"Authorization": f"Bearer {os.getenv('LLM_LED_TOKEN')}"}
    header_extractor = {"Authorization": f"Bearer {os.getenv('EXTRACTOR_TOKEN')}"}
    header_deepanalyze = {"Authorization": f"Bearer {os.getenv('LLM_DEEPANALYZE_TOKEN')}"}
    url_extractor = os.getenv("EXTRACTOR_URL")
    url_led = os.getenv("LLM_LED_URL")
    url_deepanalyze = os.getenv("LLM_DEEPANALYZE_URL")
    response_extractor = requests.get(url_extractor + "/test-integration", headers=header_extractor)
    response_led = requests.get(url_led + "/test-integration", headers=header_led)
    response_deepanalyze = requests.get(url_deepanalyze + "/test-integration", headers=header_deepanalyze)
    if response_extractor.status_code != 200 :
        raise HTTPException(status_code=response_extractor.status_code, detail=response_extractor.text)
    if response_led.status_code != 200 :
        raise HTTPException(status_code=response_led.status_code, detail=response_led.text)
    if response_deepanalyze.status_code != 200 :
        raise HTTPException(status_code=response_deepanalyze.status_code, detail=response_deepanalyze.text)
    return {"message": "Integration tests passed"}

@router.get("/health")
async def root():
    return {"message-info": "server is up"}



@router.post('/upload', dependencies=[Depends(verify_bearer_token)])
async def upload_file(
    file: UploadFile = File(...),
    normalization: Optional[bool] = Form(True),
    type: Optional[Type] = Form(Type.none),
    deepanalyze: Optional[bool] = Form(False),
):
    if not file:
        return error_response(
            code=RO_E["CODE_ERROR_NO_INPUT_DATA"],
            message=RO_E["ERROR_NO_INPUT_DATA"]
        )

    dc_type = None if type == Type.none else type.value

    orchestrator = Orchestrator()
    response, error = orchestrator.orchestrate(file=file, normalization=normalization, type=dc_type, deepanalyze=deepanalyze)

    if error is not None:
        return error_response(
            code=error,
            message=response.get("error", "Unknown error extracting metadata")
        )

    return success_response(response)