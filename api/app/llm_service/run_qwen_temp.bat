set IS_LOCAL_MODEL=True
set IS_OLLAMA_MODEL=True
set SERVICE_TOKEN=ls56as5613as81386qefq84q31sa6q1d5fq48q31s5qawdq86q1da13q84
set MODEL_SELECTED=qwen3:8b
set OLLAMA_HOST_URL=http://localhost:11434
uvicorn app.main:app --port 8003 --reload
