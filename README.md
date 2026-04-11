# UpLink – Agentic AI Student & Project Assistant

UpLink is an AI-driven personal intelligence system that transforms repository activity and digital documentation into actionable insights. Powered by agentic RAG pipelines and high-performance vector search, it understands your codebases, tracks progress, and visualizes project workflows.

## 🚀 Core Capabilities

1. **Unified Intelligence Core**: Migrated to a Google Gemini-First architecture.
   - **Dual-Model Routing**: Uses `gemini-1.5-flash` for high-throughput ingestion and `gemini-1.5-pro` for conversational reasoning.
   - **Rate Limit Resilience**: Incorporates exponential backoff and jitter across all LLM inference endpoints to support massive parallel ingestion.
2. **Parallel Source-Agnostic Engine**: 
   - Lockless architecture in `agent.py` and `server.py` enables simultaneous ingestion of multiple GitHub repositories, Jira tickets, and documents.
3. **Advanced Telemetry & Testing**: 
   - Added deep telemetry and latency tracking ([rag_pipeline_performance.py](./Test%20Scripts/rag_pipeline_performance.py)).
   - Built robust stress-testing suites to validate high-throughput loads and concurrent requests.

## 📡 Service Architecture

UpLink is built as a distributed microservice system to ensure high performance and GPU acceleration:

| Service | Port | Logic |
| :--- | :--- | :--- |
| **RAG Pipeline** | `6399` | The "Brain": Unified Gemini Intelligence and pure parallel multi-source ingestion. |
| **Embedding Server** | `6377` | AI Inference: All-MPNet-Base-v2 (CUDA/CPU). |
| **Vector DB (Qdrant)** | `6366` | Storage: Persistent Vector Database (Docker). |
| **Document Parser** | `8004` | Extractor: High-accuracy PDF (opendataloader), DOCX, CSV, TXT, MD semantic chunking. |
| **Scheduler** | `8002` | Action Layer: Orchestrates tasks, reminders, and delivery (Telegram/Calendar). |
| **Event Handler** | `8003` | Gateway: Normalizes and routes incoming events to the Scheduler. |
| **Main Server** | `8000` | Frontend Bridge: Fast API router connecting UI to RAG logic and visualizations. |

---

## 🛠️ Local Setup

The easiest way to start the complete UpLink environment (both frontend and backend services) on Windows is using the unified master launcher:

```bash
# From the project root simply run:
.\start_uplink.bat
```

**What this does automatically:**
1. **Installs Requirements**: Syncs Python dependencies via `requirements.txt` and Node dependencies via `npm install`.
2. **Starts Qdrant**: Boots the Docker-based Vector DB automatically.
3. **Bootstraps the Backend**: Launches the `Embedding Server`, `Document Parser`, `RAG Pipeline`, `Scheduler`, `Event Handler`, and `Main Server` securely.
4. **Starts the Frontend**: Spins up the React development environment.

Your console will open two background windows logic contexts. 
The Frontend responds on `http://localhost:3000` and the Backend acts on `http://127.0.0.1:8000`.

### 🧪 Verification & Maintenance
1. **Performance Benchmark**: Stress test the pipeline and verify Gemini ingestion latencies:
   ```bash
   python "Test Scripts/rag_stress_test.py"
   python "Test Scripts/rag_pipeline_performance.py"
   ```
2. **Master Verify**: Run the unified master test suites to verify pipelines (Scan -> Chat -> Viz and Document Parser):
   ```bash
   python "Test Scripts/test_rag.py"
   python "Test Scripts/test_document_parser.py"
   ```
3. **Database Maintenance**: Quickly clean stale collections in Qdrant:
   ```bash
   python "Test Scripts/clean_vdb.py"
   ```

---

## 🏗️ Project Lifecycle
Currently in **Phase 2: Agentic Integration**. The core RAG pipeline is stable, and we are moving toward deep document parsing and front-end visualization.