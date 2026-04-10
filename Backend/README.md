# UpLink Backend Services

This directory contains the microservices and analyzers that power the UpLink intelligence system.

## 📡 Service Port Registry

To avoid conflicts during development, we have assigned the following fixed ports:

| Service | Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- |
| **Qdrant Vector DB** | `6366` | REST / HTTP | Primary API for Python requests |
| **Qdrant Vector DB** | `6334` | gRPC | High-performance internal API |
| **Embedding Server** | `6377` | REST / HTTP | [IN PROGRESS] |

## 🏗️ Folder Overview

- `/Qdrant DB`: Contains the Docker configuration for the official Rust DB.
- `/Embedding Service`: Standalone FastAPI server for `all-mpnet-base-v2` embeddings (CUDA-first).
- `/GitHub Analyser`: Logic for fetching and processing repository data.
- `/Document Parser`: Logic for analyzing resumes and project PDFs.
- `/Test Scripts`: Centralized verification scripts for all services.

## 🛠️ Global Setup

1. **Venv**: Use the shared `venv` in this folder.
   ```bash
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Environment Variables**:
   - `QDRANT_HOST`: Default `localhost`
   - `QDRANT_PORT`: Default `6366`
   - `EMBEDDING_PORT`: Default `6377`
