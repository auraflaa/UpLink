import os
import time
from dotenv import load_dotenv

# --- 1. BOOTSTRAP ENVIRONMENT ---
# MUST come before any other imports that might use env vars
load_dotenv()

key = os.getenv("GOOGLE_API_KEY", "")
if key:
    print(f"[*] Environment Loaded. Google API Key Found: {key[:6]}...{key[-4:]}")
else:
    print("[!] ERROR: No GOOGLE_API_KEY found in environment!")

import requests
import json
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# These MUST be imported AFTER load_dotenv() so they pick up the config
from agent import RAGPipelineAgent
from memory import MemoryStore, SessionManager

# --- 2. CONFIGURATION ---
PORT = int(os.getenv("RAG_PIPELINE_PORT", 6399))
HOST = "0.0.0.0"
QDRANT_URL = f"http://127.0.0.1:{os.getenv('QDRANT_PORT', 6366)}"
EMBEDDING_URL = f"http://127.0.0.1:{os.getenv('EMBEDDING_PORT', 6377)}/embed"

# --- 3. INITIALISATION ---
app = FastAPI(
    title="UpLink RAG Pipeline",
    description="Agentic repository analysis, semantic chat, and workflow visualisation.",
    version="1.0.0"
)

agent = RAGPipelineAgent()
memory = MemoryStore()
sessions = SessionManager()


# --- 3. REQUEST SCHEMAS ---
class ScanRequest(BaseModel):
    source_url: Optional[str] = None
    repo_url: Optional[str] = None  # Backward compatibility alias
    source_type: str = "github"
    collection_name: str = "project_knowledge"

    @property
    def url(self) -> str:
        return self.source_url or self.repo_url or ""

class ChatRequest(BaseModel):
    query: str
    user_id: str
    session_id: str = "default"
    collection_name: str = "project_knowledge"
    source_url: Optional[str] = None
    repo_url: Optional[str] = None
    source_type: str = "github"

    @property
    def url(self) -> str:
        return self.source_url or self.repo_url or ""


# --- 4. ENDPOINTS ---

@app.get("/health")
def health_check():
    return {"status": "online", "service": "rag-pipeline", "port": PORT}


@app.get("/status")
def check_source_status(source_url: Optional[str] = None, repo_url: Optional[str] = None, collection_name: str = "project_knowledge"):
    """
    Checks whether a source has already been analysed and indexed.
    """
    url = source_url or repo_url
    if not url:
        raise HTTPException(status_code=400, detail="Missing source_url or repo_url")
        
    indexed = agent.is_indexed(collection_name, url)
    return {
        "source_url": url, 
        "indexed": indexed, 
        "collection": collection_name,
        "telemetry": agent.last_run_telemetry if indexed else {}
    }


@app.get("/sessions/{user_id}")
def list_user_sessions(user_id: str):
    """Returns all active chat sessions for a given user."""
    return {
        "user_id": user_id,
        "sessions": sessions.get_user_sessions(user_id)
    }


@app.post("/analyze")
def analyze_source(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Triggers source analysis (GitHub, Jira, etc.)
    Now includes link validation.
    """
    url = request.url
    if not url:
        raise HTTPException(status_code=400, detail="source_url or repo_url is required.")

    # Validate Link
    if not agent.validate_source(url, request.source_type):
        raise HTTPException(status_code=400, detail=f"Invalid or unreachable {request.source_type} link: {url}")

    background_tasks.add_task(
        agent.analyze_source, url, request.source_type, request.collection_name
    )
    return {
        "status": "accepted",
        "message": f"Analysis started for {url} ({request.source_type}). Check /status to confirm.",
        "collection": request.collection_name
    }


@app.post("/chat")
def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    RAG-powered conversational endpoint with session-aware memory.
    Now includes detailed telemetry and async persistence.
    """
    telemetry = {}
    try:
        t_overall = time.perf_counter()

        # 1. Register session if new
        sessions.add_session(request.user_id, request.session_id)

        # 2. Embed the query
        t0 = time.perf_counter()
        embed_res = requests.post(EMBEDDING_URL, json={"texts": [request.query]}, timeout=3)
        embed_res.raise_for_status()
        query_vector = embed_res.json().get("embeddings")[0]
        telemetry['embedding_ms'] = (time.perf_counter() - t0) * 1000

        # 3. Retrieve short-term session history
        t0 = time.perf_counter()
        short_term_history = memory.get_recent_history(
            request.user_id, request.session_id, limit=10
        )
        telemetry['memory_history_ms'] = (time.perf_counter() - t0) * 1000
        
        # 4. Semantic search over long-term memory
        t0 = time.perf_counter()
        long_term_hits = memory.search_long_term_memory(
            request.user_id, request.query, limit=2
        )
        telemetry['memory_longterm_ms'] = (time.perf_counter() - t0) * 1000

        # 5. Search project knowledge collection
        t0 = time.perf_counter()
        project_search_res = requests.post(
            f"{QDRANT_URL}/collections/{request.collection_name}/points/search",
            json={"vector": query_vector, "limit": 6, "with_payload": True},
            timeout=2
        )
        project_search = project_search_res.json().get("result", [])
        telemetry['vector_search_ms'] = (time.perf_counter() - t0) * 1000

        # 6. Compile context from project knowledge
        project_context = "\n\n".join([
            f"File: {r['payload'].get('filename', 'unknown')}\n{r['payload'].get('summary', '')}"
            for r in project_search
        ])

        # 7. Append long-term memory hits as extra context
        if long_term_hits:
            long_term_context = "\n".join([
                f"[Past session]: {m['content']}" for m in long_term_hits
            ])
            project_context += f"\n\n### Relevant Past Context:\n{long_term_context}"

        # 8. Generate grounded response
        t0 = time.perf_counter()
        answer = agent.chat_with_context(request.query, project_context, short_term_history)
        telemetry['llm_generation_ms'] = (time.perf_counter() - t0) * 1000

        # 9. Persist the conversation turn (ASYNCHRONOUS) - ONLY if answer is valid
        if answer:
            background_tasks.add_task(memory.save_message, request.user_id, request.session_id, "user", request.query)
            background_tasks.add_task(memory.save_message, request.user_id, request.session_id, "assistant", answer)
        telemetry['memory_save_ms'] = 0  # Now instant for the user

        telemetry['total_overall_ms'] = (time.perf_counter() - t_overall) * 1000

        return {
            "answer": answer,
            "sources": [r['payload'].get('filename') for r in project_search],
            "session_id": request.session_id,
            "long_term_hits": len(long_term_hits),
            "telemetry": telemetry
        }

    except Exception as e:
        print(f"[!] /chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/viz")
def generate_visualisation(request: ScanRequest):
    """
    Generates a Mermaid.js workflow diagram from the indexed project knowledge.
    Requires the repository to have been analysed first via /analyze.
    """
    try:
        url = request.url
        scroll_res = requests.post(
            f"{QDRANT_URL}/collections/{request.collection_name}/points/scroll",
            json={
                "filter": {"must": [{"key": "source_url", "match": {"value": url}}]},
                "limit": 50,
                "with_payload": True,
                "with_vector": False
            }
        )
        points = scroll_res.json().get("result", {}).get("points", [])
        summaries = [p['payload'] for p in points]

        if not summaries:
            raise HTTPException(
                status_code=404,
                detail="No indexed knowledge found for this repository. Run /analyze first."
            )

        mermaid_code = agent.generate_mermaid_diagram(summaries)
        return {"mermaid": mermaid_code, "source_files": len(summaries)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
