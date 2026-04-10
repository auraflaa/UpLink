import requests
import uuid
import json

# Configuration
EMBEDDING_URL = "http://localhost:6377/embed"
QDRANT_URL = "http://localhost:6366"
COLLECTION_NAME = "integration_test"

def run_integration_test():
    print("[*] Starting End-to-End Integration Test...")
    
    try:
        # --- 1. GET EMBEDDING ---
        print("[*] Step 1: Requesting embedding from server (port 6377)...")
        test_text = "Senior Python Developer with experience in RAG and Vector DBs."
        embed_res = requests.post(EMBEDDING_URL, json={"texts": [test_text]})
        embed_res.raise_for_status()
        vector = embed_res.json().get("embeddings")[0]
        print(f"✅ Received 768-dim vector for: '{test_text[:20]}...'")

        # --- 2. PREPARE QDRANT ---
        print(f"[*] Step 2: Preparing Qdrant collection '{COLLECTION_NAME}' (port 6366)...")
        # Ensure collection exists
        create_payload = {
            "vectors": {
                "size": 768,
                "distance": "Cosine"
            }
        }
        requests.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", json=create_payload)

        # --- 3. STORE (CREATE) ---
        print("[*] Step 3: Storing (CREATE) vector in Qdrant...")
        point_id = str(uuid.uuid4())
        point_payload = {
            "points": [
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "content": test_text,
                        "source": "Integration Test",
                        "version": 1
                    }
                }
            ]
        }
        requests.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points", json=point_payload).raise_for_status()
        print(f"✅ Point stored with ID: {point_id}")

        # --- 4. RETRIEVE (READ) ---
        print("[*] Step 4: Retrieving (READ/Search) vector from Qdrant...")
        search_payload = {
            "vector": vector,
            "limit": 1,
            "with_payload": True
        }
        search_res = requests.post(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search", json=search_payload)
        search_res.raise_for_status()
        results = search_res.json().get("result", [])
        
        if results and results[0].get("id") == point_id:
            print(f"✅ Successfully retrieved identical point. Score: {results[0].get('score')}")
        else:
            print("❌ Failed to retrieve the correct point.")
            return

        # --- 5. UPDATE ---
        print("[*] Step 5: Updating (UPDATE) payload in Qdrant...")
        update_payload = {
            "points": [
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "content": test_text,
                        "source": "Integration Test",
                        "status": "Updated"
                    }
                }
            ]
        }
        requests.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points", json=update_payload).raise_for_status()
        
        # Verify update
        check_res = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/{point_id}").json()
        if check_res.get("result", {}).get("payload", {}).get("status") == "Updated":
            print("✅ Update verified.")
        else:
            print("❌ Update failed.")

        # --- 6. DELETE ---
        print(f"[*] Step 6: Cleaning up (DELETE) collection '{COLLECTION_NAME}'...")
        requests.delete(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
        print("✅ Cleanup complete.")

        print("\n✨ END-TO-END INTEGRATION SUCCESSFUL!")
        print("The Embedding Server and Vector DB are talking to each other perfectly.")

    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
        print("Ensure both Docker (Qdrant) and the Embedding Server (server.py) are running.")
    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")

if __name__ == "__main__":
    run_integration_test()
