import requests
import json
import time

# Config
SERVER_URL = "http://localhost:6399"
TEST_REPO = "https://github.com/auraflaa/UpLink"

def test_mr_uplinker_scan():
    print(f"[*] Starting Mr. UpLinker Deep-Scan Test on: {TEST_REPO}")
    
    # 1. Check health
    try:
        health = requests.get(f"{SERVER_URL}/health")
        if health.status_code == 200:
            print("✅ Mr. UpLinker Brain Server is Online.")
        else:
            print("❌ Server is offline. Please start it with 'python server.py'")
            return
    except:
        print("❌ Could not connect to port 6399. Ensure the server is running.")
        return

    # 2. Trigger Analysis
    print("[*] Sending analysis request (this involves LLM agentic scanning)...")
    payload = {
        "repo_url": TEST_REPO,
        "collection_name": "uplink_test_knowlege"
    }
    
    start_time = time.time()
    try:
        res = requests.post(f"{SERVER_URL}/analyze", json=payload, timeout=60)
        res.raise_for_status()
        data = res.json()
        
        duration = time.time() - start_time
        print(f"✅ Success! Mr. UpLinker finished studying the repo in {duration:.2f}s.")
        print(f"📄 Files Analysed: {data.get('file_count')}")
        print(f"🧠 Knowledge stored in: {data.get('collection')}")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Analysis Failed: {e.response.text}")
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_mr_uplinker_scan()
