import requests
import numpy as np

# Config matches our server port 6377
SERVER_URL = "http://localhost:6377"

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def test_embedding_server():
    print(f"[*] Testing connection to Embedding Server at {SERVER_URL}...")
    
    try:
        # 1. Health Check
        health = requests.get(f"{SERVER_URL}/health")
        health.raise_for_status()
        print(f"[SUCCESS] Server is HEALTHY. Mode: {health.json().get('device')}")

        # 2. Semantic Accuracy Test
        print("[*] Running semantic accuracy check...")
        payload = {
            "texts": [
                "I am an expert in Python and React development.",           # Core text
                "Developing web applications with Python and Javascript.",  # Similar
                "The weather in London is quite rainy today."              # Unrelated
            ]
        }
        
        res = requests.post(f"{SERVER_URL}/embed", json=payload)
        res.raise_for_status()
        
        vecs = res.json().get("embeddings")
        dims = res.json().get("dimensions")
        
        print(f"[SUCCESS] Received embeddings with dimensions: {dims}")
        
        sim_similar = cosine_similarity(vecs[0], vecs[1])
        sim_unrelated = cosine_similarity(vecs[0], vecs[2])
        
        print(f"-> Similarity (Related): {sim_similar:.4f}")
        print(f"-> Similarity (Unrelated): {sim_unrelated:.4f}")
        
        if sim_similar > sim_unrelated:
            print("[SUCCESS] Semantic logic works. Related concepts are closer than unrelated ones.")
        else:
            print("[FAILURE] Semantic check failed.")

    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] CONNECTION ERROR: Could not reach Embedding Server.")
        print(f"   Make sure to run 'python server.py' in 'Backend/Embedding Service'")
    except Exception as e:
        print(f"\n[ERROR] during test: {e}")

if __name__ == "__main__":
    test_embedding_server()
