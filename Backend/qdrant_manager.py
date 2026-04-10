import os
import requests
import uuid

class QdrantDBManager:
    def __init__(self, collection_name="uplink_events", vector_size=384, host=None, port=None):
        """
        Pure REST implementation without the Qdrant Client "python middle man".
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", 6366))
        self.base_url = f"http://{self.host}:{self.port}"
        
        print(f"[*] Communicating directly with Qdrant REST API at {self.base_url}")
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        try:
            res = requests.get(f"{self.base_url}/collections")
            res.raise_for_status()
            collections = res.json().get("result", {}).get("collections", [])
            exists = any(col.get("name") == self.collection_name for col in collections)
            
            if not exists:
                create_payload = {
                    "vectors": {
                        "size": self.vector_size,
                        "distance": "Cosine"
                    }
                }
                requests.put(f"{self.base_url}/collections/{self.collection_name}", json=create_payload).raise_for_status()
                print(f"[*] Created Qdrant collection: {self.collection_name}")
            else:
                print(f"[*] Connected to existing Qdrant collection: {self.collection_name}")
        except requests.exceptions.RequestException as e:
            print(f"[!] Error checking/creating collection: {e}")

    def upsert_vectors(self, points):
        qdrant_points = []
        for pt in points:
            point_id = pt.get("id", str(uuid.uuid4()))
            qdrant_points.append({
                "id": point_id,
                "vector": pt["vector"],
                "payload": pt.get("payload", {})
            })
        
        payload = {"points": qdrant_points}
        url = f"{self.base_url}/collections/{self.collection_name}/points"
        res = requests.put(url, json=payload)
        res.raise_for_status()
        return res.json()

    def search(self, query_vector, limit=5, filter_dict=None):
        url = f"{self.base_url}/collections/{self.collection_name}/points/search"
        payload = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True
        }
        res = requests.post(url, json=payload)
        res.raise_for_status()
        return res.json().get("result", [])

if __name__ == "__main__":
    db = QdrantDBManager()
    print("REST manager ready.")
