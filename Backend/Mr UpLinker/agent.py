import os
import json
import uuid
from typing import List, Dict, Optional
from .github_expert import GitHubExpert
from .llm_client import GroqClient
import requests

# Constants
EMBEDDING_URL = "http://localhost:6377/embed"
QDRANT_URL = "http://localhost:6366"

class MrUpLinkerAgent:
    """
    The main orchestrator for agentic repository analysis.
    """
    
    def __init__(self, github_token: Optional[str] = None, groq_api_key: Optional[str] = None):
        self.github = GitHubExpert(token=github_token)
        self.llm = GroqClient(api_key=groq_api_key)
        
    def analyze_repository(self, repo_url: str, collection_name: str = "project_knowledge"):
        """
        Full Agentic Workflow: Scan -> Decide -> Read -> Summarize -> Index
        """
        print(f"\n[🚀] Mr. UpLinker is studying repo: {repo_url}")
        
        # 1. SCAN RECURSIVE TREE
        tree_resp = self.github.get_recursive_tree(repo_url)
        full_tree = [t['path'] for t in tree_resp.get('tree', []) if t['type'] == 'blob']
        print(f"[*] Found {len(full_tree)} files in tree.")

        # 2. DECIDE IMPORTANT FILES
        print("[*] Mr. UpLinker is deciding which files are most important...")
        files_to_read = self.llm.choose_files_to_read(full_tree)
        
        if not files_to_read:
            # Fallback to defaults if LLM fails
            files_to_read = ["README.md", "README", "package.json", "requirements.txt", "main.py"]
            files_to_read = [f for f in files_to_read if f in full_tree]
        
        print(f"[*] Decision: reading {len(files_to_read)} files: {files_to_read}")

        # 3. RETRIEVE & SUMMARIZE
        summaries = []
        for file_path in files_to_read:
            print(f"[*] Reading and summarizing {file_path}...")
            content = self.github.get_file_content(repo_url, file_path)
            if content:
                summary = self.llm.summarize_code(file_path, content)
                if summary:
                    summaries.append({
                        "filename": file_path,
                        "summary": summary,
                        "repo": repo_url
                    })

        if not summaries:
            print("[!] No summaries generated.")
            return

        # 4. INDEX IN VECTOR DB
        print(f"[*] Indexing {len(summaries)} summaries into Qdrant collection '{collection_name}'...")
        self._index_summaries(summaries, collection_name)
        
        print(f"✨ Analysis complete. Mr. UpLinker is now an expert on {repo_url}!")
        return summaries

    def _index_summaries(self, summaries: List[Dict], collection_name: str):
        """
        Helper to handle embedding and storage.
        """
        # Batch Embed
        texts = [f"File: {s['filename']}\nSummary: {s['summary']}" for s in summaries]
        embed_res = requests.post(EMBEDDING_URL, json={"texts": texts})
        embed_res.raise_for_status()
        vectors = embed_res.json().get("embeddings")

        # Prep points for Qdrant
        points = []
        for s, vec in zip(summaries, vectors):
            points.append({
                "id": str(uuid.uuid4()),
                "vector": vec,
                "payload": s
            })

        # Ensure collection
        requests.put(f"{QDRANT_URL}/collections/{collection_name}", json={
            "vectors": {"size": 768, "distance": "Cosine"}
        })

        # Upsert
        requests.put(f"{QDRANT_URL}/collections/{collection_name}/points", json={
            "points": points
        }).raise_for_status()

# Optional Visualization Logic (Mermaid)
    def generate_project_viz(self, summaries: List[Dict]) -> str:
        """
        Drafts a Mermaid.js diagram based on the summaries.
        """
        prompt = [
            {"role": "system", "content": "You are a software architect. Look at the summaries of these files and create a high-level Mermaid.js flowchart (graph TD) showing how the core components interact. Return ONLY the mermaid code."},
            {"role": "user", "content": json.dumps(summaries)}
        ]
        return self.llm.chat_completion(prompt)
