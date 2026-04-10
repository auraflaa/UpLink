"""
test_rag.py — RAG Pipeline Test Suite

Tests:
  1. Routing validation — correct HTTP responses for all source combinations
  2. Parallel ingestion — BOTH sources accepted simultaneously, no waiting
  3. Chat retrieval — Semantic query against indexed knowledge (requires Qdrant)
"""

import requests
import sys

RAG_URL = "http://127.0.0.1:6399"
GITHUB_REPO = "https://github.com/auraflaa/UpLink"
JIRA_ISSUE = "https://uplink-test.atlassian.net/browse/UP-456"


def _check_server() -> bool:
    try:
        requests.get(RAG_URL, timeout=3)
        return True
    except requests.exceptions.ConnectionError:
        return False


# ------------------------------------------------------------------ #
# TEST 1: Routing validation
# All valid payloads should return 200. Empty payload returns 400.
# No locks, no waiting — each request is processed independently.
# ------------------------------------------------------------------ #
def test_routing() -> bool:
    print("\n" + "="*60)
    print("  TEST 1: Routing Validation")
    print("="*60)

    scenarios = [
        (
            "BOTH Sources (GitHub + Jira, parallel)",
            {"github_url": GITHUB_REPO, "jira_url": JIRA_ISSUE, "collection_name": "test_both"},
            200,
        ),
        (
            "ONLY GitHub",
            {"github_url": GITHUB_REPO, "collection_name": "test_gh_only"},
            200,
        ),
        (
            "ONLY Jira",
            {"jira_url": JIRA_ISSUE, "collection_name": "test_jira_only"},
            200,
        ),
        (
            "NEITHER (should reject with 400)",
            {"collection_name": "test_none"},
            400,
        ),
    ]

    all_passed = True
    for name, payload, expected in scenarios:
        try:
            res = requests.post(f"{RAG_URL}/analyze/dual", json=payload, timeout=5)
            if res.status_code == expected:
                print(f"  [OK] {name} -> {res.status_code}")
            else:
                print(f"  [FAIL] {name}")
                print(f"         Expected {expected}, got {res.status_code}: {res.text[:120]}")
                all_passed = False
        except Exception as e:
            print(f"  [FAIL] {name} -> {e}")
            all_passed = False

    return all_passed


# ------------------------------------------------------------------ #
# TEST 2: Parallel ingestion — same endpoint, same source, back-to-back
# With no locks, both requests should be accepted (200) immediately.
# ------------------------------------------------------------------ #
def test_parallel_acceptance() -> bool:
    print("\n" + "="*60)
    print("  TEST 2: Parallel Acceptance (no lock rejection)")
    print("="*60)

    payload = {"github_url": GITHUB_REPO, "collection_name": "test_parallel"}

    r1 = requests.post(f"{RAG_URL}/analyze/dual", json=payload, timeout=5)
    r2 = requests.post(f"{RAG_URL}/analyze/dual", json=payload, timeout=5)

    if r1.status_code == 200 and r2.status_code == 200:
        print(f"  [OK] Both back-to-back requests accepted (200/200). Parallel processing active.")
        return True
    else:
        print(f"  [FAIL] Expected 200/200, got {r1.status_code}/{r2.status_code}")
        return False


# ------------------------------------------------------------------ #
# TEST 3: Chat retrieval (requires Qdrant on port 6366)
# ------------------------------------------------------------------ #
def test_chat(query: str = "What is the UpLink project designed to do?") -> bool:
    print("\n" + "="*60)
    print("  TEST 3: Semantic Chat Retrieval")
    print("="*60)
    print(f"  Query: '{query}'")

    payload = {
        "query": query,
        "collection_name": "project_knowledge",
        "session_id": "test_session_001",
        "user_id": "test_user",
    }

    try:
        res = requests.post(f"{RAG_URL}/chat", json=payload, timeout=30)
        if res.status_code == 200:
            data = res.json()
            answer = data.get("answer", "")
            sources = list(set(data.get("sources", [])))
            telemetry = data.get("telemetry", {})
            print(f"\n  UpLink AI: {answer}")
            print(f"\n  Sources: {sources or 'None (general knowledge)'}")
            print(f"  Retrieval: {telemetry.get('vector_retrieval_ms', 0):.1f}ms  |  Generation: {telemetry.get('llm_generation_ms', 0):.1f}ms")
            print(f"\n  [OK] Chat test passed.")
            return True
        elif res.status_code == 500 and "6366" in res.text:
            print(f"  [SKIP] Qdrant offline (port 6366). Start with: docker-compose up -d")
            return None
        else:
            print(f"  [FAIL] {res.status_code}: {res.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  [FAIL] RAG server offline.")
        return False


if __name__ == "__main__":
    print("="*60)
    print("  UpLink RAG Pipeline Test Suite")
    print("="*60)

    if not _check_server():
        print("\n[CRITICAL] RAG server not running on port 6399.")
        print("  Start it: python 'Backend/RAG Pipeline/server.py'")
        sys.exit(1)

    print(f"\n[OK] RAG server online at {RAG_URL}")

    test_routing()
    test_parallel_acceptance()
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    test_chat(query or "What is the UpLink project designed to do?")

    print("\n" + "="*60)
    print("  Tests complete.")
    print("="*60)
