from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import os
from run_metrics import run_metric_comparison


app = FastAPI()


API_URL = "192.168.100.5"

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    f"http://{API_URL}:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.options("/api/metrics")
async def options_metrics():
    return JSONResponse(content={"message": "OK"})

@app.post("/api/metrics")
async def get_metrics_endpoint(original_file: UploadFile = File(...), predicted_file: UploadFile = File(...)):
    try:
        original_content = await original_file.read()
        predicted_content = await predicted_file.read()
        metrics = run_metric_comparison(original_content, predicted_content)
        return JSONResponse(content=jsonable_encoder(metrics))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
