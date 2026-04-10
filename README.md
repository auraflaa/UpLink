# UpLink – Agentic AI Student & Project Assistant

UpLink is an AI-driven personal intelligence system that transforms repository activity and digital documentation into actionable insights. Powered by agentic RAG pipelines and high-performance vector search, it understands your codebases, tracks progress, and visualizes project workflows.

## 🚀 Core Capabilities

- **Mr. UpLinker (Agentic RAG)**: A dedicated AI agent that performs deep scans of GitHub repositories, decides which files to prioritize, and creates summarized semantic knowledge.
- **Microservice Intelligence**: Decoupled architecture with standalone Embedding and Vector DB services.
- **Workflow Visualization**: LLM-generated Mermaid.js diagrams for project architecture and logic flows.
- **Unified Action Layer**: Integration with Google Calendar and Telegram for automated scheduling.

## 📡 Service Architecture

UpLink is built as a distributed microservice system to ensure high performance and GPU acceleration:

| Service | Port | Logic |
| :--- | :--- | :--- |
| **Mr. UpLinker** | `6399` | The "Brain": Agentic orchestration and RAG-Chat. |
| **Embedding Server** | `6377` | AI Inference: All-MPNet-Base-v2 (CUDA/CPU). |
| **Vector DB (Qdrant)** | `6366` | Storage: Persistent Vector Database (Docker). |

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

# Start the Brain (Mr. UpLinker)
python "Mr UpLinker/server.py"
```

### 🧪 Verification
Run the unified master test to verify the entire pipeline (Scan -> Chat -> Viz):
```bash
python "Test Scripts/mr_uplinker_verify.py"
```

---

## 🏗️ Project Lifecycle
Currently in **Phase 2: Agentic Integration**. The core RAG pipeline is stable, and we are moving toward deep document parsing and front-end visualization.