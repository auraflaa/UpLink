import os
import json
import uuid
import time
import requests
from typing import List, Dict, Optional
from tinydb import TinyDB, Query

# Constants
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6366")
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "http://localhost:6377/embed")
MEMORY_COLLECTION = "chat_memory"
USER_DB_PATH = "user_sessions.json"

class SessionManager:
    """
    Manages user-to-session mappings using TinyDB.
    """
    def __init__(self, db_path: str = USER_DB_PATH):
        self.db = TinyDB(db_path)
        self.User = Query()

    def get_or_create_user(self, user_id: str) -> Dict:
        user = self.db.search(self.User.user_id == user_id)
        if not user:
            new_user = {"user_id": user_id, "sessions": []}
            self.db.insert(new_user)
            return new_user
        return user[0]

    def add_session(self, user_id: str, session_id: str, title: str = "New Chat"):
        user = self.get_or_create_user(user_id)
        if session_id not in [s['session_id'] for s in user['sessions']]:
            user['sessions'].append({
                "session_id": session_id,
                "title": title,
                "created_at": time.time()
            })
            self.db.update({"sessions": user['sessions']}, self.User.user_id == user_id)

    def get_user_sessions(self, user_id: str) -> List[Dict]:
        user = self.get_or_create_user(user_id)
        return user['sessions']

class MemoryStore:
    """
    Handles storage and semantic retrieval of chat messages in Qdrant.
    """
    def __init__(self):
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensures the chat_memory collection exists in Qdrant."""
        res = requests.get(f"{QDRANT_URL}/collections/{MEMORY_COLLECTION}")
        if res.status_code != 200:
            print(f"[*] Creating {MEMORY_COLLECTION} collection...")
            requests.put(f"{QDRANT_URL}/collections/{MEMORY_COLLECTION}", json={
                "vectors": {"size": 768, "distance": "Cosine"}
            })

    def save_message(self, user_id: str, session_id: str, role: str, content: str):
        """
        Embeds and stores a single message in Qdrant.
        """
        # 1. Embed message
        embed_res = requests.post(EMBEDDING_URL, json={"texts": [content]})
        embed_res.raise_for_status()
        vector = embed_res.json().get("embeddings")[0]

        # 2. Store in Qdrant
        point_id = str(uuid.uuid4())
        payload = {
            "user_id": user_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        
        requests.put(f"{QDRANT_URL}/collections/{MEMORY_COLLECTION}/points", json={
            "points": [{
                "id": point_id,
                "vector": vector,
                "payload": payload
            }]
        }).raise_for_status()

    def get_recent_history(self, user_id: str, session_id: str, limit: int = 10) -> List[Dict]:
        """
        Retrieves the last N messages for a specific session (Chronological).
        """
        # We use a scroll with a filter for session_id
        res = requests.post(f"{QDRANT_URL}/collections/{MEMORY_COLLECTION}/points/scroll", json={
            "filter": {
                "must": [
                    {"key": "user_id", "match": {"value": user_id}},
                    {"key": "session_id", "match": {"value": session_id}}
                ]
            },
            "limit": limit,
            "with_payload": True,
            "with_vector": False
        })
        
        points = res.json().get("result", {}).get("points", [])
        # Sort by timestamp
        points.sort(key=lambda x: x['payload']['timestamp'])
        return [p['payload'] for p in points]

    def search_long_term_memory(self, user_id: str, query: str, limit: int = 3) -> List[Dict]:
        """
        Searches all past conversations for this user (Semantic).
        """
        # 1. Embed query
        embed_res = requests.post(EMBEDDING_URL, json={"texts": [query]})
        vector = embed_res.json().get("embeddings")[0]

        # 2. Search Qdrant with user_id filter
        res = requests.post(f"{QDRANT_URL}/collections/{MEMORY_COLLECTION}/points/search", json={
            "vector": vector,
            "filter": {
                "must": [{"key": "user_id", "match": {"value": user_id}}]
            },
            "limit": limit,
            "with_payload": True
        })
        
        return [r['payload'] for r in res.json().get("result", [])]
