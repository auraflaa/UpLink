"""
server.py — UpLink Document Parser Service
Port: 8004

Endpoints:
  POST /ingest   — Upload files, parse, chunk, embed, store in Qdrant
  GET  /status   — Health check + capability report
"""

from __future__ import annotations

import datetime
import os
import sys
import uuid
from typing import List, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# ── Service discovery (matches RAG Pipeline conventions) ────────────────────
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://127.0.0.1:6377/embed")
QDRANT_URL    = os.getenv("QDRANT_URL",    "http://127.0.0.1:6366")
PORT          = int(os.getenv("DOC_PARSER_PORT", "8004"))

# ── Supported file types ─────────────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv"}

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="UpLink Document Parser",
    description="Ingests PDF/DOCX/TXT/MD/CSV files into Qdrant via embeddings.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Lazy parser import (avoids slow JVM init at import time) ─────────────────
_parser_module = None

def _get_parser():
    global _parser_module
    if _parser_module is None:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import parser as p
        _parser_module = p
    return _parser_module


# ── Core: embed + upsert to Qdrant (mirrors agent._index_summaries) ──────────

def _ensure_collection(collection_name: str):
    """Create Qdrant collection if it doesn't already exist."""
    requests.put(f"{QDRANT_URL}/collections/{collection_name}", json={
        "vectors": {"size": 768, "distance": "Cosine"}
    })  # Qdrant returns 200 if already exists, so no raise needed


def _embed_chunks_and_upsert(chunks: List[str], collection_name: str, metadata: dict) -> int:
    """
    Embeds a batch of text chunks via the Embedding Service,
    then upserts the resulting vectors into Qdrant.
    Returns the number of successfully stored chunks.
    """
    if not chunks:
        return 0

    # 1. Get embeddings
    try:
        embed_res = requests.post(EMBEDDING_URL, json={"texts": chunks}, timeout=30)
        embed_res.raise_for_status()
        vectors = embed_res.json().get("embeddings", [])
    except Exception as e:
        print(f"[!] Embedding Service error: {e}")
        return 0

    if len(vectors) != len(chunks):
        print(f"[!] Embedding count mismatch: got {len(vectors)}, expected {len(chunks)}")
        return 0

    # 2. Build Qdrant points
    points = []
    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        points.append({
            "id": str(uuid.uuid4()),
            "vector": vec,
            "payload": {
                **metadata,
                "text": chunk,
                "chunk_index": i,
                "chunk_total": len(chunks),
            }
        })

    # 3. Upsert
    try:
        _ensure_collection(collection_name)
        upsert_res = requests.put(
            f"{QDRANT_URL}/collections/{collection_name}/points",
            json={"points": points},
            timeout=30
        )
        upsert_res.raise_for_status()
        return len(points)
    except Exception as e:
        print(f"[!] Qdrant upsert error: {e}")
        return 0


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/status")
def get_status():
    """Returns service health and capability report."""
    parser = _get_parser()
    embedding_online = False
    qdrant_online = False

    try:
        r = requests.get(EMBEDDING_URL.replace("/embed", "/health"), timeout=2)
        embedding_online = r.status_code == 200
    except Exception:
        pass

    try:
        r = requests.get(f"{QDRANT_URL}/healthz", timeout=2)
        qdrant_online = r.status_code == 200
    except Exception:
        pass

    return {
        "status": "ok",
        "service": "Document Parser",
        "port": PORT,
        "capabilities": {
            "pdf_opendataloader": parser.OPENDATALOADER_AVAILABLE,
            "pdf_pypdf_fallback": parser.PYPDF_AVAILABLE,
            "docx": parser.DOCX_AVAILABLE,
            "csv_pandas": parser.PANDAS_AVAILABLE,
            "txt_md": True,
            "supported_types": sorted(SUPPORTED_EXTENSIONS),
        },
        "dependencies": {
            "embedding_service": embedding_online,
            "qdrant": qdrant_online,
        }
    }


@app.get("/health")
def get_health():
    """Compatibility health alias for service probes expecting /health."""
    return get_status()


@app.post("/ingest")
async def ingest_documents(
    files: List[UploadFile] = File(...),
    collection_name: str = Form(...),
    source_label: Optional[str] = Form(None),
):
    """
    Upload one or more documents. Each is parsed, chunked, and embedded into Qdrant.

    - **files**: One or more files (PDF, DOCX, TXT, MD, CSV)
    - **collection_name**: Target Qdrant collection
    - **source_label**: Optional tag for all vectors (e.g. "project_spec")
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")
    if not collection_name or not collection_name.strip():
        raise HTTPException(status_code=400, detail="collection_name is required.")

    # Validate all types upfront
    for f in files:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}' in '{f.filename}'. "
                       f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

    parser = _get_parser()
    results = {}
    errors = []
    total_stored = 0

    for upload in files:
        filename = upload.filename
        try:
            content = await upload.read()

            # 1. Parse → chunks
            chunks = parser.parse_file(filename, content)
            if not chunks:
                errors.append(f"{filename}: Parser returned no content.")
                results[filename] = {"chunks_parsed": 0, "chunks_stored": 0, "status": "empty"}
                continue

            # 2. Embed + upsert
            metadata = {
                "filename": filename,
                "source_type": "document",
                "source_label": source_label or collection_name,
                "collection": collection_name,
                "ingested_at": datetime.datetime.utcnow().isoformat(),
            }
            stored = _embed_chunks_and_upsert(chunks, collection_name, metadata)
            total_stored += stored

            status = "ok" if stored == len(chunks) else ("partial" if stored > 0 else "failed")
            results[filename] = {
                "chunks_parsed": len(chunks),
                "chunks_stored": stored,
                "status": status,
            }
            print(f"[OK] {filename}: {stored}/{len(chunks)} chunks stored in '{collection_name}'")

        except ValueError as e:
            errors.append(f"{filename}: {e}")
            results[filename] = {"chunks_parsed": 0, "chunks_stored": 0, "status": "unsupported"}
        except Exception as e:
            errors.append(f"{filename}: {e}")
            results[filename] = {"chunks_parsed": 0, "chunks_stored": 0, "status": "error"}
            print(f"[!] Error processing {filename}: {e}")

    overall = "completed"
    if errors and total_stored == 0:
        overall = "failed"
    elif errors:
        overall = "partial"

    return {
        "status": overall,
        "collection": collection_name,
        "total_chunks_stored": total_stored,
        "results": results,
        "errors": errors,
    }


# ── Startup ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print("[*] UpLink Document Parser starting...")
    print(f"[*] Embedding Service: {EMBEDDING_URL}")
    print(f"[*] Qdrant:            {QDRANT_URL}")

    import importlib.util
    if importlib.util.find_spec("opendataloader_pdf"):
        print("[*] PDF Engine: opendataloader-pdf (Java-accelerated, #1 benchmark)")
    elif importlib.util.find_spec("pypdf"):
        print("[!] PDF Engine: pypdf fallback (limited accuracy)")
    else:
        print("[!] WARNING: No PDF parser available. PDF uploads will fail.")

    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=False)
