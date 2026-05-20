from __future__ import annotations


import argparse
import hashlib
import os
from pathlib import Path


from dotenv import load_dotenv
from huggingface_hub import snapshot_download




REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCAL_MODEL = REPO_ROOT / "api/app/llm_service/app/models/fine-tuned-model-led"
DEFAULT_DOWNLOAD_DIR = REPO_ROOT / "_hf_compare/fine-tuned-model-led"
DEFAULT_REPO_ID = "Nahpanigo99/fine-tuned-model-led"
IGNORED_DIRS = {".git", ".cache"}




def load_hf_token() -> str | None:
    env_paths = [
        REPO_ROOT / ".env",
        REPO_ROOT / "fine_tunning/.env",
        REPO_ROOT / "api/app/.env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)
    return os.getenv("TOKEN_HUGGING_FACE") or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")




def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()




def model_files(root: Path) -> dict[str, Path]:
    files = {}
    for path in root.rglob("*"):
        if path.is_file() and not any(part in IGNORED_DIRS for part in path.parts):
            files[path.relative_to(root).as_posix()] = path
    return files




def compare_dirs(local_dir: Path, hf_dir: Path) -> bool:
    local_files = model_files(local_dir)
    hf_files = model_files(hf_dir)
    all_names = sorted(set(local_files) | set(hf_files))


    identical = True
    for name in all_names:
        if name not in local_files:
            print(f"ONLY HF:    {name}")
            identical = False
            continue
        if name not in hf_files:
            print(f"ONLY LOCAL: {name}")
            identical = False
            continue
        if sha256(local_files[name]) != sha256(hf_files[name]):
            print(f"DIFF:       {name}")
            identical = False


    if identical:
        print("OK: local model and Hugging Face snapshot are identical file by file.")
    else:
        print("Differences found.")
    return identical




def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a Hugging Face model snapshot and compare it against a local model directory."
    )
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID, help="Hugging Face model repo id.")
    parser.add_argument("--local-dir", type=Path, default=DEFAULT_LOCAL_MODEL, help="Local model directory to compare.")
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=DEFAULT_DOWNLOAD_DIR,
        help="Directory where the Hugging Face snapshot will be downloaded.",
    )
    parser.add_argument("--skip-download", action="store_true", help="Compare using an already downloaded snapshot.")
    return parser.parse_args()




def main() -> int:
    args = parse_args()
    token = load_hf_token()


    local_dir = args.local_dir.resolve()
    download_dir = args.download_dir.resolve()


    if not local_dir.exists():
        print(f"ERROR: local model directory does not exist: {local_dir}")
        return 2


    if not args.skip_download:
        print(f"Downloading {args.repo_id} to {download_dir}...")
        snapshot_download(
            repo_id=args.repo_id,
            local_dir=download_dir,
            token=token,
            local_dir_use_symlinks=False,
        )


    if not download_dir.exists():
        print(f"ERROR: Hugging Face snapshot directory does not exist: {download_dir}")
        return 2


    print(f"Comparing local: {local_dir}")
    print(f"Against HF:      {download_dir}")
    return 0 if compare_dirs(local_dir, download_dir) else 1




if __name__ == "__main__":
    raise SystemExit(main())



