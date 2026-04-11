from __future__ import annotations

import time

from main_server_test_helper import (
    DEFAULT_GITHUB_URL,
    assert_envelope_shape,
    build_envelope,
    ensure_main_server_running,
    print_header,
    print_json,
    request_json,
    stop_process,
)


def _prepare_workspace() -> str:
    analyze = request_json(
        "POST",
        "/api/main/v1/workspaces/analyze",
        build_envelope(
            "analyze_workspace",
            {"github_url": DEFAULT_GITHUB_URL},
            ui_surface="test.visualization.bootstrap",
            source_kind="github",
        ),
    )
    assert_envelope_shape(analyze)
    workspace_id = analyze["data"].get("workspace_id") or analyze["meta"].get("workspace_id")
    if not workspace_id:
        raise RuntimeError("Analyze response did not include a workspace_id.")
    return str(workspace_id)


def main() -> None:
    print_header("UpLink Main Server Visualization Test")
    started = ensure_main_server_running(auto_start=True)
    try:
        workspace_id = _prepare_workspace()
        time.sleep(2)

        response = request_json(
            "POST",
            "/api/main/v1/workspaces/visualization",
            build_envelope(
                "load_visualization",
                {"workspace_id": workspace_id},
                workspace_id=workspace_id,
                ui_surface="test.visualization",
                source_kind="github",
            ),
        )
        print_json("Visualization response", response)
        assert_envelope_shape(response)

        data = response["data"]
        if "graph" not in data or "content" not in data:
            raise RuntimeError("Visualization response is missing graph/content payloads.")
        if not isinstance(data["graph"].get("nodes", []), list):
            raise RuntimeError("Visualization graph.nodes is not a list.")

        print_header("Main Server Visualization Test Passed")
    finally:
        stop_process(started)


if __name__ == "__main__":
    main()
