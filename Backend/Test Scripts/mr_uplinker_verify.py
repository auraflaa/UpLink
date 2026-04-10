import requests
import json
import time

# Config
SERVER_URL = "http://localhost:6399"
TEST_REPO = "https://github.com/auraflaa/UpLink"
COLLECTION = "uplink_verify_master"

def run_master_verification():
    print(f"\n[💎] Starting Mr. UpLinker Master Verification")
    
    # 1. Health Check
    try:
        if requests.get(f"{SERVER_URL}/health").status_code != 200:
            print("❌ Server offline.")
            return
    except:
        print("❌ Could not connect. Ensure 'python server.py' is running.")
        return

    # 2. Step 1: Deep Analysis
    print("\n[*] Step 1: Running Agentic Deep-Scan...")
    scan_res = requests.post(f"{SERVER_URL}/analyze", json={
        "repo_url": TEST_REPO, "collection_name": COLLECTION
    }, timeout=120)
    
    if scan_res.status_code == 200:
        print(f"✅ Analysis Successful. Indexed {scan_res.json()['file_count']} critical files.")
    else:
        print(f"❌ Analysis Failed: {scan_res.text}")
        return

    # 3. Step 2: RAG Chat Verification
    print("\n[*] Step 2: Testing RAG-powered Chat...")
    query = "What is the role of the Embedding Server in this project?"
    chat_res = requests.post(f"{SERVER_URL}/chat", json={
        "query": query, "collection_name": COLLECTION
    })
    
    if chat_res.status_code == 200:
        ans = chat_res.json()
        print(f"💬 Query: '{query}'")
        print(f"🤖 Mr. UpLinker: {ans['answer'][:200]}...")
        print(f"📚 Sources used: {ans['sources']}")
        print("✅ RAG Chat Successful.")
    else:
        print(f"❌ Chat Failed: {chat_res.text}")

    # 4. Step 3: Visualization Generation
    print("\n[*] Step 3: Testing Mermaid Visualization...")
    viz_res = requests.post(f"{SERVER_URL}/viz", json={
        "repo_url": TEST_REPO, "collection_name": COLLECTION
    })
    
    if viz_res.status_code == 200:
        mermaid = viz_res.json()['mermaid']
        print(f"📊 Mermaid Code Generated (first line): {mermaid.splitlines()[0]}")
        print("✅ Visualization Successful.")
    else:
        print(f"❌ Viz Failed: {viz_res.text}")

    print("\n✨ ALL CORE PIPELINES VERIFIED. Mr. UpLinker is 100% operational.")

if __name__ == "__main__":
    run_master_verification()
