"""ONNX embedder — all-MiniLM-L6-v2 (reused from LLM Zoomcamp HW2).

Lightweight: no PyTorch, no CUDA. Produces normalized 384-dim vectors so the
dot product between two vectors equals their cosine similarity.
"""
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer


# all-MiniLM-L6-v2 was trained with a 512-token position limit; chunks up to
# CHUNK_SIZE=2000 chars can exceed that, so truncation must be explicit —
# without it, over-length inputs risk an ONNX position-embedding error.
MAX_SEQ_LEN = 512


class Embedder:
    def __init__(self, path="models/Xenova/all-MiniLM-L6-v2"):
        path = Path(path)
        self.tokenizer = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=MAX_SEQ_LEN)
        self.session = ort.InferenceSession(
            str(path / "model.onnx"), providers=["CPUExecutionProvider"]
        )
        self.input_names = {inp.name for inp in self.session.get_inputs()}

    def encode(self, text, normalize=True):
        return self.encode_batch([text], normalize=normalize)[0]

    def encode_batch(self, texts, normalize=True):
        self.tokenizer.enable_padding()
        encoded = self.tokenizer.encode_batch(texts)
        feed = {}
        if "input_ids" in self.input_names:
            feed["input_ids"] = np.array([e.ids for e in encoded], dtype=np.int64)
        if "attention_mask" in self.input_names:
            feed["attention_mask"] = np.array(
                [e.attention_mask for e in encoded], dtype=np.int64
            )
        if "token_type_ids" in self.input_names:
            feed["token_type_ids"] = np.array(
                [e.type_ids for e in encoded], dtype=np.int64
            )
        hidden = self.session.run(None, feed)[0]
        mask = feed["attention_mask"][..., None]
        pooled = (hidden * mask).sum(axis=1) / mask.sum(axis=1)
        if normalize:
            pooled = pooled / np.linalg.norm(pooled, axis=1, keepdims=True)
        return pooled.astype(np.float32)
