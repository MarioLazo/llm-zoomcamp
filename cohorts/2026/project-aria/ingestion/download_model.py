"""Download the ONNX embedding model (Xenova/all-MiniLM-L6-v2) from HuggingFace.

Same helper used in LLM Zoomcamp HW2. Run once before ingesting.
"""
import os
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download, list_repo_files

os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

ONNX_CANDIDATES = ["onnx/model.onnx", "onnx/encoder_model.onnx", "model.onnx"]


def download(repo="Xenova/all-MiniLM-L6-v2", dest="models"):
    dest = Path(dest) / repo
    dest.mkdir(parents=True, exist_ok=True)
    files = list_repo_files(repo_id=repo)
    onnx_file = next((c for c in ONNX_CANDIDATES if c in files), None)
    if not onnx_file:
        raise FileNotFoundError(f"No ONNX model found in {repo}")
    for remote, local in [("tokenizer.json", "tokenizer.json"), (onnx_file, "model.onnx")]:
        src = hf_hub_download(repo_id=repo, filename=remote)
        dst = dest / local
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"  saved {dst}")


if __name__ == "__main__":
    download()
