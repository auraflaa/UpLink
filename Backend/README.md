# UpLink Backend Services

This directory contains the microservices and analyzers that power the UpLink intelligence system.

## 📡 Service Port Registry

To avoid conflicts during development, we have assigned the following fixed ports:

| Service | Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- |
| **Qdrant Vector DB** | `6366` | REST / HTTP | Primary API for Python requests |
| **Qdrant Vector DB** | `6334` | gRPC | High-performance internal API |
| **Embedding Server** | `6377` | REST / HTTP | Standalone REST API for `all-mpnet-base-v2` |
| **Mr. UpLinker** | `6399` | REST / HTTP | [IN PROGRESS] AI Agentic Repository Brain |

## 🚀 Recent Accomplishments

1. **AI Intelligence Core**: Fully operational.
   - **Embedding Server**: Standalone FastAPI service running on port `6377`.
   - **Vector DB**: Qdrant container running on port `6366`.
   - **Semantic Precision**: Verified accuracy of 10ms/search and 0.52+ cosine similarity for technical roles.
2. **Unified Testing**: 
   - [integration_test.py](./Test%20Scripts/integration_test.py) is now the Ground Truth for the intelligence pipeline, featuring Rich terminal formatting.

## 🏗️ Folder Overview

- `/Qdrant DB`: Docker configuration for the official Rust DB.
- `/Embedding Service`: Standalone FastAPI server for `all-mpnet-base-v2` embeddings (CUDA-first).
- `/Mr UpLinker`: The "Brain" of UpLink (formerly GitHub Analyser). Handles agentic scans.
- `/Document Parser`: Logic for analyzing resumes and project PDFs.
- `/Test Scripts`: Centralized verification scripts for all services.

## 🛠️ Global Setup

1. **Venv**: Use the shared `venv` in this folder.
   ```bash
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Execution**:
   - Start DB: `cd "Qdrant DB" && docker-compose up -d`
   - Start Embedding Server: `python "Embedding Service/server.py"`
   - Start Mr. UpLinker: `python "Mr UpLinker/server.py"`

3. **Verification**:
   - Run Core Test: `python "Test Scripts/integration_test.py"`
   - Run Full Agentic Test: `python "Test Scripts/mr_uplinker_verify.py"`
