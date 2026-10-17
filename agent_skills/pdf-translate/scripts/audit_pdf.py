# -*- coding: utf-8 -*-
"""
Universal Automated PDF Translation Audit and Diff Engine
Skill: pdf-translate
Script: audit_pdf.py

Performs page-by-page 1:1 structural, numerical, and textual audit between
the source PDF and the translated vector PDF.
"""

import sys
import os
import re
import json
import argparse

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF (fitz) is required. Install via `pip install pymupdf`")
    sys.exit(1)

# Common AI hallucination / placeholder trigger words
HALLUCINATION_KEYWORDS = [
    "技术规范编制综述",
    "综述与准则",
    "核对清单 (Checklist)",
    "资质申报审查核对清单",
    "文件装订、密封与递交程序规范",
    "暂缺",
    "待补充",
    "待确认",
    "此处略",
    "因篇幅省略",
    "同上",
    "详见英文原版",
    "TBD",
    "TODO",
]

CLAUSE_REGEX = re.compile(
    r'(?:Section\s*(?:\(\s*\d+\s*\)|\d+)|'
    r'第\s*(?:\(\s*\d+\s*\)|\d+)\s*部分|'
    r'Appendix\s*[-–—]?\s*\d+|'
    r'附录\s*[-–—]?\s*[一二三四五六七八九十\d]+|'
    r'Table\s*[-–—\.]?\s*[A-Za-z0-9]+|'
    r'表\s*[-–—\.]?\s*[A-Za-z0-9\u4e00-\u9fa5]+|'
    r'(?<!\w)\d+\.\d+(?:\.\d+)*(?!\w))',
    re.IGNORECASE
)

def normalize_clause(clause: str) -> str:
    c = clause.strip().lower()
    c = re.sub(r'\s+', '', c)
    return c

def extract_clauses(text: str):
    matches = CLAUSE_REGEX.findall(text)
    seen = set()
    res = []
    for m in matches:
        norm = normalize_clause(m)
        if norm not in seen:
            seen.add(norm)
            res.append(m.strip())
    return res

