import os
import requests
import json
import uuid
import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from dotenv import load_dotenv
from agent import RAGPipelineAgent
from memory import MemoryStore, SessionManager

# Load .env from the same directory as this script
load_dotenv()

# --- 1. CONFIGURATION ---
PORT = int(os.getenv("RAG_PIPELINE_PORT", 6399))
HOST = "0.0.0.0"
QDRANT_URL = f"http://localhost:{os.getenv('QDRANT_PORT', 6366)}"
EMBEDDING_URL = f"http://localhost:{os.getenv('EMBEDDING_PORT', 6377)}/embed"

# --- 2. INITIALISATION ---
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
    repo_url: str
    collection_name: str = "project_knowledge"

class ChatRequest(BaseModel):
    query: str
    user_id: str
    session_id: str = "default"
    collection_name: str = "project_knowledge"


# --- 4. ENDPOINTS ---

@app.get("/health")
def health_check():
    return {"status": "online", "service": "rag-pipeline", "port": PORT}


@app.get("/status")
def check_repo_status(repo_url: str, collection_name: str = "project_knowledge"):
    """
    Checks whether a repository has already been analysed and indexed.
    """
    indexed = agent.is_repo_indexed(collection_name, repo_url)
    return {"repo_url": repo_url, "indexed": indexed, "collection": collection_name}


@app.get("/sessions/{user_id}")
def list_user_sessions(user_id: str):
    """Returns all active chat sessions for a given user."""
    return {
        "user_id": user_id,
        "sessions": sessions.get_user_sessions(user_id)
    }


@app.post("/analyze")
def analyze_repository(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Triggers the full agentic repository scan:
    Tree Fetch → LLM File Selection → Content Retrieval → Summarisation → Vector Indexing.
    Runs as a background task to avoid blocking the server.
    """
    background_tasks.add_task(
        agent.analyze_repository, request.repo_url, request.collection_name
    )
    return {
        "status": "accepted",
        "message": f"Analysis started for {request.repo_url}. Check /status to confirm indexing.",
        "collection": request.collection_name
    }


@app.post("/chat")
def chat(request: ChatRequest):
    """
    RAG-powered conversational endpoint with session-aware memory.
    Retrieves project context + conversation history before generating a response.
    """
    try:
        # 1. Register session if new
        sessions.add_session(request.user_id, request.session_id)

        # 2. Embed the query
        embed_res = requests.post(EMBEDDING_URL, json={"texts": [request.query]})
        embed_res.raise_for_status()
        query_vector = embed_res.json().get("embeddings")[0]

        # 3. Retrieve short-term session history
        short_term_history = memory.get_recent_history(
            request.user_id, request.session_id, limit=10
        )

        # 4. Semantic search over long-term memory for related past context
        long_term_hits = memory.search_long_term_memory(
            request.user_id, request.query, limit=2
        )

        # 5. Search project knowledge collection
        project_search = requests.post(
            f"{QDRANT_URL}/collections/{request.collection_name}/points/search",
            json={"vector": query_vector, "limit": 3, "with_payload": True}
        ).json().get("result", [])

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
        answer = agent.chat_with_context(request.query, project_context, short_term_history)

        # 9. Persist the conversation turn
        memory.save_message(request.user_id, request.session_id, "user", request.query)
        memory.save_message(request.user_id, request.session_id, "assistant", answer)

        return {
            "answer": answer,
            "sources": [r['payload'].get('filename') for r in project_search],
            "session_id": request.session_id,
            "long_term_hits": len(long_term_hits)
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
        scroll_res = requests.post(
            f"{QDRANT_URL}/collections/{request.collection_name}/points/scroll",
            json={
                "filter": {"must": [{"key": "repo_url", "match": {"value": request.repo_url}}]},
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
