import requests
import time
import json

SERVER_URL = "http://localhost:6399"
TEST_REPO = "https://github.com/auraflaa/UpLink"
COLLECTION = "rag_pipeline_verify"
USER_ID = "test_engineer_01"
SESSION_ID = f"verify_{int(time.time())}"

def run():
    print("\n[🔬] RAG Pipeline — Full System Verification\n")

    # Health
    try:
        r = requests.get(f"{SERVER_URL}/health")
        assert r.status_code == 200
        print(f"[✅] Health: {r.json()}")
    except Exception as e:
        print(f"[❌] Server unreachable: {e}")
        return

    # Status check (before analysis)
    r = requests.get(f"{SERVER_URL}/status", params={"repo_url": TEST_REPO, "collection_name": COLLECTION})
    print(f"[*] Pre-analysis index status: {r.json()['indexed']}")

    # Trigger analysis
    print(f"\n[*] Submitting analysis request for: {TEST_REPO}")
    r = requests.post(f"{SERVER_URL}/analyze", json={"repo_url": TEST_REPO, "collection_name": COLLECTION})
    print(f"[✅] Analysis accepted: {r.json()['message']}")
    print("[*] Waiting 60s for background analysis to complete...")
    time.sleep(60)

    # Status check (after analysis)
    r = requests.get(f"{SERVER_URL}/status", params={"repo_url": TEST_REPO, "collection_name": COLLECTION})
    indexed = r.json()['indexed']
    print(f"[{'✅' if indexed else '❌'}] Post-analysis index status: {indexed}")

    # RAG Chat
    print(f"\n[*] Testing RAG Chat...")
    r = requests.post(f"{SERVER_URL}/chat", json={
        "query": "What is the primary purpose of this project?",
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "collection_name": COLLECTION
    })
    if r.status_code == 200:
        data = r.json()
        print(f"[✅] Chat Response: {data['answer'][:200]}...")
        print(f"     Sources: {data['sources']}")
        print(f"     Long-term memory hits: {data['long_term_hits']}")
    else:
        print(f"[❌] Chat failed: {r.text}")

    # Memory recall
    print(f"\n[*] Testing memory recall...")
    r = requests.post(f"{SERVER_URL}/chat", json={
        "query": "What did I just ask you?",
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "collection_name": COLLECTION
    })
    if r.status_code == 200:
        print(f"[✅] Memory recall: {r.json()['answer'][:200]}...")
    else:
        print(f"[❌] Memory recall failed: {r.text}")

    # Visualisation
    print(f"\n[*] Testing Mermaid diagram generation...")
    r = requests.post(f"{SERVER_URL}/viz", json={"repo_url": TEST_REPO, "collection_name": COLLECTION})
    if r.status_code == 200:
        mermaid = r.json()['mermaid']
        print(f"[✅] Mermaid generated ({r.json()['source_files']} sources):")
        print(mermaid[:300])
    else:
        print(f"[❌] Viz failed: {r.text}")

    print("\n[🏁] Verification complete.")

if __name__ == "__main__":
    run()
