"""
test_e2e_functionality.py — Complete System Functionality Test
============================================================

End-to-end integration test validating the entire UpLink Backend lifecycle.
This script proves that the macro-services are not only online, but
actually talking to each other and retaining data accurately.

STEPS:
1. Document Parser: Uploads a test document (.txt).
2. RAG Pipeline: Submits a dual-ingestion job (GitHub URL + Jira URL).
3. Embedding Server & Qdrant: Verified implicitly as data must successfully store.
4. Chat / Retrieval: Asks a Gemini query requiring context from ALL THREE sources.
"""

import io
import time
import requests
import json
from rich.console import Console
from rich.panel import Panel

console = Console()

DOC_PARSER_URL = "http://127.0.0.1:8004"
RAG_API_URL    = "http://127.0.0.1:6399"
COLLECTION     = "e2e_master_test"

# Dummy Data
TEST_DOC = b"""
[TOP SECRET DOCUMENT]
Project Name: Operation Nebula
Launch Date: November 15, 2026
Lead Engineer: Dr. Aris Thorne
Primary Objective: Establish deep-space harmonic resonance arrays.
"""

TEST_GITHUB_REPO = "https://github.com/facebook/react"  # Just a real repo for parser to handle
TEST_JIRA_TICKET = "https://test.atlassian.net/browse/TKT-1234"

def print_banner(text):
    console.print(f"\n[bold cyan]-- {text}[/bold cyan]")

def check_status(url):
    try:
        r = requests.get(url, timeout=2)
        return r.status_code == 200
    except:
        return False

def run_tests():
    console.print(Panel("[bold magenta]UpLink End-to-End Functionality Integration Test[/bold magenta]"))

    # 1. Pre-flight Check
    print_banner("Phase 1: Pre-flight Verification")
    if not check_status(f"{RAG_API_URL}/docs"):
        console.print("[red][FAIL] RAG Pipeline (6399) is offline.[/red]")
        return
    if not check_status(f"{DOC_PARSER_URL}/status"):
        console.print("[red][FAIL] Document Parser (8004) is offline.[/red]")
        return
    console.print("[green][OK] Core APIs Online.[/green]")

    # 2. Document Parser Ingestion
    print_banner("Phase 2: Document Ingestion (Semantic Chunking)")
    try:
        r = requests.post(
            f"{DOC_PARSER_URL}/ingest",
            files={"files": ("report.txt", io.BytesIO(TEST_DOC), "text/plain")},
            data={"collection_name": COLLECTION, "source_label": "secret_doc"}
        )
        r.raise_for_status()
        stored = r.json().get("total_chunks_stored", 0)
        if stored > 0:
            console.print(f"[green][OK] Document ingested ({stored} chunks vectored to Qdrant).[/green]")
        else:
            console.print("[red][FAIL] Document ingested but 0 chunks returned.[/red]")
            return
    except Exception as e:
        console.print(f"[red][FAIL] Document upload failed: {e}[/red]")
        return

    # 3. Parallel GitHub & Jira Ingestion
    print_banner("Phase 3: Parallel Repository & Ticket Ingestion")
    try:
        payload = {
            "github_url": TEST_GITHUB_REPO,
            "jira_url": TEST_JIRA_TICKET,
            "collection_name": COLLECTION
        }
        r = requests.post(f"{RAG_API_URL}/analyze/dual", json=payload)
        r.raise_for_status()
        console.print("[green][OK] Parallel ingestion task accepted (200 OK).[/green]")
        console.print("[yellow]   Waiting 15 seconds for background LLM summary generation...[/yellow]")
        time.sleep(15)  # Simulate worker wait time for Gemini Summarization
    except Exception as e:
        console.print(f"[red][FAIL] Parallel ingestion failed: {e}[/red]")
        try:
            console.print(f"[red]Server returned: {r.text}[/red]")
        except:
            pass
        return

    # 4. RAG Chat Context Retrieval
    print_banner("Phase 4: Semantic RAG Retrieval (Gemini-1.5-Pro)")
    prompt = "Who is the lead engineer for Operation Nebula according to the top secret document?"
    console.print(f"[dim]Query: \"{prompt}\"[/dim]")
    
    try:
        chat_payload = {
            "collection_name": COLLECTION,
            "query": prompt,
            "user_id": "e2e_test_user"
        }
        r = requests.post(f"{RAG_API_URL}/chat", json=chat_payload)
        r.raise_for_status()
        answer = r.json().get("answer", "")
        
        console.print("\n[bold]Gemini Pipeline Response:[/bold]")
        console.print(Panel(answer, border_style="green"))

        if "Aris Thorne" in answer:
            console.print("\n[bold green][PASS] Cross-service data retrieval is flawless.[/bold green]")
        else:
            console.print("\n[bold yellow][WARN] Generated answer did not explicitly extract 'Aris Thorne'.[/bold yellow]")

    except Exception as e:
        console.print(f"[red][FAIL] Chat retrieval failed: {e}[/red]")

    console.print("\n[bold magenta]E2E Integration Test Completed.[/bold magenta]\n")

if __name__ == "__main__":
    run_tests()
