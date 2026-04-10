import requests
import os
import json
import time
from typing import List, Dict, Optional


class GroqLLMClient:
    """
    REST client for the Groq inference API using the Llama-3.3-70b model.
    All interactions are plain HTTP — no Groq SDK dependency.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        # Prioritise param > env > default
        self.model = model or os.getenv("LLM_MODEL") or "llama-3.3-70b-versatile"
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

        if not self.api_key:
            print("[WARNING] GROQ_API_KEY not set. All LLM calls will fail.")
        else:
            print(f"[*] Groq client initialised (Model: {self.model})")

    def chat_completion(self, messages: List[Dict], temperature: float = 0.2, max_retries: int = 3) -> Optional[str]:
        """
        Sends a chat request to Groq with Exponential Backoff for Rate Limits (429).
        """
        if not self.api_key:
            return "Error: No Groq API key configured."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }

        for attempt in range(max_retries):
            try:
                res = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
                
                if res.status_code == 429:
                    wait_time = (2 ** attempt)  # 1, 2, 4 seconds
                    print(f"[!] Groq Rate Limit (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                res.raise_for_status()
                return res.json()['choices'][0]['message']['content']

            except requests.exceptions.Timeout:
                print(f"[!] Groq API timeout (Attempt {attempt+1}/{max_retries}).")
                time.sleep(1)
            except requests.exceptions.HTTPError as e:
                print(f"[!] Groq API HTTP error: {e.response.status_code} — {e.response.text}")
                if e.response.status_code in [500, 502, 503, 504]:
                    time.sleep(1)
                    continue
                return None
            except Exception as e:
                print(f"[!] Groq API unexpected error: {e}")
                return None

        return None

    def summarise_file(self, filename: str, content: str) -> Optional[str]:
        """
        Produces a technical summary of a single source file.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a senior software architect performing a code review. "
                    "Summarise the purpose, core logic, and key dependencies of the provided file. "
                    "Be concise and technically precise. Maximum 150 words."
                )
            },
            {"role": "user", "content": f"File: `{filename}`\n\n```\n{content[:5000]}\n```"}
        ]
        return self.chat_completion(messages)

    def select_key_files(self, repo_tree: List[str]) -> List[str]:
        """
        Agentic step: given a full file tree (pre-filtered by scanner), 
        returns the 10-15 most architecturally important files.
        """
        # No longer slicing at 300, as the tree is now junk-filtered.
        tree_text = "\n".join(repo_tree)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a repository analyst. Examine the directory tree below and identify "
                    "the 10-15 files that best represent the project's architecture, entry points, "
                    "and core logic (e.g. README, main server files, agent logic, database schemas). "
                    "Prioritize source code over configuration. "
                    "Return ONLY a valid JSON array of file path strings. No explanation."
                )
            },
            {"role": "user", "content": f"Repository Tree:\n{tree_text}"}
        ]

        response = self.chat_completion(messages)
        if not response:
            print("[!] Groq returned no response for file selection.")
            return []

        print(f"[*] Raw LLM selection response: {response[:150]}...")
        try:
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end > 0:
                return json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[!] Failed to parse LLM file selection response: {e}")

        return []


# --- Quick sanity test ---
if __name__ == "__main__":
    client = GroqLLMClient()
    result = client.chat_completion([{"role": "user", "content": "Reply with: Groq connection verified."}])
    print(f"Groq test: {result}")
