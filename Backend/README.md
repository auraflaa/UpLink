# UpLink Backend Services — Technical Documentation

This directory contains the microservices and analyzers that power the UpLink intelligence system. The backend architecture is designed as a **highly concurrent, asynchronous microservice framework** optimized for pure parallel data ingestion and AI inference scaling.

## 📡 Service Port Registry & Topology

To ensure smooth IPC (Inter-Process Communication) and zero-conflict scaling, the routing topology relies on fixed-port assignments:

| Service | Port | Protocol | Technical Purpose & Utility Goal |
| :--- | :--- | :--- | :--- |
| **Qdrant Vector DB** | `6366` | REST / gRPC | **Storage Layer**: Open-source Rust-based vector database. Acts as the final data target for all vectorized knowledge. |
| **Embedding Server** | `6377` | REST / HTTP | **Inference Layer**: Standalone FastAPI server for `all-mpnet-base-v2`. Provides raw vectorization (CUDA-first). Offloads matrix multiplication from API servers to ensure pipeline stability. |
| **RAG Pipeline** | `6399` | REST / HTTP | **Intelligence Core**: Unified Gemini Intelligence. Executes lockless parallel ingestion algorithms. Translates raw multi-source data (GitHub trees, Jira tickets) into context-aware vector payload. |
| **Document Parser** | `8004` | REST / HTTP | **Extraction Gateway**: High-accuracy file parsing (PDF, DOCX, CSV, txt). Implements semantic chunking schemas before offloading data to the Embedding Server. |
| **Scheduler** | `8002` | REST / HTTP | **Action Orchestration layer**: Task dispatch mechanism (CRON-style and event-driven). Connects data insights to external APIs (Telegram, Google Calendar). |
| **Event Handler** | `8003` | REST / HTTP | **Normalization Gateway**: Funnel for third-party inbound Webhook traffic. Standardizes event payloads and routes them internally. |

---

## 🚀 Advanced Core Architecture

The backend has undergone a significant modernization phase to achieve enterprise-grade scale and fault-tolerance:

### 1. Pure Parallel Ingestion (Lockless Architecture)
- **Utility Goal**: Eliminate API bottlenecks and maximize hardware I/O when processing large numbers of knowledge sources simultaneously.
- **Functionality**: The `agent.py` ingestion engine has been stripped of all `threading.Lock` mechanisms. It runs a purely stateless `/analyze/dual` endpoint utilizing FastAPI `BackgroundTasks`. The system seamlessly handles throughput bursts of 20+ concurrent ingestion queries. 409 Conflict logic was entirely removed in favor of frontend restraint checks, enabling unlimited back-to-back POST payloads in the core API.

### 2. LLM Inference Resiliency (Exponential Backoff & Jitter)
- **Utility Goal**: Prevent data loss when LLM APIs restrict request flows (RPM capping) during parallel batch processing.
- **Functionality**: Re-engineered `llm_client.py` and wrapped the Google Gemini generation loops with robust `429 (Resource Exhausted)` catch blocks. Introduces an exponential backoff scaling delay (`2^attempt + random(0, 1)`) up to 5 retries. This "jitter" prevents the thundering herd problem, drastically lowering ingestion failures during sustained high-concurrency API floods.

### 3. Document Extraction & Semantic Chunking (`Document Parser`)
- **Utility Goal**: Ingest static human-written files and prepare them for semantic RAG vector querying alongside codebase intelligence.
- **Functionality**: A new Fast API service on port `8004` executing:
   - **`opendataloader-pdf` runtime**: Invokes a Java-accelerated layout analyzer capable of achieving 0.907+ precision and preserving document reading structure, tables, and borders (with `pypdf` fallback capabilities).
   - **Semantic Splitting Algorithms**: Utilizes Markdown heading boundaries (`#`, `##`) to bind paragraphs, falling back to an 800-token sliding window with an 80-token overlap if chunk size exceeds safety bounds.

---

## 🔗 RAG Pipeline API Reference (Port 6399)

The center of intelligence operations. Coordinates knowledge gathering.

### 📥 High-Throughput Ingestion
- **`POST /analyze/dual`**
  - **Payload**: `{"github_url": "<URL>", "jira_url": "<URL>", "collection_name": "<NAMESPACE>"}`
  - **Functionality**: Immediately returns `200 OK` and forks processing into parallel BackgroundWorkers. Generates AST file maps for GitHub, fetches Jira sub-tasks, queries the Gemini LLM for dense summarizations, hits the `Embedding Server (6377)`, and injects memory into `Qdrant (6366)`.
- **`GET /status`**
  - Polling target to check Background Worker readiness and server load health.

### 🧠 Semantic Retrieval & Generation
- **`POST /chat`**
  - **Payload**: `{"query": "User context", "collection_name": "<NAMESPACE>"}`
  - **Functionality**: Computes vector similarity of the query, retrieves K-closest contexts from the Qdrant DB, builds a tightly structured prompt, and invokes the `gemini-1.5-pro` model to formulate an accurate, localized response using solely the retrieved context constraints.

---

## 🔗 Document Parser API Reference (Port 8004)

### 📥 Multi-file Document Ingestion
- **`POST /ingest`**
  - **Payload**: `multipart/form-data` with `files[]` boundaries. Accommodates `collection_name`.
  - **Functionality**: Validates file types (`.pdf`, `.docx`, `.csv`, `.md`, `.txt`). Processes and chunks all accepted documents iteratively. Proxies directly to the `Embedding Service` and forces Vector push into `Qdrant` locally. Yields a highly organized dict reporting processing chunks and status codes per file upload.

---

## 🧪 Global Setup & System Verification

The repository adopts a strict centralized testing protocol to ensure microservices behave reliably under load.

1. **Venv Deployment**: Use the shared `venv` in this `/Backend/` root.
   ```powershell
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Infrastructure Rollout**:
   ```powershell
   # Start Vector Storage
   cd "Qdrant DB" && docker-compose up -d

   # Spin up Python Macro-Services
   python "Embedding Service/server.py"
   python "Document Parser/server.py"
   python "RAG Pipeline/server.py"
   ```

3. **Master Verification Framework**:
   Detailed QA testing must be invoked when editing architecture routing rules. Located within `Test Scripts/`:
   - `test_rag.py`: Verifies the RAG 200 Acceptance pathways, checks parallel response times, and validates DB chat query vectors.
   - `rag_stress_test.py`: Triggers massive ThreadPool bursts, logging request/sec capacity, HTTP Timeouts, and latency percentile distributions (p95).
   - `test_document_parser.py`: Asserts semantic chunks limits, forces invalid mimetype rejection, and tracks correct API response schemas.
