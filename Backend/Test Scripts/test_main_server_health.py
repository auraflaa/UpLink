from __future__ import annotations

from main_server_test_helper import (
    assert_envelope_shape,
    ensure_main_server_running,
    print_header,
    print_json,
    request_json,
    stop_process,
)


def main() -> None:
    print_header("UpLink Main Server Health Test")
    started = ensure_main_server_running(auto_start=True)
    try:
        health = request_json("GET", "/health")
        print_json("Health response", health)

        dependencies = request_json("GET", "/dependencies")
        print_json("Dependencies response", dependencies)

        if health.get("status") != "healthy":
            raise RuntimeError("Main Server health endpoint did not report healthy status.")
        if "dependencies" not in dependencies:
            raise RuntimeError("Dependencies endpoint did not include dependency data.")

        print_header("Main Server Health Test Passed")
    finally:
        stop_process(started)


if __name__ == "__main__":
    main()
