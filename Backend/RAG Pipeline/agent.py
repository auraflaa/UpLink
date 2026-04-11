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
        self.telemetry = {
            "github": {},
            "jira": {}
        }

    @property
    def last_run_telemetry(self):
        return {**self.telemetry["github"], **self.telemetry["jira"]}

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

            # 2. Best-effort reachability check.
            # Network restrictions, proxy behavior, or private repos can make a
            # valid GitHub URL fail a HEAD request even though the downstream
            # scanner can still handle it correctly.
            try:
                headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"} if os.getenv("GITHUB_TOKEN") else {}
                res = requests.head(url.strip(), headers=headers, timeout=5, allow_redirects=True)
                if res.status_code >= 500:
                    print(f"[WARN] GitHub reachability check returned {res.status_code} for {url}. Proceeding anyway.")
                elif res.status_code >= 400:
                    print(f"[WARN] GitHub reachability check returned {res.status_code} for {url}. Proceeding with regex-only validation.")
            except Exception as exc:
                print(f"[WARN] GitHub reachability check failed for {url}: {exc}. Proceeding with regex-only validation.")

            return True
        
        elif source_type == "jira":
            # Simple URL format check for Jira
            return url.startswith("http") and "atlassian.net" in url
            
        return False

    # ------------------------------------------------------------------ #
    #  PHASE 1 — Source Ingestion                                         #
    # ------------------------------------------------------------------ #

    def analyze_source(self, source_url: str, source_type: str = "github", collection_name: str = "project_knowledge") -> Optional[List[Dict]]:
        """
        Routes ingestion to the correct handler. Fully parallel — no locks.
        Frontend is responsible for enforcing source-type limits before calling.
        """
        if source_type == "github":
            return self._analyze_github(source_url, collection_name)
        elif source_type == "jira":
            return self._analyze_jira(source_url, collection_name)
        return None

    def analyze_dual_source(self, github_url: str, jira_url: str, collection_name: str = "project_knowledge"):
        """
        Parallel ingestion coordinator. Chaining handled via individual analyze_source calls 
        (which handle their own locks).
        """
        print(f"[🚀] Starting Parallel DUAL analysis for {github_url} and {jira_url}")
        # Note: server.py will actually spawn these in separate background task threads
    def _analyze_github(self, repo_url: str, collection_name: str = "project_knowledge") -> Optional[List[Dict]]:
        """
        Full Agentic Workflow for GitHub: Scan -> Decide -> Retrieve -> Summarize -> Index.
        Runs fully in parallel — no locking. Multiple repos can be processed simultaneously.
        """
        t_start = self.time.perf_counter()
        self.telemetry["github"] = {
            "tree_scan_ms": 0,
            "file_selection_ms": 0,
            "summarization_ms": 0,
            "indexing_ms": 0,
            "total_ingestion_ms": 0
        }
        
        try:
            print(f"\n[START] [PARALLEL] GitHub Pipeline starting analysis: {repo_url}")

            # --- SMART CACHE CHECK ---
            last_embedded_utc = self._get_last_embedded_time(repo_url)
            pushed_at = self.scanner.get_repo_pushed_at(repo_url)
            if last_embedded_utc and pushed_at:
                if pushed_at <= last_embedded_utc:
                    print(f"[CACHE] GitHub {repo_url} unchanged since last index. Skipping.")
                    return []

            # 1. Recursive tree scan
            t0 = self.time.perf_counter()
            tree_resp = self.scanner.get_recursive_tree(repo_url)
            full_tree = [t['path'] for t in tree_resp.get('tree', []) if t['type'] == 'blob']
            self.telemetry["github"]['tree_scan_ms'] = (self.time.perf_counter() - t0) * 1000
            print(f"[*] Repository tree fetched. {len(full_tree)} files found.")

            # 2. LLM selects key files
            t0 = self.time.perf_counter()
            print("[*] Requesting file selection from LLM...")
            files_to_read = self.llm.select_key_files(full_tree)[:7]
            self.telemetry["github"]['file_selection_ms'] = (self.time.perf_counter() - t0) * 1000
            print(f"[*] LLM selected {len(files_to_read)} files (capped at 7).")

            if not files_to_read:
                candidates = ["README.md", "README", "package.json", "requirements.txt", "main.py", "Backend/requirements.txt"]
                files_to_read = [f for f in candidates if f in full_tree]
                print(f"[!] LLM selection empty. Using fallback: {files_to_read}")

            # 3. Fetch and summarise (batched)
            t0 = self.time.perf_counter()
            files_to_summarize = []
            for file_path in files_to_read:
                print(f"[*] Fetching: {file_path}")
                content = self.scanner.get_file_content(repo_url, file_path)
                if content:
                    files_to_summarize.append({"filename": file_path, "content": content})

            print(f"[*] Sending batch summarisation for {len(files_to_summarize)} files...")
            batch_results = self.llm.summarise_batch(files_to_summarize)
            
            summaries = [
                {"filename": fp, "summary": s, "source_url": repo_url, "source_type": "github"}
                for fp, s in batch_results.items()
            ]
            self.telemetry["github"]['summarization_ms'] = (self.time.perf_counter() - t0) * 1000

            if not summaries:
                print("[!] No summaries generated. Analysis aborted.")
                return None

            # 4. Index
            t0 = self.time.perf_counter()
            print(f"[*] Indexing {len(summaries)} summaries into '{collection_name}'...")
            self._index_summaries(summaries, collection_name)
            self.telemetry["github"]['indexing_ms'] = (self.time.perf_counter() - t0) * 1000
            
            print(f"[OK] GitHub analysis complete. Indexed {len(summaries)} files.")
            return summaries

        except Exception as e:
            print(f"[FAIL] CRITICAL ERROR during GitHub analysis: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.telemetry["github"]['total_ingestion_ms'] = (self.time.perf_counter() - t_start) * 1000

    def _analyze_jira(self, source_url: str, collection_name: str) -> Optional[List[Dict]]:
        """
        Fetches structured Jira data from the Scheduler and indexes it.
        Runs fully in parallel — no locking.
        """
        t_start = self.time.perf_counter()
        self.telemetry["jira"] = {
            "jira_fetch_ms": 0,
            "summarization_ms": 0,
            "indexing_ms": 0,
            "total_ingestion_ms": 0
        }
        scheduler_url = os.getenv("SCHEDULER_URL", "http://127.0.0.1:8002")
        print(f"[*] [PARALLEL] Starting JIRA analysis for: {source_url}")
        
        try:
            # 1. Fetch RAG-ready document from Scheduler
            t0 = self.time.perf_counter()
            res = requests.get(f"{scheduler_url}/jira/rag-document", params={"url": source_url}, timeout=30)
            res.raise_for_status()
            data = res.json()
            
            if data.get("status") != "completed":
                print(f"[!] Scheduler Jira analysis failed: {data.get('message')}")
                return None
                
            rag_doc = data.get("rag_document")
            self.telemetry["jira"]['jira_fetch_ms'] = (self.time.perf_counter() - t0) * 1000

            # --- SMART CACHE CHECK ---
            last_embedded_utc = self._get_last_embedded_time(source_url)
            ticket_updated_at = rag_doc.get("metadata", {}).get("updated")
            if last_embedded_utc and ticket_updated_at:
                if ticket_updated_at <= last_embedded_utc:
                    print(f"[CACHE] Jira ticket {source_url} unchanged. Skipping.")
                    return []
            
            # 2. Summarise
            print(f"[*] Sending Jira data for Gemini summarisation...")
            t0 = self.time.perf_counter()
            file_obj = {
                "filename": rag_doc.get("title", "Jira Task"),
                "content": rag_doc.get("content", "")
            }
            batch_results = self.llm.summarise_batch([file_obj])
            llm_summary = list(batch_results.values())[0] if batch_results else "Summary unavailable."
            self.telemetry["jira"]['summarization_ms'] = (self.time.perf_counter() - t0) * 1000
            
            # 3. Index
            summary_entry = {
                "filename": rag_doc.get("title", "Jira Document"),
                "summary": llm_summary,
                "source_url": source_url,
                "source_type": "jira",
                "metadata": rag_doc.get("metadata", {})
            }
            
            t0 = self.time.perf_counter()
            self._index_summaries([summary_entry], collection_name)
            self.telemetry["jira"]['indexing_ms'] = (self.time.perf_counter() - t0) * 1000
            
            print(f"[OK] JIRA analysis complete for {source_url}.")
            return [summary_entry]
            
        except Exception as e:
            print(f"[FAIL] Error during JIRA analysis: {e}")
            return None
        finally:
            self.telemetry["jira"]['total_ingestion_ms'] = (self.time.perf_counter() - t_start) * 1000

    def _get_last_embedded_time(self, source_url: str) -> Optional[str]:
        """Helper to quickly check the embedding registry for the last ingestion time."""
        registry_path = "embedding_registry.json"
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)
                return registry.get(source_url, {}).get("last_embedded_utc")
            except Exception:
                pass
        return None

    def _clear_previous_source_data(self, collection_name: str, source_type: str):
        """
        Enforces the 'Singleton Source' rule: Wipes all data of a specific type.
        """
        requests.post(f"{QDRANT_URL}/collections/{collection_name}/points/delete", json={
            "filter": {
                "must": [{"key": "source_type", "match": {"value": source_type}}]
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

        # --- Embedding Registry Tracker ---
        if summaries:
            registry_path = "embedding_registry.json"
            registry = {}
            if os.path.exists(registry_path):
                try:
                    with open(registry_path, "r", encoding="utf-8") as f:
                        registry = json.load(f)
                except Exception:
                    pass
            
            import datetime
            source_url = summaries[0].get("source_url", "unknown_url")
            registry[source_url] = {
                "source_type": summaries[0].get("source_type", "unknown"),
                "indexed_items": len(summaries),
                "last_embedded_utc": datetime.datetime.utcnow().isoformat(),
                "collection": collection_name
            }
            
            with open(registry_path, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=4)
            print(f"[*] Saved embedding payload to {registry_path}")

    # ------------------------------------------------------------------ #
    #  PHASE 2 — RAG Chat                                                  #
    # ------------------------------------------------------------------ #

    def chat_with_context(self, query: str, project_context: str, conversation_history: list) -> str | None:
        """
        Generates a grounded LLM response using project knowledge and session history.
        Output-only: never exposes reasoning or system text.
        """
        history_text = "\n".join([
            f"{m['role'].capitalize()}: {m['content']}" for m in (conversation_history or [])[-6:]
        ])

        context_section = f"Project context:\n{project_context.strip()}" if project_context.strip() else ""
        history_section = f"Recent conversation:\n{history_text}" if history_text else ""
        background = "\n\n".join(filter(None, [context_section, history_section]))

        system_prompt = (
            "You are UpLink, an AI software engineering assistant. "
            "Answer using the project context if provided. "
            "\n\nCRITICAL RULES:\n"
            "- Output ONLY the final answer. Nothing else.\n"
            "- NEVER show reasoning, analysis steps, thought process, or internal notes.\n"
            "- NEVER start with labels like 'User question:', 'Context:', 'Intent:', etc.\n"
            "- Begin immediately with the actual answer content.\n"
            "- Use clean markdown - headings, bullets, code blocks ONLY for the answer itself."
        )

        user_content = (f"{background}\n\nAnswer this: {query}" if background else query)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

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
