"""
parse_my_doc.py — Quick personal document parser test.

Usage:
    python parse_my_doc.py path/to/your/resume.pdf
    python parse_my_doc.py path/to/your/resume.pdf --collection my_resume
"""

import sys
import os
import io
import requests
import argparse

DOC_PARSER_URL = "http://127.0.0.1:8004"


def main():
    parser = argparse.ArgumentParser(description="Upload a document to UpLink Document Parser")
    parser.add_argument("file", help="Path to the document (PDF, DOCX, TXT, MD, CSV)")
    parser.add_argument("--collection", default="personal_docs", help="Qdrant collection name (default: personal_docs)")
    parser.add_argument("--label", default=None, help="Optional label tag for the document")
    parser.add_argument("--show-chunks", action="store_true", help="Print extracted chunk text")
    args = parser.parse_args()

    file_path = args.file
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    # Quick type check
    supported = {".pdf", ".docx", ".txt", ".md", ".csv"}
    if ext not in supported:
        print(f"[ERROR] Unsupported file type: {ext}. Supported: {', '.join(sorted(supported))}")
        sys.exit(1)

    print(f"\n{'='*55}")
    print(f"  UpLink Document Parser — Personal Test")
    print(f"{'='*55}")
    print(f"  File:       {filename}")
    print(f"  Collection: {args.collection}")
    print(f"  Parser URL: {DOC_PARSER_URL}")
    print(f"{'='*55}\n")

    # If --show-chunks, use the local parser directly to preview chunks
    if args.show_chunks:
        print("[*] Extracting chunks locally for preview...\n")
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Document Parser"))
            import parser as doc_parser
            with open(file_path, "rb") as f:
                content = f.read()
            chunks = doc_parser.parse_file(filename, content)
            print(f"[*] {len(chunks)} chunk(s) extracted:\n")
            for i, chunk in enumerate(chunks, 1):
                preview = chunk[:300].replace("\n", " ")
                print(f"  --- Chunk {i}/{len(chunks)} ---")
                print(f"  {preview}{'...' if len(chunk) > 300 else ''}")
                print()
        except Exception as e:
            print(f"[!] Local preview failed: {e}\n")

    # Upload to the service
    print("[*] Uploading to Document Parser service...")
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv",
    }

    with open(file_path, "rb") as f:
        content = f.read()

    data = {"collection_name": args.collection}
    if args.label:
        data["source_label"] = args.label

    try:
        resp = requests.post(
            f"{DOC_PARSER_URL}/ingest",
            files={"files": (filename, io.BytesIO(content), mime_map[ext])},
            data=data,
            timeout=120,
        )
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to Document Parser on port 8004.")
        print("  Start it: python 'Backend/Document Parser/server.py'")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"[ERROR] Server returned {resp.status_code}: {resp.text}")
        sys.exit(1)

    result = resp.json()
    file_result = result.get("results", {}).get(filename, {})

    print(f"\n{'='*55}")
    print(f"  Result")
    print(f"{'='*55}")
    print(f"  Status:         {result['status']}")
    print(f"  Collection:     {result['collection']}")
    print(f"  Chunks parsed:  {file_result.get('chunks_parsed', 'N/A')}")
    print(f"  Chunks stored:  {file_result.get('chunks_stored', 0)}")
    print(f"  File status:    {file_result.get('status', 'unknown')}")

    if result.get("errors"):
        print(f"\n  Errors:")
        for err in result["errors"]:
            print(f"    [!] {err}")

    if result["status"] in ("completed", "partial") and file_result.get("chunks_stored", 0) > 0:
        print(f"\n  [OK] Document is now searchable via RAG chat!")
        print(f"       Query it: POST http://127.0.0.1:6399/chat")
        print(f"       {{\"query\": \"what is in my resume?\", \"collection_name\": \"{args.collection}\"}}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
