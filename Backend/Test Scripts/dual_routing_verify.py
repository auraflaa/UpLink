import requests

RAG_URL = "http://127.0.0.1:6399"
GITHUB_REPO = "https://github.com/auraflaa/UpLink"
JIRA_ISSUE = "https://uplink-test.atlassian.net/browse/UP-456"
COLLECTION = "routing_test_suite"

def test_routing(scenario_name, payload, expected_status):
    print(f"\n[*] Testing: {scenario_name}")
    print(f"    Payload: {payload}")
    try:
        res = requests.post(f"{RAG_URL}/analyze/dual", json=payload)
        code = res.status_code
        data = res.json()
        
        if code == expected_status:
            print(f"    [OK] PASSED! Got expected status {code}.")
            print(f"         RAG Server Reply: {data.get('message', data.get('detail'))}")
        else:
            print(f"    [FAIL] FAILED! Expected {expected_status}, got {code}")
            print(f"         Response: {data}")
    except Exception as e:
        print(f"    [FAIL] Connection error (Server might be offline): {e}")

def run_tests():
    print("="*65)
    print("      UPLINK DUAL-ROUTING OPTIMAL STRATEGY VERIFICATION")
    print("="*65)
    
    # 1. Option A: Both 
    payload_both = {
        "github_url": GITHUB_REPO,
        "jira_url": JIRA_ISSUE,
        "collection_name": COLLECTION
    }
    test_routing("BOTH Sources Provided (Optimal: Parallel Execution)", payload_both, 200)

    # 2. Option B: Only GitHub
    payload_gh_only = {
        "github_url": GITHUB_REPO,
        "collection_name": COLLECTION
    }
    test_routing("ONLY GitHub Provided (Optimal: Process GH, Skip Jira)", payload_gh_only, 200)

    # 3. Option C: Only Jira
    payload_jr_only = {
        "jira_url": JIRA_ISSUE,
        "collection_name": COLLECTION
    }
    test_routing("ONLY Jira Provided (Optimal: Process Jira, Skip GH)", payload_jr_only, 200)

    # 4. Option D: None
    payload_none = {
        "collection_name": COLLECTION
    }
    test_routing("NEITHER Provided (Optimal: Immediate 400 Rejection)", payload_none, 400)

    print("\n" + "="*65)
    print("All routing checks initiated. Note: Background tasks are now processing in parallel.")

if __name__ == "__main__":
    run_tests()
