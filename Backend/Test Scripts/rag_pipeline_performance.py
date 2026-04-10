import requests
import time
import json
import sys
import concurrent.futures

# Use 127.0.0.1 to avoid Windows localhost resolution lag
SERVER_URL = "http://127.0.0.1:6399"
TEST_REPO = "https://github.com/auraflaa/UpLink"
COLLECTION = "rag_perf_test"
USER_ID = "stress_tester"
SESSION_ID = f"sim_{int(time.time())}"

def print_box(text, style="="):
    print(f"\n{style * 60}\n {text}\n{style * 60}")

def measure_request(name, method, endpoint, **kwargs):
    t0 = time.perf_counter()
    url = f"{SERVER_URL}{endpoint}"
    try:
        r = getattr(requests, method)(url, timeout=60, **kwargs)
        elapsed = (time.perf_counter() - t0) * 1000
        return r, elapsed
    except Exception as e:
        return None, 0

def run_performance_audit():
    print_box("SCENARIO 1: INGESTION SEGMENT ANALYSIS", "=")
    
    # 1. Clear previous test data if any
    requests.post(f"{SERVER_URL}/analyze", json={"repo_url": TEST_REPO, "collection_name": COLLECTION})
    
    print(f"[*] Analyzing: {TEST_REPO}")
    print("[*] Waiting for background indexing...")
    
    telemetry = {}
    for i in range(24):
        time.sleep(5)
        r, _ = measure_request("Status", "get", "/status", params={"repo_url": TEST_REPO, "collection_name": COLLECTION})
        if r and r.json().get("indexed"):
            tel = r.json().get("telemetry", {})
            if tel.get('summarization_ms'):  # Ensure we have the NEW telemetry
                telemetry = tel
                break
            else:
                print(f"[*] Analysis in progress... (Step {i+1}/24)")
            
    if not telemetry:
        print("[ERROR] Ingestion failed or NEW telemetry didn't arrive. (Old index might be interfering).")
    else:
        print("\n[📊] INGESTION BREAKDOWN:")
        print(f"  - Tree Scan:        {telemetry.get('tree_scan_ms', 0):>8.1f}ms")
        print(f"  - LLM Selection:    {telemetry.get('file_selection_ms', 0):>8.1f}ms")
        print(f"  - Summarization:    {telemetry.get('summarization_ms', 0):>8.1f}ms")
        print(f"  - Vector Indexing:  {telemetry.get('indexing_ms', 0):>8.1f}ms")
        print(f"  {'─' * 40}")
        print(f"  - TOTAL INGESTION:  {telemetry.get('total_ingestion_ms', 0)/1000:>8.2f}s")


def run_chat_simulation():
    print_box("SCENARIO 2: MULTI-TURN CHAT SIMULATION", "=")
    
    script = [
        "What are the main backend components in this project?",
        "How is the RAG Pipeline connected to the GitHub Scanner?",
        "Can you explain the summary generation logic in agent.py?",
        "What did I just ask you about agent.py?",
        "Tell me about the Qdrant configuration."
    ]
    
    total_latencies = []
    
    for i, query in enumerate(script):
        print(f"\n[Turn {i+1}] User: {query}")
        r, wall_ms = measure_request(f"Turn {i+1}", "post", "/chat", json={
            "query": query,
            "user_id": USER_ID,
            "session_id": SESSION_ID,
            "collection_name": COLLECTION
        })
        
        if r and r.status_code == 200:
            data = r.json()
            answer = data.get('answer') or "Error: AI returned empty response."
            tel = data.get("telemetry", {})
            print(f"🤖 assistant: {answer[:100]}...")
            print(f"    [⏱ Segments]: Embed:{tel.get('embedding_ms',0):.0f}ms | Hist:{tel.get('memory_history_ms',0):.0f}ms | L-Term:{tel.get('memory_longterm_ms',0):.0f}ms")
            print(f"    [⏱ Segments]: Search:{tel.get('vector_search_ms',0):.0f}ms | LLM:{tel.get('llm_generation_ms',0):.0f}ms | Save:{tel.get('memory_save_ms',0):.0f}ms")
            print(f"    [⏱ Total]: {wall_ms/1000:.2f}s (Telemetry Total: {tel.get('total_overall_ms',0)/1000:.2f}s)")
            total_latencies.append(wall_ms)
        else:
            print(f"[ERROR] Request failed.")
            
    avg = sum(total_latencies)/len(total_latencies) if total_latencies else 0
    print(f"\n[📈] Chat Statistics: Avg: {avg/1000:.2f}s | Max: {max(total_latencies or [0])/1000:.2f}s")


def run_stress_test():
    print_box("SCENARIO 3: CONCURRENCY STRESS TEST", "=")
    print("[*] Hammering /chat with 5 parallel queries...")
    
    queries = [
        "Explain the whole architecture.",
        "List all dependencies.",
        "How do we handle memory?",
        "What is the embedding port?",
        "Summarize server.py"
    ]
    
    def hit_chat(q):
        t0 = time.perf_counter()
        requests.post(f"{SERVER_URL}/chat", json={
            "query": q, "user_id": "stress_user", "session_id": "stress", "collection_name": COLLECTION
        })
        return (time.perf_counter() - t0) * 1000

    t_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(hit_chat, queries))
    
    t_total = (time.perf_counter() - t_start) * 1000
    print(f"\n[🔥] Result: {len(results)} queries finished in {t_total/1000:.2f}s")
    print(f"     Average parallel latency: {sum(results)/len(results)/1000:.2f}s")


if __name__ == "__main__":
    try:
        # Check health with 127.0.0.1 first
        r, ms = measure_request("Health Check", "get", "/health")
        if not r:
            print("[ERROR] Server not responding on 127.0.0.1:6399. Try starting server.py.")
            sys.exit(1)
        
        print(f"[OK] Connected to Backend. Health check (127.0.0.1): {ms:.1f}ms")
        if ms > 500:
            print("     [WARN] WARNING: Local networking is slow. Check for proxy/VPN interference.")

        run_performance_audit()
        run_chat_simulation()
        run_stress_test()
        
        print_box("PERFORMANCE ANALYSIS COMPLETE", "*")
    except KeyboardInterrupt:
        print("\n[ABORT] Test aborted.")
