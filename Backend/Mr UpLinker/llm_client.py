import requests
import os
from typing import List, Dict, Optional

class GroqClient:
    """
    Client for interacting with the Groq API using the llama-3.3-70b model.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.api_key:
            print("[WARNING] No Groq API Key found. LLM features will fail.")

    def chat_completion(self, messages: List[Dict], temperature: float = 0.2) -> Optional[str]:
        """
        Sends a request to Groq and returns the text response.
        """
        if not self.api_key:
            return "Error: No API Key configured."
            
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
            res = requests.post(self.base_url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"[!] Groq API Error: {e}")
            return None

    def summarize_code(self, filename: str, content: str) -> Optional[str]:
        """
        Specific helper for summarizing a single file.
        """
        prompt = [
            {"role": "system", "content": "You are Mr. UpLinker, an expert software architect. Summarize the purpose and core logic of the provided file content. Be concise but technical."},
            {"role": "user", "content": f"File: {filename}\n\nContent:\n{content[:5000]}"} # Limit input size
        ]
        return self.chat_completion(prompt)

    def choose_files_to_read(self, repo_tree: List[str]) -> List[str]:
        """
        An agentic step: LLM looks at a file tree and chooses the most important files.
        """
        tree_text = "\n".join(repo_tree[:200]) # Limit tree size
        prompt = [
            {"role": "system", "content": "You are a repository analyzer. Look at the directory tree and pick the 5 most important files to read to understand the project structure and logic (e.g. README, main scripts, config files). Return ONLY a JSON list of file paths."},
            {"role": "user", "content": f"Directory Tree:\n{tree_text}"}
        ]
        
        response = self.chat_completion(prompt)
        if not response:
            return []
            
        try:
            # Clean response to ensure it's just JSON
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end != -1:
                return json.loads(response[start:end])
        except Exception as e:
            print(f"[!] Error parsing LLM response for file selection: {e}")
            
        return []

# Simple test block
if __name__ == "__main__":
    import json
    # Mock test (requires API key)
    client = GroqClient()
    test_res = client.chat_completion([{"role": "user", "content": "Say 'Groq is ready'."}])
    print(f"Test Result: {test_res}")
