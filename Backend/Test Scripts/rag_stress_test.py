"""
rag_stress_test.py — RAG Pipeline Load & Stress Test Suite

Tests (no locks, pure parallel architecture):
  1. Throughput burst    — 20 simultaneous dual-ingestion requests
  2. Sustained load      — 50 sequential rapid-fire requests, measures req/sec
  3. Validation speed    — 30 concurrent bad payloads, measures rejection latency
  4. Stability check     — Server health after heavy load (does it stay responsive?)
"""

import concurrent.futures
import statistics
import sys
import time

import requests

RAG_URL = "http://127.0.0.1:6399"
GITHUB_REPO = "https://github.com/auraflaa/UpLink"
JIRA_ISSUE = "https://uplink-test.atlassian.net/browse/UP-456"
COLLECTION = "stress_test_suite"


def _fire(method: str, endpoint: str, payload=None, params=None) -> tuple[int, float]:
    """Fire a single request, return (status_code, latency_ms). Returns (-1, 0) on error."""
    url = f"{RAG_URL}{endpoint}"
    try:
        t0 = time.perf_counter()
        if method == "POST":
            res = requests.post(url, json=payload, timeout=8)
        else:
            res = requests.get(url, params=params, timeout=8)
        latency = (time.perf_counter() - t0) * 1000
        return res.status_code, latency
    except requests.exceptions.Timeout:
        return -1, 8000.0
    except requests.exceptions.ConnectionError:
        return -2, 0.0


def _print_latency_stats(label: str, latencies: list[float]) -> None:
    if not latencies:
        print(f"  {label}: no data")
        return
    print(f"  {label}: "
          f"min={min(latencies):.1f}ms  "
          f"avg={statistics.mean(latencies):.1f}ms  "
          f"p95={sorted(latencies)[int(len(latencies)*0.95)]:.1f}ms  "
          f"max={max(latencies):.1f}ms")


# ------------------------------------------------------------------ #
# TEST 1: Throughput Burst (20 simultaneous dual-ingestion requests)
# All should return 200 — no locks means no 409s.
# ------------------------------------------------------------------ #
def test_throughput_burst() -> bool:
    print("\n" + "="*65)
    print("  TEST 1: Throughput Burst (20 concurrent dual-ingestion)")
    print("="*65)

    payload = {"github_url": GITHUB_REPO, "jira_url": JIRA_ISSUE, "collection_name": COLLECTION}

    t_start = time.time()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(_fire, "POST", "/analyze/dual", payload) for _ in range(20)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    elapsed = time.time() - t_start
    statuses = [r[0] for r in results]
    latencies = [r[1] for r in results if r[0] > 0]

    ok = statuses.count(200)
    offline = statuses.count(-2)
    timeouts = statuses.count(-1)

    print(f"  Completed 20 requests in {elapsed:.2f}s")
    print(f"  HTTP 200 (Accepted): {ok}/20")
    if offline:  print(f"  Offline:             {offline}/20")
    if timeouts: print(f"  Timeouts:            {timeouts}/20")
    _print_latency_stats("Response latency", latencies)

    if offline > 0:
        print("  [FAIL] Server is offline.")
        return False
    if ok == 20:
        print("  [OK] All 20 requests accepted — lockless parallel architecture confirmed.")
        return True
    else:
        print(f"  [WARN] {20-ok} requests were not accepted. Check server logs.")
        return False


# ------------------------------------------------------------------ #
# TEST 2: Sustained Load (50 sequential rapid requests, req/sec metric)
# ------------------------------------------------------------------ #
def test_sustained_load() -> bool:
    print("\n" + "="*65)
    print("  TEST 2: Sustained Load (50 sequential rapid requests)")
    print("="*65)

    payload = {"github_url": GITHUB_REPO, "collection_name": COLLECTION}
    latencies = []
    statuses = []

    t_start = time.time()
    for i in range(50):
        code, lat = _fire("POST", "/analyze/dual", payload)
        statuses.append(code)
        if code > 0:
            latencies.append(lat)

    elapsed = time.time() - t_start
    ok = statuses.count(200)
    rps = 50 / elapsed

    print(f"  Completed 50 requests in {elapsed:.2f}s  ({rps:.1f} req/sec)")
    print(f"  HTTP 200 (Accepted): {ok}/50")
    _print_latency_stats("Response latency", latencies)

    if ok == 50:
        print(f"  [OK] Server handled sustained load at {rps:.1f} req/sec with 0 drops.")
        return True
    else:
        print(f"  [WARN] {50 - ok} requests failed. May be validation rejections or server errors.")
        return False


# ------------------------------------------------------------------ #
# TEST 3: Validation Speed (30 concurrent bad payloads)
# Empty payloads should be rejected instantly with 400.
# ------------------------------------------------------------------ #
def test_validation_speed() -> bool:
    print("\n" + "="*65)
    print("  TEST 3: Validation Speed (30 concurrent bad payloads)")
    print("="*65)

    bad_payload = {"collection_name": COLLECTION}  # no github or jira url

    t_start = time.time()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as pool:
        futures = [pool.submit(_fire, "POST", "/analyze/dual", bad_payload) for _ in range(30)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    elapsed = time.time() - t_start
    statuses = [r[0] for r in results]
    latencies = [r[1] for r in results if r[0] > 0]

    bad_count = statuses.count(400)
    print(f"  Completed 30 bad requests in {elapsed:.2f}s")
    print(f"  HTTP 400 (Correctly rejected): {bad_count}/30")
    _print_latency_stats("Rejection latency", latencies)

    if bad_count == 30:
        print("  [OK] Validation layer correctly rejected all bad payloads under load.")
        return True
    else:
        print(f"  [FAIL] {30 - bad_count} bad requests were not rejected properly.")
        return False


# ------------------------------------------------------------------ #
# TEST 4: Stability Check — is the server still healthy after load?
# ------------------------------------------------------------------ #
def test_stability() -> bool:
    print("\n" + "="*65)
    print("  TEST 4: Post-Load Stability Check")
    print("="*65)

    # Simple GET to status endpoint
    code, lat = _fire("GET", "/status", params={"source_url": GITHUB_REPO, "collection_name": COLLECTION})

    if code == 200:
        print(f"  [OK] Server is stable and responding after load. Latency: {lat:.1f}ms")
        return True
    elif code == -2:
        print("  [FAIL] Server crashed or became unreachable after load test.")
        return False
    else:
        print(f"  [WARN] Unexpected status {code} after load. Server may be degraded.")
        return False


# ------------------------------------------------------------------ #
# Main
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    print("="*65)
    print("  UpLink RAG Pipeline — Stress Test Suite")
    print("="*65)

    # Pre-flight
    code, _ = _fire("GET", "/status", params={"source_url": GITHUB_REPO, "collection_name": "ping"})
    if code == -2:
        print("\n[CRITICAL] RAG server is offline on port 6399. Cannot run stress tests.")
        sys.exit(1)

    print(f"\n[OK] RAG server is online. Starting stress tests...\n")

    results = []
    results.append(("Throughput Burst",   test_throughput_burst()))
    results.append(("Sustained Load",     test_sustained_load()))
    results.append(("Validation Speed",   test_validation_speed()))
    results.append(("Post-Load Stability", test_stability()))

    print("\n" + "="*65)
    print("  STRESS TEST SUMMARY")
    print("="*65)
    passed = sum(1 for _, r in results if r is True)
    for name, result in results:
        symbol = "[OK]" if result is True else "[SKIP]" if result is None else "[FAIL]"
        print(f"  {symbol}  {name}")

    print(f"\n  {passed}/{len(results)} tests passed.")
    print("="*65)
