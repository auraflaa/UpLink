# UpLink – Agentic AI Student & Project Assistant

UpLink is an AI-driven personal intelligence system that transforms repository activity and digital documentation into actionable insights. Powered by agentic RAG pipelines and high-performance vector search, it understands your codebases, tracks progress, and visualizes project workflows.

## 🚀 Core Capabilities

1. **Unified Intelligence Core**: Migrated to a Google Gemini-First architecture.
   - **Dual-Model Routing**: Uses `gemini-1.5-flash` for high-throughput ingestion and `gemini-1.5-pro` for conversational reasoning.
   - **Unified Client**: Consolidated logic into `llm_client.py` for easier provider swapping.
2. **Source-Agnostic Engine**: 
   - Refactored `agent.py` and `server.py` to move beyond GitHub-only logic.
   - Prepared architecture for **JIRA integration**.
3. **Performance & Audit**: 
   - Added [rag_pipeline_performance.py](./Test%20Scripts/rag_pipeline_performance.py) for deep telemetry and latency tracking.

## 📡 Service Architecture

UpLink is built as a distributed microservice system to ensure high performance and GPU acceleration:

| Service | Port | Logic |
| :--- | :--- | :--- |
| **RAG Pipeline** | `6399` | The "Brain": Unified Gemini Intelligence (Flash + Pro) and source-agnostic analysis. |
| **Embedding Server** | `6377` | AI Inference: All-MPNet-Base-v2 (CUDA/CPU). |
| **Vector DB (Qdrant)** | `6366` | Storage: Persistent Vector Database (Docker). |
| **Scheduler** | `8002` | Action Layer: Orchestrates tasks, reminders, and delivery (Telegram/Calendar). |
| **Event Handler** | `8003` | Gateway: Normalizes and routes incoming events to the Scheduler. |
| **Scheduler** | `8002` | Action Layer: Orchestrates tasks, reminders, and delivery (Telegram/Calendar). |
| **Event Handler** | `8003` | Gateway: Normalizes and routes incoming events to the Scheduler. |

---

## 🛠️ Local Setup (Backend)

### 1. Vector Database
Ensure Docker Desktop is running.
```bash
cd Backend/Qdrant\ DB
docker-compose up -d
```

### 2. AI Intelligence Core
Initialize the environment and start the models.
```bash
# Setup Environment
cd Backend
.\venv\Scripts\activate
pip install -r requirements.txt

# Start Embedding Server
python "Embedding Service/server.py"

# Start the Intelligence Engine (RAG Pipeline)
python "RAG Pipeline/server.py"
```

### 🧪 Verification & Maintenance
1. **Performance Benchmark**: Stress test the pipeline and verify Gemini ingestion latencies:
   ```bash
   python "Test Scripts/rag_pipeline_performance.py"
   ```
2. **Master Verify**: Run the unified master test to verify the entire pipeline (Scan -> Chat -> Viz):
   ```bash
   python "Test Scripts/rag_pipeline_verify.py"
   ```
3. **Database Maintenance**: Quickly clean stale collections in Qdrant:
   ```bash
   python "Test Scripts/clean_vdb.py"
   ```

---

## 🏗️ Project Lifecycle
Currently in **Phase 2: Agentic Integration**. The core RAG pipeline is stable, and we are moving toward deep document parsing and front-end visualization.