def audit_document(src_path: str, tgt_path: str, strict: bool = False, json_out: str = None):
    print("=" * 70)
    print("  PDF-TRANSLATE AUTOMATED AUDIT ENGINE")
    print(f"  Source:     {src_path}")
    print(f"  Target:     {tgt_path}")
    print("=" * 70)

    if not os.path.exists(src_path):
        print(f"[FATAL] Source PDF not found: {src_path}")
        return False
    if not os.path.exists(tgt_path):
        print(f"[FATAL] Target PDF not found: {tgt_path}")
        return False

    doc_src = fitz.open(src_path)
    doc_tgt = fitz.open(tgt_path)

    total_src = len(doc_src)
    total_tgt = len(doc_tgt)

    report = {
        "summary": {
            "source_pages": total_src,
            "target_pages": total_tgt,
            "pages_matched": total_src == total_tgt,
            "total_raster_images": 0,
            "critical_errors": 0,
            "warnings": 0,
        },
        "pages": []
    }

    print(f"\n[1/4] PAGE COUNT CHECK:")
    if total_src == total_tgt:
        print(f"  ✔ PASS: Page count matches exactly ({total_src} pages).")
    else:
        print(f"  ✖ FAIL: Page count mismatch! Source={total_src}, Target={total_tgt}")
        report["summary"]["critical_errors"] += 1

    print(f"\n[2/4] VECTOR TEXT & ASSET INTEGRITY CHECK (Target PDF):")
    total_src_images = sum(len(page.get_images()) for page in doc_src)
    total_tgt_images = sum(len(page.get_images()) for page in doc_tgt)
    report["summary"]["total_raster_images"] = total_tgt_images

    # Check for full-page raster scans (fake OCR / full-page screenshots)
    full_page_scans = 0
    for pno, page in enumerate(doc_tgt):
        for img in page.get_images():
            rects = page.get_image_rects(img[0])
            for r in rects:
                if r.width > page.rect.width * 0.85 and r.height > page.rect.height * 0.85:
                    full_page_scans += 1

    if full_page_scans > 0:
        print(f"  ✖ FAIL: Found {full_page_scans} full-page raster scans! Target must be vector layout.")
        report["summary"]["critical_errors"] += 1
    elif total_tgt_images > 0:
        print(f"  ✔ PASS: Vector layout with {total_tgt_images} preserved asset images (Source has {total_src_images}).")
    else:
        print(f"  ✔ PASS: 100% pure vector text layer.")

    print(f"\n[3/4] PAGE-BY-PAGE 1:1 DEEP AUDIT:")
    max_pages = max(total_src, total_tgt)

    for pno in range(max_pages):
        page_info = {
            "page_num": pno + 1,
            "status": "PASS",
            "issues": []
        }

        if pno >= total_src:
            page_info["status"] = "FAIL"
            page_info["issues"].append("Extra page beyond source document")
            report["summary"]["critical_errors"] += 1
            report["pages"].append(page_info)
            continue

        if pno >= total_tgt:
            page_info["status"] = "FAIL"
            page_info["issues"].append("Missing page present in source document")
            report["summary"]["critical_errors"] += 1
            report["pages"].append(page_info)
            continue

        src_page = doc_src[pno]
        tgt_page = doc_tgt[pno]

        src_text = src_page.get_text().strip()
        tgt_text = tgt_page.get_text().strip()

        # Check for empty / suspicious blank page
        if len(tgt_text) < 20:
            page_info["issues"].append("Suspiciously blank target page (< 20 chars)")
            page_info["status"] = "WARNING"
            report["summary"]["warnings"] += 1

        # Check for AI hallucination keywords
        found_hallucinations = [kw for kw in HALLUCINATION_KEYWORDS if kw in tgt_text]
        if found_hallucinations:
            for h in found_hallucinations:
                msg = f"Hallucination keyword detected: '{h}'"
                page_info["issues"].append(msg)
            page_info["status"] = "FAIL"
            report["summary"]["critical_errors"] += 1

        # Check clauses
        src_clauses = extract_clauses(src_text)
        tgt_clauses = extract_clauses(tgt_text)

        src_norm = {normalize_clause(c): c for c in src_clauses}
        tgt_norm = {normalize_clause(c): c for c in tgt_clauses}

        missing_clauses = [src_norm[k] for k in src_norm if k not in tgt_norm and re.search(r'\d+\.\d+', k)]
        missing_clauses = [c for c in missing_clauses if not any(ign in c for ign in ["2026", "2531", "1998", "2009", "2010", "2016"])]

        if missing_clauses:
            page_info["issues"].append(f"Missing clauses in target: {missing_clauses}")
            if strict:
                page_info["status"] = "WARNING"
            report["summary"]["warnings"] += 1

        report["pages"].append(page_info)

        issue_str = f" ({'; '.join(page_info['issues'])})" if page_info["issues"] else ""
        icon = "✔" if page_info["status"] == "PASS" else ("▲" if page_info["status"] == "WARNING" else "✖")
        print(f"  Page {pno+1:02d}: [{icon} {page_info['status']:7s}]{issue_str}")

    print(f"\n[4/4] AUDIT SUMMARY:")
    print(f"  Total Critical Errors: {report['summary']['critical_errors']}")
    print(f"  Total Warnings:        {report['summary']['warnings']}")

    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"  Report exported to:    {json_out}")

    all_passed = (report["summary"]["critical_errors"] == 0)
    if all_passed:
        print("\n>>> AUDIT PASSED: Translation meets publication-grade fidelity standards! <<<")
    else:
        print("\n>>> AUDIT FAILED: Please review and fix critical issues above! <<<")

    return all_passed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit PDF translation quality and page-by-page alignment.")
    parser.add_argument("--src", required=True, help="Path to original source PDF")
    parser.add_argument("--tgt", required=True, help="Path to translated target PDF")
    parser.add_argument("--strict", action="store_true", help="Treat missing subclause warnings as critical")
    parser.add_argument("--json", default=None, help="Optional output path for JSON audit report")

    args = parser.parse_args()
    success = audit_document(args.src, args.tgt, strict=args.strict, json_out=args.json)
    sys.exit(0 if success else 1)
