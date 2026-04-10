# UpLink API Reference Guide

This document serves as the master contract for the UpLink Backend. It details the exact functionality, acceptable input payloads, constraints, and standard output formats for every microservice currently active in the cluster.

---

## 1. RAG Intelligence Core (`Port 6399`)
The central orchestrator for repository analysis, Jira ingestion, and semantic retrieval via Gemini 1.5.

### 1a. `POST /analyze`
**Functionality**: Triggers an asynchronous ingestion of a single software source (GitHub repository or Jira ticket).
**Input Format** (JSON):
```json
{
  "source_url": "https://github.com/facebook/react",
  "source_type": "github",
  "collection_name": "project_knowledge"
}
```
* **Possibilities**: `source_type` can be `"github"` or `"jira"`.
* **Restrictions**: 
  * Strict `HTTP 409 Conflict` lock enforced if another source of the **same type** is currently being analyzed. 
  * Links are validated. Jira links *must* contain `.atlassian.net`. GitHub links *must* match the standard github.com structure.
* **Output Format** (`HTTP 200`):
```json
{
  "status": "accepted",
  "message": "Analysis started for https://github.com/facebook/react (github).",
  "collection": "project_knowledge"
}
```

### 1b. `POST /analyze/dual`
**Functionality**: A high-throughput dual orchestrator that maps an ingestion of both a Jira ticket and a GitHub repo perfectly in parallel. Bypasses old mutual-exclusion locks.
**Input Format** (JSON):
```json
{
  "github_url": "https://github.com/facebook/react",
  "jira_url": "https://test.atlassian.net/browse/TKT-123",
  "collection_name": "project_knowledge"
}
```
* **Possibilities**: Can accept one or both parameters. Missing parameter gracefully omits that specific pipeline.
* **Restrictions**: At least one URL must be provided. Standard validation rules apply.
* **Output Format** (`HTTP 200`): List of triggered services.

### 1c. `POST /chat`
**Functionality**: Queries the Qdrant Vector database and parses the retrieved context using Gemini for conversational flow.
**Input Format** (JSON):
```json
{
  "query": "Who is the lead engineer?",
  "user_id": "uuid-1234",
  "session_id": "default",
  "collection_name": "project_knowledge"
}
```
* **Possibilities**: Maintains conversational session history based on `user_id` and `session_id`.
* **Restrictions**: `user_id` is absolutely mandatory (FastAPI returns `422 Unprocessable Entity` without it).
* **Output Format** (`HTTP 200`):
```json
{
  "response": "The lead engineer is Dr. Aris Thorne.",
  "telemetry": {
     "qdrant_search_ms": 35.1,
     "gemini_inference_ms": 4200.5
  }
}
```

### 1d. `GET /status`
**Functionality**: Deep scans the Vector database to check if a specific codebase/ticket has been fully embedded and indexed.
**Input Format**: Requires Query Parameters.
*`GET /status?source_url=https://github.com/facebook/react&collection_name=project_knowledge`*
* **Restrictions**: If `source_url` is omitted, throws `HTTP 400 Bad Request`.
* **Output Format** (`HTTP 200`):
```json
{
  "source_url": "https://github.com/facebook/react",
  "indexed": true,
  "collection": "project_knowledge",
  "telemetry": {}
}
```

---

## 2. Document Parser (`Port 8004`)
An autonomous offshoot service handling raw document layouts, extracting their text, semantic chunking, and embedding directly into Qdrant.

### 2a. `POST /ingest`
**Functionality**: Extracts text from raw files, groups text natively alongside Markdown headers via a custom parser, splits them into 800-character chunks with a 200-character rolling overlap, and upserts them.
**Input Format** (Multipart Form Data):
* `files`: Native standard file blob wrapper.
* `collection_name` (string): The Qdrant namespace target.
* `source_label` (string): Metadata tag.
* **Possibilities**: Accepts batches of files simultaneously.
* **Restrictions**: Strictly limited to `[pdf, docx, txt, md, csv]`. Uses Java (`opendataloader-pdf`) for precision PDF layout extraction. Falls back to vanilla `pypdf` if Java is broken.
* **Output Format** (`HTTP 200`):
```json
{
  "status": "success",
  "total_chunks_stored": 45,
  "results": [
    {"filename": "report.pdf", "chunks": 45}
  ]
}
```

### 2b. `GET /status`
**Functionality**: System liveness check for testing scripts. No input required. Output is a static JSON liveness ping.

---

## 3. Embedding Vector Service (`Port 6377`)
The internal ML router. Acts as a unified PyTorch hardware gateway so that both the RAG Pipeline and Document Parser aren't trying to load identical, heavy VRAM Transformers into memory at the exact same time.

### 3a. `POST /embed`
**Functionality**: Converts human-readable text batches into mathematically aligned high-dimension vectors (arrays) using `all-MiniLM-L6-v2`.
**Input Format** (JSON):
```json
{
  "texts": ["Sentence 1", "Sentence 2"]
}
```
* **Possibilities**: Scales effectively via batch tensors.
* **Restrictions**: Strictly an internal service route. Not meant to be exposed or called by frontend applications due to lacking input validation bounds.
* **Output Format** (`HTTP 200`): Length-matched multidimensional arrays representing mapped vector traits.

---

## 4. Qdrant Document Store (`Port 6366`)
The core database running isolated via Docker.
**Input/Output**: Interacted with strictly via internal python GRPC/HTTP clients. Data is structured cleanly within namespaced `collections`. 
* **Restrictions**: Wipes dynamically if container volumes are dropped. Stores localized files exclusively in `./qdrant_storage`.

---

## 5. Background Dependencies & Network Rules
* **Retry Exponential Backoff**: The system expects API volatility from Gemini due to Free-Tier Rate limits. The backend seamlessly catches `429 RESOURCE EXHAUSTED` responses, adds random Jitter, and exponentially backs off (`2^x`). Therefore, background workers may occasionally take `20-45` seconds longer to finish analysis.
* **Lockless Async Environment**: There are no database mutexes blocking simultaneous calls, meaning multiple files or repositories can be shot at the backend endpoints at exact same time with zero failure logic.
