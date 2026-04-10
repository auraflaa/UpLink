import requests
import uuid
import time

# Config matches our docker-compose port 6366
QDRANT_HOST = "localhost"
QDRANT_PORT = 6366
BASE_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"

def test_vdb():
    print(f"[*] Testing connection to Qdrant at {BASE_URL}...")
    
    try:
        # 1. Check health
        health = requests.get(f"{BASE_URL}/healthz")
        health.raise_for_status()
        print("✅ Qdrant service is HEALTHY.")

        # 2. Check collections
        col_res = requests.get(f"{BASE_URL}/collections")
        col_res.raise_for_status()
        print(f"✅ Connection successful. Current collections: {col_res.json().get('result', {}).get('collections', [])}")

        # 3. Create a temporary 'test' collection
        test_col = "connection_test"
        print(f"[*] Creating temporary collection '{test_col}'...")
        create_payload = {
            "vectors": {
                "size": 4, # Small for testing
                "distance": "Cosine"
            }
        }
        requests.put(f"{BASE_URL}/collections/{test_col}", json=create_payload)

        # 4. Insert dummy vector
        print("[*] Inserting test vector...")
        point_id = str(uuid.uuid4())
        point_payload = {
            "points": [
                {
                    "id": point_id,
                    "vector": [0.1, 0.2, 0.3, 0.4],
                    "payload": {"test": "success"}
                }
            ]
        }
        requests.put(f"{BASE_URL}/collections/{test_col}/points", json=point_payload).raise_for_status()

        # 5. Search
        print("[*] Running test search...")
        search_payload = {
            "vector": [0.1, 0.2, 0.3, 0.4],
            "limit": 1
        }
        search_res = requests.post(f"{BASE_URL}/collections/{test_col}/points/search", json=search_payload)
        search_res.raise_for_status()
        
        match = search_res.json().get("result", [])
        if match and match[0].get("id") == point_id:
            print("✨ VDB FULL ROUND-TRIP SUCCESSFUL! Insertion and Search work.")
        else:
            print("❌ Search failed to find the test vector.")

        # 6. Cleanup
        print(f"[*] Cleaning up temporary collection '{test_col}'...")
        requests.delete(f"{BASE_URL}/collections/{test_col}")
        print("✅ Cleanup complete.")

    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: Could not reach Qdrant.")
        print("   Make sure Docker Desktop is RUNNING and you've run 'docker-compose up -d' in 'Backend/Qdrant DB'")
    except Exception as e:
        print(f"\n❌ ERROR during test: {e}")

if __name__ == "__main__":
    test_vdb()
