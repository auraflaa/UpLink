import requests
import time
import json
import sys

SERVER_URL = "http://localhost:6399"
TEST_REPO = "https://github.com/auraflaa/UpLink"
COLLECTION = "rag_pipeline_verify"
USER_ID = "test_engineer_01"
SESSION_ID = f"verify_{int(time.time())}"

# Parse CLI flags:  --viz to include diagram generation
RUN_VIZ = "--viz" in sys.argv

latencies = {}

def timed_request(label: str, method: str, url: str, **kwargs):
    t0 = time.perf_counter()
    res = getattr(requests, method)(url, **kwargs)
    elapsed = (time.perf_counter() - t0) * 1000
    latencies[label] = elapsed
    return res, elapsed

def fmt(ms: float) -> str:
    return f"{ms/1000:.2f}s" if ms >= 1000 else f"{ms:.1f}ms"

def run():
    print("\n[🔬] RAG Pipeline — Full System Verification")
    if RUN_VIZ:
        print("     [--viz mode: diagram generation included]")
    print()

    total_start = time.perf_counter()

    # ── Health ────────────────────────────────────────────────
    r, ms = timed_request("Health", "get", f"{SERVER_URL}/health")
    if r.status_code != 200:
        print(f"[❌] Server unreachable. Is RAG Pipeline running on port 6399?")
        return
    print(f"[✅] Health: {r.json()}  ({fmt(ms)})")

    # ── Pre-analysis status ──────────────────────────────────
    r, ms = timed_request("Status (pre)", "get", f"{SERVER_URL}/status",
        params={"repo_url": TEST_REPO, "collection_name": COLLECTION})
    already_indexed = r.json()['indexed']
    print(f"[*] Pre-analysis index status: {already_indexed}  ({fmt(ms)})")

    # ── Trigger analysis (only if needed) ────────────────────
    if already_indexed:
        print(f"\n[*] Repo already indexed — skipping analysis.")
        latencies["Analyze (total)"] = 0
    else:
        print(f"\n[*] Submitting analysis request for: {TEST_REPO}")
        r, ms = timed_request("Analyze (submit)", "post", f"{SERVER_URL}/analyze",
            json={"repo_url": TEST_REPO, "collection_name": COLLECTION})
        print(f"[✅] Analysis accepted  ({fmt(ms)})")

        print("[*] Polling for indexing completion (max 120s)...")
        poll_start = time.perf_counter()
        indexed = False
        for i in range(24):
            time.sleep(5)
            r = requests.get(f"{SERVER_URL}/status",
                params={"repo_url": TEST_REPO, "collection_name": COLLECTION})
            indexed = r.json().get("indexed", False)
            elapsed_poll = int(time.perf_counter() - poll_start)
            print(f"     [{elapsed_poll}s] indexed={indexed}", end="\r")
            if indexed:
                break

        poll_ms = (time.perf_counter() - poll_start) * 1000
        latencies["Analyze (total)"] = poll_ms
        print(f"\n[{'✅' if indexed else '❌'}] Indexing complete  ({fmt(poll_ms)}){'  ⚠ Timed out' if not indexed else ''}")

    # ── RAG Chat ─────────────────────────────────────────────
    print(f"\n[*] Testing RAG Chat...")
    r, ms = timed_request("Chat (RAG)", "post", f"{SERVER_URL}/chat",
        json={
            "query": "What is the primary purpose of this project?",
            "user_id": USER_ID,
            "session_id": SESSION_ID,
            "collection_name": COLLECTION
        })
    if r.status_code == 200:
        data = r.json()
        src = data['sources']
        print(f"[✅] Chat  ({fmt(ms)})")
        print(f"     {data['answer'][:200]}...")
        print(f"     Sources: {src if src else '⚠ None (check collection has indexed data)'}")
        print(f"     Long-term memory hits: {data['long_term_hits']}")
    else:
        print(f"[❌] Chat failed  ({fmt(ms)}): {r.text}")

    # ── Memory recall ─────────────────────────────────────────
    print(f"\n[*] Testing memory recall...")
    r, ms = timed_request("Chat (memory)", "post", f"{SERVER_URL}/chat",
        json={
            "query": "What did I just ask you?",
            "user_id": USER_ID,
            "session_id": SESSION_ID,
            "collection_name": COLLECTION
        })
    if r.status_code == 200:
        print(f"[✅] Memory recall  ({fmt(ms)})")
        print(f"     {r.json()['answer'][:200]}...")
    else:
        print(f"[❌] Memory failed  ({fmt(ms)}): {r.text}")

    # ── Visualisation (on demand only) ────────────────────────
    if RUN_VIZ:
        print(f"\n[*] Generating Mermaid diagram...")
        r, ms = timed_request("Viz (Mermaid)", "post", f"{SERVER_URL}/viz",
            json={"repo_url": TEST_REPO, "collection_name": COLLECTION})
        if r.status_code == 200:
            data = r.json()
            print(f"[✅] Mermaid generated  ({fmt(ms)}, {data['source_files']} sources)")
            print(data['mermaid'][:400])
        else:
            print(f"[❌] Viz failed  ({fmt(ms)}): {r.text}")
    else:
        print(f"\n[⏭] Viz skipped (run with --viz to include diagram generation)")

    # ── Summary ───────────────────────────────────────────────
    total_ms = (time.perf_counter() - total_start) * 1000
    print("\n" + "─" * 47)
    print(f"  {'Endpoint':<26} {'Latency':>10}  {'':5}")
    print("─" * 47)
    WARN_THRESHOLD_MS = 5000
    for name, ms in latencies.items():
        skip = name == "Analyze (total)" and ms == 0
        warn = "  ⚠" if ms > WARN_THRESHOLD_MS and "Analyze" not in name else ""
        val = "skipped" if skip else fmt(ms)
        print(f"  {name:<26} {val:>10}{warn}")
    print("─" * 47)
    print(f"  {'Total session':<26} {fmt(total_ms):>10}")
    print("─" * 47)
    print("\n[🏁] Verification complete.\n")

if __name__ == "__main__":
    run()
