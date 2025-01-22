
from .utils.extraction.text_extraction import get_text
from .utils.model_manipulation.llms_extraction import model_extraction
from .errors import ROUTE_ERRORS as RO_E
from fastapi import APIRouter,HTTPException,UploadFile

router = APIRouter()


@router.get("/")
async def root():
    return {"message-info": "server is up"}



@router.post('/upload')
async def upload_file(file: UploadFile):
    if not file:
        raise HTTPException(status_code=RO_E["CODE_ERROR_NO_INPUT_DATA"], detail=RO_E["ERROR_NO_INPUT_DATA"])
    response_extraction,error = get_text(file)
    if(error is not None):
        raise HTTPException(status_code=error, detail=response_extraction.get("error", "Unknown error during text extraction"))
    response_ml,error = model_extraction(response_extraction["text"])
    print(response_ml)
    if (error is not None):
         raise HTTPException(status_code=error, detail=response_ml.get("error", "Unknown error during model extraction"))
    return response_ml