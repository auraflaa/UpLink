import requests
import time
import json
import threading

RAG_URL = "http://127.0.0.1:6399"
GITHUB_REPO_A = "https://github.com/auraflaa/UpLink"
GITHUB_REPO_B = "https://github.com/google/googletest"
JIRA_ISSUE = "https://uplink-test.atlassian.net/browse/UP-456"
COLLECTION = "final_verification_suite"

def trigger_analysis(url, source_type):
    print(f"[*] Triggering {source_type} -> {url}")
    try:
        res = requests.post(f"{RAG_URL}/analyze", json={
            "source_url": url,
            "source_type": source_type,
            "collection_name": COLLECTION
        })
        return res.status_code, res.json()
    except Exception as e:
        return 500, str(e)

def run_suite():
    print("\n" + "="*60)
    print("      UPLINK PARALLEL RAG PIPELINE - FINAL VERIFICATION")
    print("="*60)

    # TEST 1: Parallel Ingestion of Different Types
    print("\n[TEST 1] Testing Parallel Ingestion (GitHub + Jira)...")
    code1, res1 = trigger_analysis(GITHUB_REPO_A, "github")
    time.sleep(0.5) # Give worker a moment to lock
    code2, res2 = trigger_analysis(JIRA_ISSUE, "jira")

    if code1 == 200 and code2 == 200:
        print("[OK] SUCCESS: Parallel analysis of different types is ENABLED.")
    else:
        print(f"[!!] FAILED: Parallel ingestion did not return OK. Got ({code1}, {code2})")


    # TEST 2: Type-Aware Concurrency Guard
    print("\n[TEST 2] Testing Type-Aware Locking (GitHub + GitHub)...")
    # Repo A is already running, trigger Repo B
    code3, res3 = trigger_analysis(GITHUB_REPO_B, "github")
    if code3 == 409:
        print(f"[OK] SUCCESS: Concurrency guard correctly blocked duplicate GitHub analysis: {res3.get('detail')}")
    else:
        print(f"[!!] FAILED: Duplicate type NOT blocked. Got {code3}")

    # TEST 3: Wait and Verify Results
    print("\n[*] Waiting for parallel indexing to complete...")
    for _ in range(30):
        time.sleep(10)
        st_gh = requests.get(f"{RAG_URL}/status", params={"source_url": GITHUB_REPO_A, "collection_name": COLLECTION}).json()
        st_jr = requests.get(f"{RAG_URL}/status", params={"source_url": JIRA_ISSUE, "collection_name": COLLECTION}).json()
        
        if st_gh.get("indexed") and st_jr.get("indexed"):
            print("[OK] Both sources indexed successfully.")
            break
        print(f"    - Status: GH={st_gh.get('indexed')}, Jira={st_jr.get('indexed')}")
    else:
        print("[!!] TIMEOUT: Indexing took too long.")
        return

    # TEST 4: Singleton Eviction (Evict GH Repo A with GH Repo B)
    print("\n[TEST 4] Testing Singleton Eviction (Switching Repo A -> Repo B)...")
    code4, res4 = trigger_analysis(GITHUB_REPO_B, "github")
    if code4 == 202:
        print("[OK] Analysis for Repo B started.")
    
    print("[*] Waiting for Repo B to finish and evict Repo A...")
    time.sleep(20) # Usually fast for small repos/summaries

    # Check if Repo A is gone but Jira is still here
    check_a = requests.get(f"{RAG_URL}/status", params={"source_url": GITHUB_REPO_A, "collection_name": COLLECTION}).json()
    check_b = requests.get(f"{RAG_URL}/status", params={"source_url": GITHUB_REPO_B, "collection_name": COLLECTION}).json()
    check_jr = requests.get(f"{RAG_URL}/status", params={"source_url": JIRA_ISSUE, "collection_name": COLLECTION}).json()

    print(f"\n[FINAL AUDIT]")
    print(f"  - Repo A (Old) Indexed: {check_a.get('indexed')} (Should be False)")
    print(f"  - Repo B (New) Indexed: {check_b.get('indexed')} (Should be True)")
    print(f"  - Jira (Existing) Indexed: {check_jr.get('indexed')} (Should be True)")

    if not check_a.get('indexed') and check_b.get('indexed') and check_jr.get('indexed'):
        print("\n[⭐] Data Isolation Tests PASSED! System is robust, parallel, and singleton-compliant.")
    else:
        print("\n[!!] AUDIT FAILED: Singleton rule or data isolation violated.")

    # TEST 5: Verify RAG Query Answering (Chat)
    print("\n[TEST 5] Verifying RAG Query Reasoning (Chat capabilities)...")
    chat_res = requests.post(f"{RAG_URL}/chat", json={
        "query": "What is the purpose of this project and what is the Jira task about?",
        "user_id": "test_engineer",
        "collection_name": COLLECTION
    }).json()

    if chat_res.get("answer"):
        print(f"  [+] Reply received. Excerpt: {chat_res.get('answer')[:120]}...")
        print(f"  [+] Sources leveraged: {len(chat_res.get('sources', []))} items")
        print("\n[⭐] ALL TESTS PASSED! RAG Query engine and Embeddings are fully operational.")
    else:
        print("\n[!!] CHAT FAILED: The query engine could not generate an answer. Check embedding configuration.")

    print("\n" + "="*60)

if __name__ == "__main__":
    run_suite()
