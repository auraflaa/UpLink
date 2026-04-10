import requests
import os
import json
from typing import List, Dict, Optional


class GroqLLMClient:
    """
    REST client for the Groq inference API using the Llama-3.3-70b model.
    All interactions are plain HTTP — no Groq SDK dependency.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

        if not self.api_key:
            print("[WARNING] GROQ_API_KEY not set. All LLM calls will fail.")

    def chat_completion(self, messages: List[Dict], temperature: float = 0.2) -> Optional[str]:
        """
        Sends a chat request to Groq and returns the assistant's text response.
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

        try:
            res = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            res.raise_for_status()
            return res.json()['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            print("[!] Groq API timeout.")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"[!] Groq API HTTP error: {e.response.status_code} — {e.response.text}")
            return None
        except Exception as e:
            print(f"[!] Groq API unexpected error: {e}")
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
        Agentic step: given a full file tree, returns the 5-7 most architecturally
        important files to read for project understanding.
        Returns a JSON list of file paths.
        """
        tree_text = "\n".join(repo_tree[:300])
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a repository analyst. Examine the directory tree below and identify "
                    "the 5-7 files that best represent the project's architecture, entry points, "
                    "and dependencies (e.g. README, main server files, config files, package manifests). "
                    "Return ONLY a valid JSON array of file path strings. No explanation."
                )
            },
            {"role": "user", "content": f"Repository Tree:\n{tree_text}"}
        ]

        response = self.chat_completion(messages)
        if not response:
            return []

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
