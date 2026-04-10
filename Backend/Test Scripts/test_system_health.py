"""
test_system_health.py — Infrastructure live connection verification.

Tests whether all critical macro-services have successfully booted and are 
accepting TCP connections or responding to health check HTTP routes.
"""

import socket
import requests
import time
from rich.console import Console
from rich.table import Table
import sys

console = Console()

SERVICES = [
    {
        "name": "Qdrant Vector DB",
        "port": 6366,
        "type": "http",
        "url": "http://127.0.0.1:6366/",
    },
    {
        "name": "Embedding Service",
        "port": 6377,
        "type": "http",
        "url": "http://127.0.0.1:6377/health",
    },
    {
        "name": "RAG Intelligence Core",
        "port": 6399,
        "type": "http",
        "url": "http://127.0.0.1:6399/status",
    },
    {
        "name": "Document Parser",
        "port": 8004,
        "type": "http",
        "url": "http://127.0.0.1:8004/status",
    },
    {
        "name": "Event Handler Gateway",
        "port": 8003,
        "type": "tcp",
    },
]

# Scheduler is rarely launched in the automated block if keys are missing, but let's check it.
SERVICES.append({
    "name": "Task Scheduler",
    "port": 8002,
    "type": "tcp",
})

def check_tcp(port: int, timeout: float = 1.0) -> bool:
    """Check if a port is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex(('127.0.0.1', port))
        return result == 0

def check_http(url: str, timeout: float = 2.0) -> tuple[bool, str]:
    """Check if HTTP health route returns 200."""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, "200 OK"
        return False, f"HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, "Connection Refused"

def main():
    console.print("\n[cyan]=================================================[/cyan]")
    console.print("[cyan]  UpLink System Health Verification  [/cyan]")
    console.print("[cyan]=================================================[/cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Service")
    table.add_column("Port", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    all_systems_go = True

    for srv in SERVICES:
        name = srv["name"]
        port = str(srv["port"])
        status = "[red]OFFLINE[/red]"
        details = "Unreachable"

        if srv["type"] == "http":
            is_up, http_msg = check_http(srv["url"])
            if is_up:
                status = "[green]ONLINE[/green]"
                details = http_msg
            else:
                all_systems_go = False
                details = http_msg
        else:
            is_up = check_tcp(srv["port"])
            if is_up:
                status = "[green]ONLINE[/green]"
                details = "TCP Open"
            else:
                all_systems_go = False
                details = "TCP Closed"

        table.add_row(name, port, status, details)

    console.print(table)
    console.print()
    if all_systems_go:
        console.print("[bold green][OK] All Macro-Services are operational![/bold green]\n")
        sys.exit(0)
    else:
        console.print("[bold red][FAIL] One or more services failed to boot.[/bold red]")
        console.print("   Check the terminal window logs spawned by [yellow].\\start_backend.ps1[/yellow] to debug exceptions.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
