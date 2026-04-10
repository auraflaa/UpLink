import requests
import json
import base64
import os
from typing import List, Dict, Optional


class GitHubScanner:
    """
    Handles deep scanning of GitHub repositories via the REST API:
    - Recursive directory tree retrieval
    - Individual file content extraction
    - Smart token loading from env or JSON file
    """

    def __init__(self, token: Optional[str] = None):
        raw_token = token or os.getenv("GITHUB_TOKEN")
        self.token = self._resolve_token(raw_token)
        self.base_url = "https://api.github.com/repos"
        self.headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def _resolve_token(self, token_input: Optional[str]) -> Optional[str]:
        """
        Resolves a token from either:
          - A raw string (the token itself)
          - A path to a JSON file containing a 'github_token' key
        """
        if not token_input:
            return None

        if token_input.endswith(".json") and os.path.exists(token_input):
            try:
                with open(token_input, 'r') as f:
                    data = json.load(f)
                for key in ["github_token", "access_token", "token"]:
                    if key in data:
                        print(f"[*] GitHub token loaded from JSON key: '{key}'")
                        return data[key]
                print(f"[!] JSON file found at '{token_input}' but no recognised token key (github_token/access_token/token).")
            except Exception as e:
                print(f"[!] Failed to parse token JSON: {e}")
            return None

        return token_input

    def _parse_repo_path(self, repo_url: str) -> str:
        """Extracts 'owner/repo' from a full GitHub URL."""
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            raise ValueError(f"Cannot parse GitHub URL: '{repo_url}'")
        return f"{parts[-2]}/{parts[-1]}"

    def get_recursive_tree(self, repo_url: str, branch: str = "main") -> Dict:
        """
        Fetches the complete directory tree of a repository recursively.
        Automatically falls back from 'main' to 'master'.
        """
        repo_path = self._parse_repo_path(repo_url)
        url = f"{self.base_url}/{repo_path}/git/trees/{branch}?recursive=1"

        print(f"[*] Fetching repository tree: {repo_path} (branch: {branch})")
        res = requests.get(url, headers=self.headers)

        if res.status_code == 404 and branch == "main":
            print("[!] Branch 'main' not found. Retrying with 'master'...")
            return self.get_recursive_tree(repo_url, branch="master")

        res.raise_for_status()
        data = res.json()

        # --- JUNK FILTER ---
        ignore_list = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".next"}
        filtered_tree = [
            item for item in data.get("tree", [])
            if not any(part in ignore_list for part in item.get("path", "").split("/"))
        ]
        data["tree"] = filtered_tree
        # -------------------

        if data.get("truncated"):
            print(f"[!] Repository tree truncated by GitHub API (>100k entries).")

        return data

    def get_file_content(self, repo_url: str, file_path: str) -> Optional[str]:
        """
        Fetches and decodes the raw text content of a single file.
        Returns None if the file cannot be retrieved.
        """
        repo_path = self._parse_repo_path(repo_url)
        url = f"{self.base_url}/{repo_path}/contents/{file_path}"

        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            data = res.json()
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            return data.get("content")

        print(f"[!] Could not retrieve '{file_path}' (HTTP {res.status_code})")
        return None


# --- Quick sanity test ---
if __name__ == "__main__":
    import os
    scanner = GitHubScanner(token=os.getenv("GITHUB_TOKEN"))
    test_repo = "https://github.com/auraflaa/UpLink"
    try:
        tree = scanner.get_recursive_tree(test_repo)
        files = [t['path'] for t in tree.get('tree', []) if t['type'] == 'blob']
        print(f"[✅] Tree scan OK: {len(files)} files found.")
        readme = scanner.get_file_content(test_repo, "README.md")
        if readme:
            print(f"[✅] README OK: {readme[:80].strip()}...")
    except Exception as e:
        print(f"[❌] Test failed: {e}")
