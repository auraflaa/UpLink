"""
parser.py — Document parsing engine for the UpLink Document Parser service.

Supports: PDF (opendataloader-pdf / pypdf fallback), DOCX, TXT, MD, CSV
Output: List of text chunks ready for embedding.
"""

from __future__ import annotations

import csv
import io
import os
import tempfile
from typing import List

# ── Availability flags ──────────────────────────────────────────────────────
try:
    import opendataloader_pdf
    OPENDATALOADER_AVAILABLE = True
except ImportError:
    OPENDATALOADER_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# ── Constants ───────────────────────────────────────────────────────────────
CHUNK_SIZE   = 800   # Target tokens per chunk (approx 1 token ≈ 4 chars)
CHUNK_OVERLAP = 80   # Overlap in tokens between consecutive chunks
CHARS_PER_TOKEN = 4


def parse_file(filename: str, content: bytes) -> List[str]:
    """
    Entry point. Dispatches to the correct parser based on file extension.
    Returns a list of text chunks.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        text = _parse_pdf(filename, content)
    elif ext in (".docx",):
        text = _parse_docx(content)
    elif ext in (".txt", ".md"):
        text = content.decode("utf-8", errors="replace")
    elif ext == ".csv":
        text = _parse_csv(content)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    return _chunk_text(text, filename)


# ── PDF ──────────────────────────────────────────────────────────────────────

def _parse_pdf(filename: str, content: bytes) -> str:
    """Parse PDF. Uses opendataloader-pdf if available (Java required), else falls back to pypdf."""
    if OPENDATALOADER_AVAILABLE:
        return _parse_pdf_opendataloader(filename, content)
    if PYPDF_AVAILABLE:
        print(f"[!] opendataloader-pdf not available. Using pypdf fallback for {filename}")
        return _parse_pdf_pypdf(content)
    raise RuntimeError("No PDF parser available. Install opendataloader-pdf or pypdf.")


def _parse_pdf_opendataloader(filename: str, content: bytes) -> str:
    """
    Write to a temp file, convert to Markdown via opendataloader_pdf,
    then read and return the result.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, filename)
        output_dir = os.path.join(tmp_dir, "out")
        os.makedirs(output_dir, exist_ok=True)

        with open(input_path, "wb") as f:
            f.write(content)

        try:
            opendataloader_pdf.convert(
                input_path=[input_path],
                output_dir=output_dir,
                format="markdown",
            )
        except Exception as e:
            print(f"[!] opendataloader-pdf failed for {filename}: {e}. Falling back to pypdf.")
            if PYPDF_AVAILABLE:
                return _parse_pdf_pypdf(content)
            raise

        # Locate the generated .md file
        for root, _, files in os.walk(output_dir):
            for f in files:
                if f.endswith(".md"):
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="replace") as fh:
                        return fh.read()

    raise RuntimeError(f"opendataloader-pdf produced no output for {filename}")


def _parse_pdf_pypdf(content: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(content))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return "\n\n".join(pages)


# ── DOCX ─────────────────────────────────────────────────────────────────────

def _parse_docx(content: bytes) -> str:
    if not DOCX_AVAILABLE:
        raise RuntimeError("python-docx is not installed. Run: pip install python-docx")
    doc = DocxDocument(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


# ── CSV ───────────────────────────────────────────────────────────────────────

def _parse_csv(content: bytes) -> str:
    if PANDAS_AVAILABLE:
        df = pd.read_csv(io.BytesIO(content))
        return df.to_string(index=False)
    # Pure-stdlib fallback
    decoded = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(decoded))
    rows = ["\t".join(row) for row in reader]
    return "\n".join(rows)


# ── Chunker ───────────────────────────────────────────────────────────────────

def _chunk_text(text: str, source_hint: str = "") -> List[str]:
    """
    Semantic-aware chunker:
    1. Splits on Markdown headings (#, ##, ###) to keep sections together.
    2. If a section exceeds CHUNK_SIZE, splits further by paragraph.
    3. If a paragraph still exceeds CHUNK_SIZE, hard-splits by character window.
    Returns a flat list of non-empty chunks tagged with a source hint.
    """
    max_chars = CHUNK_SIZE * CHARS_PER_TOKEN
    overlap_chars = CHUNK_OVERLAP * CHARS_PER_TOKEN

    # 1. Split on heading boundaries
    import re
    sections = re.split(r"(?m)^(#{1,3} .+)$", text)
    raw_sections: List[str] = []
    i = 0
    while i < len(sections):
        part = sections[i].strip()
        if re.match(r"^#{1,3} ", part) and i + 1 < len(sections):
            # Attach heading to the body that follows
            raw_sections.append(part + "\n" + sections[i + 1].strip())
            i += 2
        else:
            if part:
                raw_sections.append(part)
            i += 1

    chunks: List[str] = []
    for section in raw_sections:
        if len(section) <= max_chars:
            chunks.append(section)
        else:
            # 2. Split large sections by paragraph
            paragraphs = [p.strip() for p in section.split("\n\n") if p.strip()]
            buf = ""
            for para in paragraphs:
                if len(buf) + len(para) + 2 <= max_chars:
                    buf = (buf + "\n\n" + para).strip()
                else:
                    if buf:
                        chunks.append(buf)
                    # 3. Hard-split oversized single paragraph
                    if len(para) > max_chars:
                        for start in range(0, len(para), max_chars - overlap_chars):
                            piece = para[int(start):int(start + max_chars)]
                            if piece.strip():
                                chunks.append(piece)
                    else:
                        buf = para
            if buf:
                chunks.append(buf)

    return [c for c in chunks if c.strip()]
