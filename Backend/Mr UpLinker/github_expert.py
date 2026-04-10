import requests
import json
import base64
from typing import List, Dict, Optional

class GitHubExpert:
    """
    Handles deep scanning of GitHub repositories, including recursive tree
    retrieval and file content extraction for LLM analysis.
    """
    
    def __init__(self, token: Optional[str] = None):
        self.raw_token = token or os.getenv("GITHUB_TOKEN")
        self.token = self._load_token(self.raw_token)
        self.base_url = "https://api.github.com/repos"
        self.headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def _load_token(self, token_str: Optional[str]) -> Optional[str]:
        """
        Smart token loader: if input looks like a .json path, read it.
        Otherwise, return as-is.
        """
        if not token_str:
            return None
        
        # Check if it's a JSON path
        if token_str.endswith(".json") and os.path.exists(token_str):
            try:
                with open(token_str, 'r') as f:
                    data = json.load(f)
                    # Support standard key names
                    for key in ["github_token", "access_token", "token"]:
                        if key in data:
                            return data[key]
                    # Also support the Google structure seen earlier just in case
                    if "web" in data and "client_secret" in data["web"]:
                        return data["web"]["client_secret"]
            except Exception as e:
                print(f"[!] Warning: Failed to parse token JSON at {token_str}: {e}")
        
        return token_str

    def _parse_url(self, repo_url: str) -> str:
        """Extracts owner/repo from a GitHub URL."""
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            raise ValueError("Invalid GitHub URL format")
        return f"{parts[-2]}/{parts[-1]}"

    def get_recursive_tree(self, repo_url: str, branch: str = "main") -> Dict:
        """
        Fetches the complete directory structure recursively.
        Returns a flat list of all files and folders.
        """
        repo_path = self._parse_url(repo_url)
        # Using the git/trees endpoint with recursive=1
        url = f"{self.base_url}/{repo_path}/git/trees/{branch}?recursive=1"
        
        print(f"[*] Scanning repository tree: {repo_path} ({branch})...")
        res = requests.get(url, headers=self.headers)
        
        # Fallback if 'main' doesn't exist (try 'master')
        if res.status_code == 404 and branch == "main":
            print("[!] 'main' branch not found, trying 'master'...")
            return self.get_recursive_tree(repo_url, branch="master")
            
        res.raise_for_status()
        data = res.json()
        
        if data.get("truncated"):
            print("[WARNING] Repository tree is too large and was truncated by GitHub.")
            
        return data

    def get_file_content(self, repo_url: str, path: str) -> Optional[str]:
        """
        Fetches the raw text content of a single file.
        """
        repo_path = self._parse_url(repo_url)
        url = f"{self.base_url}/{repo_path}/contents/{path}"
        
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            data = res.json()
            # Content is usually base64 encoded
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
                return content
            return data.get("content")
        
        print(f"[!] Could not fetch file: {path} (Status: {res.status_code})")
        return None

# Simple Test Block
if __name__ == "__main__":
    import os
    # Try to load token from .env if running standalone
    token = os.getenv("GITHUB_TOKEN")
    expert = GitHubExpert(token=token)
    
    # Test with a public repo or the current project
    test_repo = "auraflaa/UpLink"
    try:
        tree = expert.get_recursive_tree(f"https://github.com/{test_repo}")
        files = [t['path'] for t in tree.get('tree', []) if t['type'] == 'blob']
        print(f"✅ Scanning successful. Found {len(files)} files.")
        
        # Try fetching README
        readme = expert.get_file_content(f"https://github.com/{test_repo}", "README.md")
        if readme:
            print(f"✅ README fetched (first 50 chars): {readme[:50]}...")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
