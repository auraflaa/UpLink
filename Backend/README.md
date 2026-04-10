# UpLink Backend Services

This directory contains the microservices and analyzers that power the UpLink intelligence system.

## 📡 Service Port Registry

To avoid conflicts during development, we have assigned the following fixed ports:

| Service | Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- |
| **Qdrant Vector DB** | `6366` | REST / HTTP | Primary API for Python requests |
| **Embedding Server** | `6377` | REST / HTTP | Standalone REST API for `all-mpnet-base-v2` |
| **RAG Pipeline** | `6399` | REST / HTTP | **Agentic Intelligence Core** (Unified Gemini) |
| **Scheduler** | `8002` | REST / HTTP | Task & Reminder Orchestration |
| **Event Handler** | `8003` | REST / HTTP | Event Normalization Gateway |

## 🚀 Recent Core Architecture Accomplishments

1. **Unified Intelligence Hub (`llm_client.py`)**: 
   - Consolidated all AI provider logic (Gemini & Groq) into a single, polymorphic client.
   - Implemented dual-model architecture: **Gemini 1.5 Flash/Pro** for reasoning-heavy tasks and **Llama 3 (via Groq)** for high-throughput stream processing.
2. **Source-Agnostic Engine**:
   - Upgraded the RAG pipeline to handle generic `source_url` and `source_type` schemas.
   - Fully prepared for future **JIRA/Confluence** data source integrations.
3. **Advanced Telemetry & Maintenance**:
   - **`rag_pipeline_performance.py`**: Real-time audit of ingestion bottlenecks and search latencies.
   - **`clean_vdb.py`**: Easy-to-use utility for wiping stale vector collections.

## 🏗️ Folder Overview

- `/Qdrant DB`: Docker configuration for the official Rust DB.
- `/Embedding Service`: Standalone FastAPI server for `all-mpnet-base-v2` embeddings (CUDA-first).
- `/RAG Pipeline`: The "Brain" of UpLink. Handles unified Gemini orchestration and knowledge management.
- `/Document Parser`: Logic for analyzing resumes and project PDFs.
- `/Test Scripts`: Centralized verification scripts for all services.

## 🔗 Integration Endpoints (Port 8002)

The **Scheduler** acts as the gateway for all external actions and notifications.

### 📬 Telegram Bot
- **`POST /telegram/link-token`**: Generates a secure token to link a `user_id` to a Telegram chat.
- **`POST /telegram/update`**: The primary **Webhook** for the Telegram bot to receive commands (e.g., `/start`).
- **`GET /telegram/links/{user_id}`**: Check existing Telegram link status.

### 📅 Google Calendar
- **`POST /schedule`**: Include `"calendar"` in the `channels` list to automatically sync the task/event to Google Calendar.
- **Auth**: Managed internally via `calendar_credentials.json`.

### 🎫 Jira Integration
- **`POST /jira/issues`**: Create high-priority Jira issues directly from the pipeline.
- **`GET /jira/analyze-link?url=<JIRA_URL>`**: Inspect a Jira link and return a structured RAG document.

---

## 🛠️ Global Setup

1. **Venv**: Use the shared `venv` in this folder.
   ```bash
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Execution Flow**:
   - Start DB: `cd "Qdrant DB" && docker-compose up -d`
   - Start Embedding Server: `python "Embedding Service/server.py"`
   - Start RAG Pipeline: `python "RAG Pipeline/server.py"`
   - Start Scheduler: `python "Scheduler/scheduler.py"`
   - Start Event Handler: `python "Event Handler/event.py"`

3. **Maintenance**:
   - Clean stale indices: `python "Test Scripts/clean_vdb.py"`
   - Benchmark performance: `python "Test Scripts/rag_pipeline_performance.py"`
