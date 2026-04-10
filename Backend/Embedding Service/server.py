import os
import torch
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uvicorn

# --- 1. CONFIGURATION ---
MODEL_NAME = 'all-mpnet-base-v2'
PORT = int(os.getenv("EMBEDDING_PORT", 6377))
HOST = "0.0.0.0"

# --- 2. INITIALIZATION ---
print(f"[*] Starting Embedding Server on port {PORT}...")

# Determine Device (CUDA first, CPU fallback)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
if device == 'cuda':
    print(f"[*] CUDA detected! Using GPU for embeddings.")
else:
    print(f"[*] CUDA not found. Falling back to CPU.")

# Load Model once on startup
print(f"[*] Loading model '{MODEL_NAME}' on {device}...")
model = SentenceTransformer(MODEL_NAME, device=device)
print(f"[*] Model loaded successfully. Service ready.")

# --- 3. API SERVER ---
app = FastAPI(title="UpLink Embedding Service")

class EmbeddingRequest(BaseModel):
    texts: List[str]

@app.get("/health")
def health_check():
    return {"status": "healthy", "device": device, "model": MODEL_NAME}

@app.post("/embed")
def generate_embeddings(request: EmbeddingRequest):
    """
    Takes a list of strings and returns their 768-dim embeddings.
    """
    if not request.texts:
        raise HTTPException(status_code=400, detail="No texts provided")
    
    try:
        # Generate embeddings
        embeddings = model.encode(request.texts, convert_to_tensor=True)
        
        # Convert to list for JSON response
        return {
            "embeddings": embeddings.cpu().tolist(),
            "dimensions": 768
        }
    except Exception as e:
        print(f"[!] Error during embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
