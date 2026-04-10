# UpLink – Student Growth & Project Assistant

UpLink is an AI-driven personal intelligence system for students that transforms scattered digital activity into actionable insights and automated execution. It understands your work, tracks your progress, and guides your next actions.

## 🚀 Core Capabilities

- **Data Aggregation**: Unified collection from GitHub, personal notes, and external events.
- **Intelligent Processing**: Contextual understanding powered by RAG (Retrieval-Augmented Generation) and Vector Embeddings.
- **Execution Layer**: Automated scheduling via Google Calendar and direct communication through Telegram.

## 🏗️ System Architecture

### 1. Data Layer
- **GitHub Analyser**: Extracts repository data and pushes embeddings to the vector database.
- **Document Parser**: Processes resumes and personal documents.

### 2. AI & Storage Layer
- **Qdrant DB (Vector Store)**: A high-performance Rust-based vector database hosted locally in Docker (Port `6366`).
- **LLM Engine**: Central reasoning engine for progress insights and recommendations.

### 3. Action Layer
- **Scheduler**: Syncs with Google Calendar and triggers Telegram notifications.

## 🛠️ Local Setup

### 1. Start Vector Database (Qdrant)
```bash
cd "UpLink/Backend/Qdrant DB"
docker-compose up -d
```

### 2. Backend Setup
```bash
cd UpLink/Backend
python -m venv venv
# Windows
.\venv\Scripts\activate
pip install -r requirements.txt
```