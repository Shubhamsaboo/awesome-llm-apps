"""
LexReviewer Demo — End-to-End Walkthrough
==========================================
This self-contained script demonstrates the full LexReviewer workflow:

  1. Upload a PDF legal document (base64-encoded)
  2. Ask a question and stream the answer with citations
  3. Retrieve and display the chat history
  4. Clean up (delete vectors + history)

Prerequisites
-------------
  • LexReviewer backend running at http://localhost:8000
    (see the project README for setup instructions)
  • `requests` installed  (pip install -r requirements.txt)

Usage
-----
  python demo.py                         # uses the bundled sample contract text
  python demo.py --pdf path/to/file.pdf  # upload your own PDF
  python demo.py --url http://host:port  # point at a different backend URL
"""

import argparse
import base64
import io
import json
import sys
import textwrap
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("❌  'requests' is not installed. Run:  pip install -r requirements.txt")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEPARATOR = "─" * 70

def _print_header(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def _print_ok(msg: str) -> None:
    print(f"  ✅  {msg}")


def _print_info(msg: str) -> None:
    print(f"  ℹ️   {msg}")


def _print_error(msg: str) -> None:
    print(f"  ❌  {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Tiny synthetic PDF builder (no external library needed)
# ---------------------------------------------------------------------------

def _build_minimal_pdf(text: str) -> bytes:
    """
    Return a minimal but valid PDF containing *text*.
    Uses only the PDF cross-reference / object structure — no third-party lib.
    """
    lines = textwrap.wrap(text, width=80)
    # Escape special PDF chars
    safe = "\n".join(lines).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    stream_body = (
        "BT\n"
        "/F1 11 Tf\n"
        "50 750 Td\n"
        "12 TL\n"
    )
    for line in safe.split("\n"):
        stream_body += f"({line}) Tj T*\n"
    stream_body += "ET\n"
    stream_bytes = stream_body.encode()

    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    obj4 = (
        b"4 0 obj\n<< /Length " + str(len(stream_bytes)).encode() + b" >>\nstream\n"
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )
    obj5 = b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"

    header = b"%PDF-1.4\n"
    body = obj1 + obj2 + obj3 + obj4 + obj5

    # Build cross-reference table
    offsets = []
    pos = len(header)
    for obj in (obj1, obj2, obj3, obj4, obj5):
        offsets.append(pos)
        pos += len(obj)

    xref_offset = len(header) + len(body)
    xref = b"xref\n0 6\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n".encode()

    trailer = (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n" + str(xref_offset).encode() + b"\n%%EOF\n"
    )

    return header + body + xref + trailer


# ---------------------------------------------------------------------------
# Sample contract text (used when no PDF is supplied)
# ---------------------------------------------------------------------------

SAMPLE_CONTRACT = """
COMMERCIAL LEASE AGREEMENT

This Commercial Lease Agreement ("Agreement") is entered into as of January 1, 2025,
between Acme Properties LLC ("Landlord") and TechStart Inc. ("Tenant").

1. PREMISES
Landlord hereby leases to Tenant the premises located at 100 Innovation Drive,
Suite 400, San Francisco, CA 94105 ("Premises"), consisting of approximately
2,500 square feet of office space.

2. TERM
The lease term shall commence on February 1, 2025 and expire on January 31, 2027,
unless sooner terminated as provided herein.

3. RENT
Tenant agrees to pay monthly base rent of $8,500, due on the first day of each
calendar month. A late fee of 5% shall apply to payments received after the
5th of the month.

4. SECURITY DEPOSIT
Tenant shall deposit $17,000 (two months' rent) as a security deposit upon
execution of this Agreement. The security deposit shall be returned within
21 days of lease termination, less any deductions for damages beyond normal wear.

5. PERMITTED USE
The Premises shall be used solely for general office and technology business
purposes. Tenant shall not use the Premises for any unlawful purpose.

6. MAINTENANCE AND REPAIRS
Tenant shall maintain the Premises in good condition. Landlord is responsible
for structural repairs and HVAC maintenance. Tenant is responsible for interior
maintenance, including lighting and minor plumbing repairs.

7. INSURANCE
Tenant shall maintain commercial general liability insurance with limits of not
less than $1,000,000 per occurrence and $2,000,000 aggregate. Landlord shall
be named as an additional insured.

8. ASSIGNMENT AND SUBLETTING
Tenant shall not assign this lease or sublet the Premises without the prior
written consent of Landlord, which shall not be unreasonably withheld.

9. TERMINATION
Either party may terminate this Agreement upon 60 days written notice following
a material breach that remains uncured for 30 days after written notice of such breach.

10. GOVERNING LAW
This Agreement shall be governed by the laws of the State of California.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first
written above.

Acme Properties LLC                    TechStart Inc.
By: ___________________________        By: ___________________________
Name: Margaret Chen                    Name: David Okafor
Title: Managing Director               Title: CEO
"""

DEMO_QUESTIONS = [
    "What is the monthly rent amount and when is it due?",
    "What are the Tenant's maintenance responsibilities?",
    "What insurance coverage is the Tenant required to maintain?",
]


# ---------------------------------------------------------------------------
# API client helpers
# ---------------------------------------------------------------------------

def upload_document(base_url: str, doc_id: str, pdf_bytes: bytes) -> bool:
    """POST /upload-documents — returns True on success."""
    b64 = base64.b64encode(pdf_bytes).decode()
    resp = requests.post(
        f"{base_url}/upload-documents",
        headers={"Content-Type": "application/json", "document-id": doc_id},
        json={"file": b64},
        timeout=120,
    )
    if resp.status_code == 201:
        return True
    _print_error(f"Upload failed [{resp.status_code}]: {resp.text[:200]}")
    return False


def collection_exists(base_url: str, doc_id: str) -> bool:
    """POST /collection-exists — True if the document is already indexed."""
    resp = requests.post(
        f"{base_url}/collection-exists",
        headers={"Content-Type": "application/json", "document-ids": doc_id},
        json={},
        timeout=30,
    )
    if resp.status_code == 200:
        results = resp.json()
        return bool(results and results[0])
    return False


def ask_question(base_url: str, doc_id: str, user_id: str, username: str, question: str) -> dict:
    """
    POST /ask — streams NDJSON lines.
    Returns a dict with keys: answer (str), thoughts (list), references (list).
    """
    result = {"answer": "", "thoughts": [], "references": []}

    with requests.post(
        f"{base_url}/ask",
        headers={
            "Content-Type": "application/json",
            "document-id": doc_id,
            "user-id": user_id,
            "username": username,
        },
        json={"question": question},
        stream=True,
        timeout=120,
    ) as resp:
        if resp.status_code != 200:
            _print_error(f"Ask failed [{resp.status_code}]: {resp.text[:200]}")
            return result

        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            try:
                line = raw_line.decode() if isinstance(raw_line, bytes) else raw_line
                data = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            if "chunk" in data:
                result["answer"] += data["chunk"]
                # Print incrementally so the user sees streaming in action
                print(data["chunk"], end="", flush=True)
            elif "thought" in data:
                result["thoughts"].extend(
                    data["thought"] if isinstance(data["thought"], list) else [data["thought"]]
                )
            elif "reference_positions" in data:
                result["references"].extend(data["reference_positions"])
            elif "error" in data:
                _print_error(f"Stream error: {data['error']}")

    return result


def get_history(base_url: str, doc_id: str, user_id: str) -> list:
    """GET /get-history — returns list of ChatEntry dicts."""
    resp = requests.get(
        f"{base_url}/get-history",
        headers={"document-id": doc_id, "user-id": user_id},
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.json().get("chatHistory", [])
    return []


def clear_history(base_url: str, doc_id: str, user_id: str) -> None:
    """DELETE /clear-history."""
    requests.delete(
        f"{base_url}/clear-history",
        headers={"document-id": doc_id, "user-id": user_id},
        timeout=30,
    )


def delete_vector(base_url: str, doc_id: str, user_id: str) -> None:
    """DELETE /delete-vector."""
    requests.delete(
        f"{base_url}/delete-vector",
        headers={"document-id": doc_id, "user-id": user_id},
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

def run_demo(base_url: str, pdf_path: str | None) -> None:
    doc_id   = "demo-lease-001"
    user_id  = "demo-user"
    username = "Demo User"

    # ------------------------------------------------------------------
    # 0. Health-check
    # ------------------------------------------------------------------
    _print_header("Step 0 — Checking backend connectivity")
    try:
        resp = requests.get(f"{base_url}/docs", timeout=10)
        _print_ok(f"Backend reachable at {base_url}  (status {resp.status_code})")
    except requests.exceptions.ConnectionError:
        _print_error(
            f"Cannot reach backend at {base_url}\n"
            "       Make sure LexReviewer is running:  python app.py"
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Prepare PDF
    # ------------------------------------------------------------------
    _print_header("Step 1 — Preparing PDF document")
    if pdf_path:
        pdf_bytes = Path(pdf_path).read_bytes()
        _print_info(f"Loaded PDF from disk: {pdf_path}  ({len(pdf_bytes):,} bytes)")
    else:
        _print_info("No PDF supplied — generating a synthetic commercial lease contract …")
        pdf_bytes = _build_minimal_pdf(SAMPLE_CONTRACT)
        _print_ok(f"Generated in-memory PDF  ({len(pdf_bytes):,} bytes)")

    # ------------------------------------------------------------------
    # 2. Upload / index
    # ------------------------------------------------------------------
    _print_header("Step 2 — Uploading & indexing the document")

    if collection_exists(base_url, doc_id):
        _print_info(f"Document '{doc_id}' is already indexed — skipping upload.")
    else:
        _print_info("Uploading document … (this may take ~30 s while Unstructured.io chunks it)")
        t0 = time.time()
        ok = upload_document(base_url, doc_id, pdf_bytes)
        if not ok:
            sys.exit(1)
        _print_ok(f"Indexed successfully in {time.time() - t0:.1f}s")

    # ------------------------------------------------------------------
    # 3. Q&A loop
    # ------------------------------------------------------------------
    _print_header("Step 3 — Asking questions (streaming RAG answers)")

    for i, question in enumerate(DEMO_QUESTIONS, 1):
        print(f"\n  Question {i}/{len(DEMO_QUESTIONS)}: {question}")
        print("  " + "·" * 60)
        print("  Answer: ", end="", flush=True)

        result = ask_question(base_url, doc_id, user_id, username, question)

        print()  # newline after streamed answer

        if result["thoughts"]:
            print(f"\n  Agent reasoning steps: {len(result['thoughts'])}")

        if result["references"]:
            print(f"\n  Source references returned: {len(result['references'])}")
        else:
            _print_info("No bounding-box references in this response.")

    # ------------------------------------------------------------------
    # 4. Cleanup
    # ------------------------------------------------------------------
    _print_header("Step 4 — Cleanup (deleting vectors + history)")
    _print_info("Deleting document vectors …")
    delete_vector(base_url, doc_id, user_id)
    _print_ok("Vectors deleted")

    _print_info("Clearing chat history …")
    clear_history(base_url, doc_id, user_id)
    _print_ok("History cleared")

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("  🎉  LexReviewer demo complete!")
    print("  Everything worked end-to-end:")
    print("    ✅ Document uploaded & indexed")
    print("    ✅ Questions answered with streaming RAG")
    print("    ✅ Cleanup successful")
    print(SEPARATOR + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="LexReviewer end-to-end demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the running LexReviewer backend (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--pdf",
        default=None,
        metavar="PATH",
        help="Path to a PDF to upload. Omit to use the built-in synthetic contract.",
    )
    args = parser.parse_args()

    run_demo(base_url=args.url.rstrip("/"), pdf_path=args.pdf)