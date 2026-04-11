import hashlib
import os
import re
from typing import List

import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# --- 1. CONFIGURATION ---
MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-mpnet-base-v2")
PORT = int(os.getenv("EMBEDDING_PORT", 6377))
HOST = "0.0.0.0"
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", 768))
ALLOW_HASH_FALLBACK = os.getenv("EMBEDDING_ALLOW_HASH_FALLBACK", "true").lower() != "false"
LOCAL_ONLY = os.getenv("EMBEDDING_LOCAL_ONLY", "false").lower() == "true"
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")

# --- 2. INITIALIZATION ---
print(f"[*] Starting Embedding Server on port {PORT}...")

device = "cuda" if torch.cuda.is_available() else "cpu"
if device == "cuda":
    print("[*] CUDA detected! Using GPU for embeddings.")
else:
    print("[*] CUDA not found. Falling back to CPU.")

model = None
embedding_backend = "transformer"
startup_warning = None

print(f"[*] Loading model '{MODEL_NAME}' on {device}...")
try:
    model = SentenceTransformer(MODEL_NAME, device=device, local_files_only=LOCAL_ONLY)
    detected_dimensions = model.get_sentence_embedding_dimension()
    if detected_dimensions:
        EMBEDDING_DIMENSIONS = int(detected_dimensions)
    print(f"[*] Model loaded successfully. Service ready with {EMBEDDING_DIMENSIONS} dimensions.")
except Exception as exc:
    startup_warning = str(exc)
    if not ALLOW_HASH_FALLBACK:
        raise

    embedding_backend = "hash-fallback"
    print(f"[!] Model load failed: {exc}")
    print("[*] Falling back to deterministic offline embeddings.")
    print(f"[*] Fallback embedding dimensionality: {EMBEDDING_DIMENSIONS}")


def _tokenize(text: str) -> List[str]:
    normalized = (text or "").strip().lower()
    tokens = TOKEN_PATTERN.findall(normalized)
    if tokens:
        return tokens
    return [normalized or "<empty>"]


def _hash_embed_text(text: str) -> List[float]:
    vector = np.zeros(EMBEDDING_DIMENSIONS, dtype=np.float32)

    for token in _tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for offset in range(0, 24, 4):
            index = int.from_bytes(digest[offset:offset + 2], "big") % EMBEDDING_DIMENSIONS
            magnitude = 0.5 + (digest[offset + 2] / 255.0)
            sign = 1.0 if digest[offset + 3] % 2 == 0 else -1.0
            vector[index] += sign * magnitude

    norm = np.linalg.norm(vector)
    if norm == 0.0:
        vector[0] = 1.0
    else:
        vector /= norm

    return vector.tolist()


def _generate_embeddings(texts: List[str]) -> List[List[float]]:
    if model is not None:
        embeddings = model.encode(texts, convert_to_tensor=True)
        return embeddings.cpu().tolist()

    return [_hash_embed_text(text) for text in texts]


# --- 3. API SERVER ---
app = FastAPI(title="UpLink Embedding Service")


class EmbeddingRequest(BaseModel):
    texts: List[str]


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "device": device,
        "model": MODEL_NAME,
        "dimensions": EMBEDDING_DIMENSIONS,
        "backend": embedding_backend,
        "warning": startup_warning,
    }


@app.post("/embed")
def generate_embeddings(request: EmbeddingRequest):
    """
    Takes a list of strings and returns embeddings in the configured dimension.
    """
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")

    try:
        return {
            "embeddings": _generate_embeddings(request.texts),
            "dimensions": EMBEDDING_DIMENSIONS,
            "backend": embedding_backend,
        }
    except Exception as exc:
        print(f"[!] Error during embedding: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
