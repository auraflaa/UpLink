import os
import requests
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from .agent import MrUpLinkerAgent

# --- 1. CONFIGURATION ---
PORT = int(os.getenv("MR_UPLINKER_PORT", 6399))
HOST = "0.0.0.0"

app = FastAPI(title="Mr. UpLinker Brain Server")

# Initialize Agent (will load keys from .env automatically if set)
agent = MrUpLinkerAgent()

# --- 2. SCHEMAS ---
class ScanRequest(BaseModel):
    repo_url: str
    collection_name: str = "project_knowledge"

class ChatRequest(BaseModel):
    query: str
    collection_name: str = "project_knowledge"

# --- 3. ENDPOINTS ---

@app.get("/health")
def health_check():
    return {"status": "alive", "service": "mr-uplinker"}

@app.post("/analyze")
def analyze_repo(request: ScanRequest):
    """
    Triggers the Agentic Deep-Scan pipeline.
    """
    try:
        summaries = agent.analyze_repository(request.repo_url, request.collection_name)
        if not summaries:
            raise HTTPException(status_code=500, detail="Analysis failed to generate summaries.")
            
        return {
            "status": "success",
            "message": f"Successfully studied {request.repo_url}",
            "file_count": len(summaries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/viz")
def get_visualization(request: ScanRequest):
    """
    Generates Mermaid.js diagram data for the project.
    """
    try:
        # 1. Search for all summaries in this collection
        search_res = requests.post(f"{QDRANT_URL}/collections/{request.collection_name}/points/scroll", json={
            "limit": 50,
            "with_payload": True
        }).json().get("result", {}).get("points", [])
        
        summaries = [p['payload'] for p in search_res]
        
        if not summaries:
            raise HTTPException(status_code=404, detail="No project knowledge found. Please scan the repo first.")
            
        # 2. Ask LLM to generate Mermaid code
        mermaid_code = agent.generate_project_viz(summaries)
        return {"mermaid": mermaid_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_with_mr_uplinker(request: ChatRequest):
    """
    RAG-powered chat about the repository.
    """
    try:
        # 1. Embed the query
        embed_res = requests.post(EMBEDDING_URL, json={"texts": [request.query]})
        query_vec = embed_res.json().get("embeddings")[0]
        
        # 2. Search Qdrant for context
        search_res = requests.post(f"{QDRANT_URL}/collections/{request.collection_name}/points/search", json={
            "vector": query_vec,
            "limit": 3,
            "with_payload": True
        }).json().get("result", [])
        
        context = "\n\n".join([f"File: {r['payload']['filename']}\nSummary: {r['payload']['summary']}" for r in search_res])
        
        # 3. Final Answer via Groq
        prompt = [
            {"role": "system", "content": f"You are Mr. UpLinker. Answer the user's question about the repository using the provided context. If you don't know, say so. Project Context:\n{context}"},
            {"role": "user", "content": request.query}
        ]
        
        answer = agent.llm.chat_completion(prompt)
        return {"answer": answer, "sources": [r['payload']['filename'] for r in search_res]}
        
    except Exception as e:
        print(f"[!] Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
