import os
import requests
import json
import uuid
from typing import List, Dict, Optional
from dotenv import load_dotenv
from github_scanner import GitHubScanner
from llm_client import LLMClient

load_dotenv()

# --- SERVICE CONFIG (resolved from .env with fallbacks) ---
EMBEDDING_URL = f"http://127.0.0.1:{os.getenv('EMBEDDING_PORT', 6377)}/embed"
QDRANT_URL = f"http://127.0.0.1:{os.getenv('QDRANT_PORT', 6366)}"

class RAGPipelineAgent:
    """
    Unified RAG Agent capable of analyzing multiple sources (GitHub, Jira).
    Uses the Unified LLMClient for semantic intelligence.
    """

    def __init__(self, github_token: Optional[str] = None):
        import time
        self.time = time
        self.scanner = GitHubScanner(token=github_token or os.getenv("GITHUB_TOKEN"))
        self.llm = LLMClient()
        self.last_run_telemetry = {
            "tree_scan_ms": 0,
            "file_selection_ms": 0,
            "summarization_ms": 0,
            "vector_indexing_ms": 0,
            "total_ingestion_ms": 0
        }

    def validate_source(self, url: str, source_type: str = "github") -> bool:
        """
        Verifies if the source link is valid and reachable.
        """
        import re
        if source_type == "github":
            # 1. Regex check
            github_pattern = r"^https?://github\.com/[\w\.-]+/[\w\.-]+/?$"
            if not re.match(github_pattern, url.strip()):
                return False
            
            # 2. Reachability check (HEAD request)
            try:
                # We use the scanner's token if available for better rate limits
                headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"} if os.getenv("GITHUB_TOKEN") else {}
                res = requests.head(url.strip(), headers=headers, timeout=5, allow_redirects=True)
                return res.status_code == 200
            except:
                return False
        
        elif source_type == "jira":
            # Simple URL format check for Jira
            return url.startswith("http") and "atlassian.net" in url
            
        return False

    # ------------------------------------------------------------------ #
    #  PHASE 1 — Source Ingestion                                         #
    # ------------------------------------------------------------------ #

    def analyze_source(self, source_url: str, source_type: str = "github", collection_name: str = "project_knowledge") -> Optional[List[Dict]]:
        """
        Orchestrates ingestion based on source type (GitHub, Jira, etc.)
        """
        if source_type == "github":
            return self._analyze_github(source_url, collection_name)
        elif source_type == "jira":
            print(f"[*] Jira analysis for {source_url} is not yet implemented (Placeholder).")
            return None
        return None

    def _analyze_github(self, repo_url: str, collection_name: str = "project_knowledge") -> Optional[List[Dict]]:
        """
        Full Agentic Workflow for GitHub: Scan → Decide → Retrieve → Summarize → Index
        """
        try:
            self.last_run_telemetry = {}
            t_start = self.time.perf_counter()
            print(f"\n[🚀] RAG Pipeline starting analysis: {repo_url}")

            # 1. Recursive tree scan
            t0 = self.time.perf_counter()
            tree_resp = self.scanner.get_recursive_tree(repo_url)
            full_tree = [t['path'] for t in tree_resp.get('tree', []) if t['type'] == 'blob']
            self.last_run_telemetry['tree_scan_ms'] = (self.time.perf_counter() - t0) * 1000
            print(f"[*] Repository tree fetched. {len(full_tree)} files found (post-filter).")
            if not full_tree:
                print("[!] Full tree is empty after filtering. Check ignore_list.")

            # 2. LLM decides which files are most valuable
            t0 = self.time.perf_counter()
            print("[*] Requesting file selection from LLM...")
            # Limit selection to 7 core files for token efficiency
            files_to_read = self.llm.select_key_files(full_tree)[:7]
            self.last_run_telemetry['file_selection_ms'] = (self.time.perf_counter() - t0) * 1000
            print(f"[*] LLM selected {len(files_to_read)} files for summarisation (Capped at 7).")

            if not files_to_read:
                # Deterministic fallback
                candidates = ["README.md", "README", "package.json", "requirements.txt", "main.py", "Backend/requirements.txt"]
                files_to_read = [f for f in candidates if f in full_tree]
                print(f"[!] LLM selection failed or returned empty. Using fallback: {files_to_read}")

            # 3. Fetch file contents and summarise (BATCHED)
            t0 = self.time.perf_counter()
            files_to_summarize = []
            for file_path in files_to_read:
                print(f"[*] Fetching: {file_path}")
                content = self.scanner.get_file_content(repo_url, file_path)
                if content:
                    files_to_summarize.append({"filename": file_path, "content": content})

            print(f"[*] Sending batch summarisation request for {len(files_to_summarize)} files...")
            batch_results = self.llm.summarise_batch(files_to_summarize)
            
            summaries = []
            for file_path, summary in batch_results.items():
                summaries.append({
                    "filename": file_path,
                    "summary": summary,
                    "source_url": repo_url  # Unified metadata key
                })
            
            self.last_run_telemetry['summarization_ms'] = (self.time.perf_counter() - t0) * 1000

            if not summaries:
                print("[!] No summaries generated. Analysis aborted.")
                return None

            # 4. Clear stale data for this repo + re-index
            print(f"[*] Clearing stale entries for {repo_url} in '{collection_name}'...")
            self._delete_stale_entries(collection_name, repo_url)

            t0 = self.time.perf_counter()
            print(f"[*] Indexing {len(summaries)} summaries into '{collection_name}'...")
            self._index_summaries(summaries, collection_name)
            self.last_run_telemetry['vector_indexing_ms'] = (self.time.perf_counter() - t0) * 1000
            
            print(f"[✅] Analysis complete. RAG Pipeline indexed {len(summaries)} files.")
            return summaries
        except Exception as e:
            print(f"[❌] CRITICAL ERROR during analysis: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.last_run_telemetry['total_ingestion_ms'] = (self.time.perf_counter() - t_total) * 1000

    def _delete_stale_entries(self, collection_name: str, source_url: str):
        """Removes old vector entries for a specific source before re-indexing."""
        requests.post(f"{QDRANT_URL}/collections/{collection_name}/points/delete", json={
            "filter": {
                "must": [{"key": "source_url", "match": {"value": source_url}}]
            }
        })

    def _index_summaries(self, summaries: List[Dict], collection_name: str):
        """Batch-embeds summaries and upserts into Qdrant."""
        texts = [f"File: {s['filename']}\nSummary: {s['summary']}" for s in summaries]

        embed_res = requests.post(EMBEDDING_URL, json={"texts": texts})
        embed_res.raise_for_status()
        vectors = embed_res.json().get("embeddings")

        points = [
            {"id": str(uuid.uuid4()), "vector": vec, "payload": s}
            for s, vec in zip(summaries, vectors)
        ]

        # Ensure collection exists
        requests.put(f"{QDRANT_URL}/collections/{collection_name}", json={
            "vectors": {"size": 768, "distance": "Cosine"}
        })

        requests.put(f"{QDRANT_URL}/collections/{collection_name}/points", json={
            "points": points
        }).raise_for_status()

    # ------------------------------------------------------------------ #
    #  PHASE 2 — RAG Chat                                                  #
    # ------------------------------------------------------------------ #

    def chat_with_context(self, query: str, project_context: str, conversation_history: List[Dict]) -> Optional[str]:
        """
        Generates a grounded LLM response using project knowledge and session history.
        """
        history_text = "\n".join([
            f"{m['role'].capitalize()}: {m['content']}" for m in conversation_history
        ])

        system_prompt = (
            "You are an expert software engineering assistant integrated into the UpLink platform. "
            "Answer the user's question using the provided project knowledge and conversation history. "
            "Be concise and technically precise. If the context is insufficient, say so clearly.\n\n"
            f"### Project Knowledge:\n{project_context}\n\n"
            f"### Recent Conversation:\n{history_text}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        # Use the Pro model for reasoning during RAG chat
        return self.llm.chat_completion(messages, model_type="chat")

    def is_indexed(self, collection_name: str, source_url: str) -> bool:
        """Checks if a source already has indexed summaries in Qdrant."""
        try:
            res = requests.post(f"{QDRANT_URL}/collections/{collection_name}/points/scroll", json={
                "filter": {"must": [{"key": "source_url", "match": {"value": source_url}}]},
                "limit": 1,
                "with_payload": False,
                "with_vector": False
            }, timeout=2)
            if res.status_code != 200:
                return False
            return len(res.json().get("result", {}).get("points", [])) > 0
        except Exception as e:
            print(f"[!] Warning: Failed to check index status: {e}")
            return False

    # ------------------------------------------------------------------ #
    #  PHASE 3 — Visualisation                                            #
    # ------------------------------------------------------------------ #

    def generate_mermaid_diagram(self, summaries: List[Dict]) -> Optional[str]:
        """
        Generates a Mermaid.js flowchart from indexed project summaries.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a software architect. Based on the provided file summaries, "
                    "generate a high-level Mermaid.js flowchart (graph TD) that clearly shows "
                    "how the major components interact. Return ONLY valid Mermaid code."
                )
            },
            {"role": "user", "content": json.dumps(summaries)}
        ]
        return self.llm.chat_completion(messages)
