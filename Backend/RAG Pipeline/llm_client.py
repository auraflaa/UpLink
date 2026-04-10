import os
import json
import time
import random
import requests
from typing import List, Dict, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Gemini rate limit retry config
_GEMINI_MAX_RETRIES = 5
_GEMINI_BASE_DELAY = 2  # seconds, doubled each retry

class LLMClient:
    """
    Unified LLM Client supporting multiple providers (Google Gemini, Groq).
    Source-agnostic and dual-model ready (Summary vs Chat).
    """

    def __init__(self, provider: Optional[str] = None):
        # Auto-detect provider if not specified
        self.provider = provider or self._detect_provider()
        
        # Load keys & models
        self.google_key = os.getenv("GOOGLE_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        
        # Model mapping for dual-model architecture
        self.summary_model = os.getenv("SUMMARY_MODEL") or os.getenv("LLM_MODEL") or "gemini-1.5-flash"
        self.chat_model = os.getenv("CHAT_MODEL") or os.getenv("LLM_MODEL") or "gemini-1.5-pro"

        if self.provider == "google":
            # Sanitize Google model names (must be lowercase and prefixed with 'models/')
            def sanitize_google(name):
                name = name.lower()
                if not name.startswith("models/"):
                    return f"models/{name}"
                return name
            
            self.summary_model = sanitize_google(self.summary_model)
            self.chat_model = sanitize_google(self.chat_model)

            if not self.google_key:
                print("[!] ERROR: GOOGLE_API_KEY missing for Google provider.")
            else:
                genai.configure(api_key=self.google_key)
                self.google_summary = genai.GenerativeModel(self.summary_model)
                self.google_chat = genai.GenerativeModel(self.chat_model)
                print(f"[*] Unified Client: Google Gemini (Summary: {self.summary_model}, Chat: {self.chat_model})")
        
        elif self.provider == "groq":
            if not self.groq_key:
                print("[!] ERROR: GROQ_API_KEY missing for Groq provider.")
            else:
                self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
                print(f"[*] Unified Client: Groq (Model: {self.chat_model})")

    def _detect_provider(self) -> str:
        if os.getenv("GOOGLE_API_KEY"):
            return "google"
        if os.getenv("GROQ_API_KEY"):
            return "groq"
        return "unknown"

    def chat_completion(self, messages: List[Dict], temperature: float = 0.2, model_type: str = "chat", max_retries: int = 3) -> Optional[str]:
        """
        Generic chat completion interface.
        model_type: 'chat' (Pro reasoning) or 'summary' (Flash throughput).
        """
        model_name = self.chat_model if model_type == "chat" else self.summary_model

        if self.provider == "google":
            return self._google_chat(messages, model_name, temperature)
        elif self.provider == "groq":
            return self._groq_chat(messages, model_name, temperature, max_retries)
        
        return "Error: No LLM provider configured."

    def _gemini_call_with_retry(self, model, prompt: str, temperature: float = 0.2) -> Optional[str]:
        """
        Wrapper for all Gemini generate_content calls.
        Retries on 429 (Resource Exhausted) with exponential backoff + jitter.
        """
        for attempt in range(_GEMINI_MAX_RETRIES):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(temperature=temperature)
                )
                return response.text
            except Exception as e:
                err = str(e)
                is_rate_limit = "429" in err or "Resource has been exhausted" in err or "RESOURCE_EXHAUSTED" in err
                if is_rate_limit and attempt < _GEMINI_MAX_RETRIES - 1:
                    delay = (_GEMINI_BASE_DELAY ** attempt) + random.uniform(0, 1)
                    print(f"[!] Gemini rate limit hit (attempt {attempt+1}/{_GEMINI_MAX_RETRIES}). Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    print(f"[!] Gemini Error (attempt {attempt+1}): {e}")
                    return None
        return None

    def _google_chat(self, messages: List[Dict], model_name: str, temperature: float) -> Optional[str]:
        # Separate system instruction from user messages (pure Python, no try needed)
        system_msg = next((m['content'] for m in messages if m['role'] == 'system'), None)
        user_msgs = [m for m in messages if m['role'] != 'system']

        if "gemma" in model_name.lower():
            # Open-weight Gemma models reject strict system_instruction payloads
            model = genai.GenerativeModel(model_name=model_name)
            prompt = ""
            if system_msg:
                prompt += f"System Instructions: {system_msg}\n\n"
            prompt += "\n".join([f"{m['role'].upper()}: {m['content']}" for m in user_msgs])
        else:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_msg
            )
            prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in user_msgs])

        return self._gemini_call_with_retry(model, prompt, temperature)


    def _groq_chat(self, messages: List[Dict], model_name: str, temperature: float, max_retries: int) -> Optional[str]:
        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        payload = {"model": model_name, "messages": messages, "temperature": temperature}
        
        for attempt in range(max_retries):
            try:
                res = requests.post(self.groq_url, headers=headers, json=payload, timeout=30)
                if res.status_code == 429:
                    time.sleep(2**attempt)
                    continue
                res.raise_for_status()
                return res.json()['choices'][0]['message']['content']
            except Exception as e:
                print(f"[!] Groq Error: {e}")
                time.sleep(1)
        return None

    def summarise_batch(self, files: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Summarizes multiple files. uses Flash for Google or loop for Groq.
        """
        if self.provider == "google":
            return self._google_summarise_batch(files)
        
        # Fallback to sequential for Groq (legacy)
        results = {}
        for f in files:
            summary = self.chat_completion([
                {"role": "system", "content": "Summarize this file."},
                {"role": "user", "content": f['content'][:3000]}
            ], model_type="summary")
            if summary:
                results[f['filename']] = summary
        return results

    def _google_summarise_batch(self, files: List[Dict[str, str]]) -> Dict[str, str]:
        prompt = "Summarize the following code files for a technical knowledge base. Respond ONLY with a JSON object where keys are filenames and values are concise technical summaries.\n\n"
        for f in files:
            prompt += f"--- FILE: {f['filename']} ---\n{f['content'][:5000]}\n\n"

        try:
            return self._extract_json(
                self._gemini_call_with_retry(self.google_summary, prompt, temperature=0.2) or "{}"
            )
        except Exception as e:
            print(f"[!] Gemini Batch Error: {e}")
            return {}

    def _extract_json(self, text: str) -> Dict:
        """Helper to robustly extract JSON from LLM responses."""
        try:
            # Look for the first { and last }
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > 0:
                return json.loads(text[start:end])
            return json.loads(text)
        except Exception as e:
            print(f"[!] Failed to parse JSON from response: {e}")
            return {}

    def select_key_files(self, repo_tree: List[str]) -> List[str]:
        tree_text = "\n".join(repo_tree)
        prompt = f"Identify the 10 most relevant source files for understanding the architecture from this tree. Return ONLY a JSON array of file paths.\n\n{tree_text}"
        
        messages = [{"role": "system", "content": "You are a repository analyst. Return ONLY a JSON array."}, {"role": "user", "content": prompt}]
        
        response = self.chat_completion(messages, model_type="summary")
        if not response: return []
        
        try:
            start, end = response.find("["), response.rfind("]") + 1
            if start != -1 and end > 0:
                return json.loads(response[start:end])
            return json.loads(response)
        except Exception as e:
            print(f"[!] Failed to parse file selection JSON: {e}")
            return []
