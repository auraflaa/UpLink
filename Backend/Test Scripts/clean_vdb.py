import os
import requests
import sys
from dotenv import load_dotenv

# Load environment logic from current or parent dir
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'RAG Pipeline', '.env'))

QDRANT_PORT = os.getenv("QDRANT_PORT", "6366")
BASE_URL = f"http://127.0.0.1:{QDRANT_PORT}"

def clean_vdb(force=False):
    print(f"\n[🧹] UpLink VDB Cleaner — Targeting: {BASE_URL}")
    
    try:
        # 1. Fetch all collections
        response = requests.get(f"{BASE_URL}/collections", timeout=5)
        response.raise_for_status()
        collections = response.json().get("result", {}).get("collections", [])
        
        if not collections:
            print("[*] VDB is already empty. No collections found.")
            return

        print(f"[*] Found {len(collections)} collections.")
        
        for col in collections:
            name = col['name']
            
            if not force:
                confirm = input(f"    Delete collection '{name}'? (y/N): ")
                if confirm.lower() != 'y':
                    print(f"    [SKIP] {name}")
                    continue
            
            # 2. Delete the collection
            print(f"    [DELETE] {name}...", end=" ", flush=True)
            del_resp = requests.delete(f"{BASE_URL}/collections/{name}")
            if del_resp.status_code == 200:
                print("DONE")
            else:
                print(f"FAILED ({del_resp.status_code})")
                
        print("\n[✅] Cleanup process finished.")

    except Exception as e:
        print(f"\n[❌] Error connecting to Qdrant: {e}")
        print("     Ensure Qdrant is running (check 'uplink_qdrant' container).")

if __name__ == "__main__":
    force_mode = "--all" in sys.argv or "--force" in sys.argv
    clean_vdb(force=force_mode)
