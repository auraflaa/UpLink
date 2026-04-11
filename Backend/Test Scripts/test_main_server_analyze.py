from __future__ import annotations

from main_server_test_helper import (
    DEFAULT_GITHUB_URL,
    DEFAULT_JIRA_URL,
    assert_envelope_shape,
    build_envelope,
    ensure_main_server_running,
    print_header,
    print_json,
    request_json,
    stop_process,
)


def run_scenario(name: str, payload: dict[str, str], source_kind: str) -> None:
    print_header(f"Analyze Scenario: {name}")
    response = request_json(
        "POST",
        "/api/main/v1/workspaces/analyze",
        build_envelope(
            "analyze_workspace",
            payload,
            ui_surface="test.analyze",
            source_kind=source_kind,
        ),
    )
    print_json("Analyze response", response)
    assert_envelope_shape(response)
    if response["meta"]["status"] not in {"accepted", "failed"}:
        raise RuntimeError(f"Unexpected analyze status: {response['meta']['status']}")


def main() -> None:
    started = ensure_main_server_running(auto_start=True)
    try:
        run_scenario("GitHub only", {"github_url": DEFAULT_GITHUB_URL}, "github")
        run_scenario("Jira only", {"jira_url": DEFAULT_JIRA_URL}, "jira")
        run_scenario(
            "GitHub + Jira",
            {"github_url": DEFAULT_GITHUB_URL, "jira_url": DEFAULT_JIRA_URL},
            "dual",
        )
        print_header("Main Server Analyze Test Passed")
    finally:
        stop_process(started)


if __name__ == "__main__":
    main()
