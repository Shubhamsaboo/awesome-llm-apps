---
name: pdf-translate
description: >-
  Translates PDF documents across languages while strictly preserving original visual layout, typography, tables, and signatures. Reconstructs layout using HTML/CSS print paged media and vector rendering, with automated 1:1 page-by-page audit and zero-hallucination contracts. Use when the user asks to translate a PDF while keeping the original formatting, preserve layout on translated documents, convert documents with strict layout fidelity, or audit translated PDF geometry against the source.
license: Apache-2.0
compatibility: "Python 3.8+. Requires Playwright and PyMuPDF. Completely local and offline."
metadata:
  author: "lxsssssss"
  version: "2.3.0"
  source: "https://github.com/lxsssssss/pdf-translate"
---

# PDF Layout-Preserving Translation Skill

Translates PDF documents across languages with strict requirements to fully preserve original page layout, official letterheads, tables of contents, bilingual comparison tables, signature blocks, and exact figure dimensions, outputting publication-grade vector PDF files.

## Four Ironclad Rules

1. **Strict Faithful Translation & Zero Hallucination**:
   - **Never compress or omit clauses**: Faithfully translate every tier-1, tier-2, and tier-3 sub-clause. Subjective summaries or clause merges are strictly prohibited.
   - **Never fabricate common-sense content**: Strictly prohibit inventing non-existent submission procedures, binding copies, bank credit facilities, or administrative workflows.
   - **1:1 Faithful Table Reconstruction**: Official appendices must match column headers, row heights, checkboxes, remarks, and signature/stamp blocks 1:1. Never substitute with makeshift checklists.
2. **Geometry Probe & Visual Anchor Measurement First**:
   - **Never guess dimensions empirically**: Never apply arbitrary CSS constraints such as `max-height: 220px` without inspecting original PDF geometry.
   - **Extract physical coordinates & rects 1:1**: Call `page.get_image_rects(xref)` to obtain actual `width`, `height`, and `(x0, y0)` coordinates, rendering them at exact physical dimensions in HTML.
   - **Faithful geometric line and rule replication**: Use `page.get_drawings()` to extract all geometric rules and divider bars.
   - **Chinese information density compensation**: Chinese text density is 20%~35% higher than English. Record key vertical anchor baselines `y0`. Use balanced line-heights (`1.35~1.45`), margin tuning, and grid/absolute anchors to prevent lower-half blank voids.
   - **First-page header/footer conventions**: Respect conference or document cover conventions where page 1 omits running page numbers.
3. **Schema-First & Chunked Pipeline**:
   - **Decouple data from layout**: For long documents, extract structured page data before injecting into standardized HTML templates. Never generate freeform long-form text while concurrently writing markup.
   - **Single batch must not exceed 10 pages**: Documents exceeding 10 pages must be split into modular units of 10 pages each to prevent attention degradation.
4. **Mandatory Automated Audit & User Preview Gate Before Commit**:
   - Once rendered, execute the built-in [scripts/audit_pdf.py](scripts/audit_pdf.py) to check page count, vector layers, clause symmetric diffs, and hallucination keywords.
   - Side-by-side comparison images (PNG) should be rendered for user review.

---

## When to use

- User provides a PDF requesting translation while preserving formatting and page layout
- User asks to "translate this PDF and keep the exact layout", "output as vector PDF", or "preserve formatting"
- Official tender documents, technical specifications, academic papers, and enterprise contracts requiring 1:1 layout fidelity
- Bilingual documents with side-by-side comparison tables, signature/stamp blocks, and leader dot tables of contents
- Auditing translated PDF geometry against original documents

## When not to use

- Quick plain-text translation where visual layout and page geometry do not matter
- Translating plain Word (`.docx`), Markdown, or text files
- OCR scanning of heavily degraded, low-resolution unreadable scanned photos without vector text

---

## Standard Operating Procedure (SOP)

### Step 1: Document Inspection & Geometry Probing

Use PyMuPDF (`fitz`) to inspect physical page dimensions, image coordinates, and geometric rules:

```python
import fitz

doc = fitz.open("path/to/document.pdf")
print("Total pages:", len(doc))

for i, page in enumerate(doc):
    print(f"\n=== PAGE {i+1} rect: {page.rect} ===")
    for img in page.get_images():
        for r in page.get_image_rects(img[0]):
            print(f"  Image xref {img[0]}: w={r.width:.1f}, h={r.height:.1f}, (x0={r.x0:.1f}, y0={r.y0:.1f})")
    for d in page.get_drawings():
        r = d['rect']
        if r.width > 30:
            print(f"  Line: w={r.width:.1f}, h={r.height:.1f}, (x0={r.x0:.1f}, y0={r.y0:.1f})")
    for b in page.get_text("blocks"):
        if b[4].strip():
            print(f"  Block ({b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, {b[3]:.1f}): {b[4].strip()[:40]}")
```

### Step 2: Two-Stage Translation (Contract & Population)

1. **Stage 1 (Extraction & Verification)**: Extract clause numbers, parameters, and table schemas page-by-page.
2. **Stage 2 (Template Population)**: Accurately translate technical terminology while verifying numbers, units, and formulas 100%.

### Step 3: High-Fidelity Vector Layout Reconstruction

Use HTML5 + CSS `@page` print media:

```css
@page {
  size: 8.5in 11in; /* or 210mm 297mm for A4 */
  margin: 0;
}
.page {
  width: 8.5in;
  height: 11in;
  max-height: 11in;
  padding: 72pt 108pt 72pt 108pt;
  page-break-after: always;
  position: relative;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.content-area {
  flex: 1;
  overflow: hidden;
}
```

### Step 4: Headless Vector Rendering & JS Overflow Check

Execute the built-in Playwright rendering script [scripts/render_pdf.py](scripts/render_pdf.py):

```bash
python scripts/render_pdf.py path/to/input.html path/to/output.pdf
```

### Step 5: Automated 1:1 Comparison Audit

Execute [scripts/audit_pdf.py](scripts/audit_pdf.py) to audit page count, vector integrity, clause diffs, and hallucination keywords:

```bash
python scripts/audit_pdf.py --src path/to/source.pdf --tgt path/to/output.pdf
```

---

## Built-in Scripts

- **[scripts/render_pdf.py](scripts/render_pdf.py)**: Headless Playwright script that renders HTML to vector PDF with an automated JS probe detecting element overflow.
- **[scripts/audit_pdf.py](scripts/audit_pdf.py)**: Automated audit engine that compares source and target PDFs across page counts, vector layers, clause alignment, and anti-hallucination radar.
- **[scripts/requirements.txt](scripts/requirements.txt)**: Minimal Python dependencies (`playwright`, `pymupdf`).
