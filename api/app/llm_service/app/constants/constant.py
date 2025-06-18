from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[0]

BASE_MODEL_LED="allenai/led-base-16384"
BASE_MODEL_LED_LARGE="allenai/led-large-16384"
BASE_MODEL_LED_SPANISH="vgaraujov/led-base-16384-spanish"
BASE_MODEL_GEMMA="google/gemma-3-1b-pt"
BASE_MODEL_QWEN="Qwen/Qwen3-4B"
BASE_MODEL_LLAMA="meta-llama/Llama-3.2-1B"
BASE_MODEL_MISTRAL="mistralai/Mistral-7B-v0.1"
BASE_MODEL_DEEPSEK_QWEN="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
BASE_MODEL_NUEXTRACT="numind/NuExtract-tiny"
BASE_MODEL_T5="google-t5/t5-base"

MAX_TOKENS_INPUT= 2048
MAX_TOKENS_OUTPUT= 512
LOG_DIR = ROOT_DIR /  "log"
FINAL_MODEL_PATH =ROOT_DIR / "fine-tuned-model"
CHECKPOINT_MODEL_PATH = ROOT_DIR / "results"

FILETYPES = [".pdf", ".docx"]


