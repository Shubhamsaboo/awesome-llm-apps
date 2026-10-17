# PDF Layout-Preserving Translation Agent Skill

`pdf-translate` translates PDF documents across languages while strictly preserving original visual layout, typography, tables, and signatures. It combines LLM two-stage schema extraction with geometry probing, HTML/CSS `@page` vector layout reconstruction, Playwright rendering, and an automated 1:1 page-by-page audit engine.

## What it does

- **1:1 Visual Layout Fidelity**: Accurately preserves headers, multi-column articles, tables of contents, bilingual comparison tables, signature blocks, and embedded figures.
- **Physical Geometry Probing**: Measures image dimensions and coordinate bounding boxes using PyMuPDF (`fitz`), eliminating distorted image clamps.
- **Zero Hallucination Contract**: Enforces faithful clause-by-clause translation without arbitrary summarization, content omissions, or invented terms.
- **Vector PDF Output**: Generates pure vector PDF pages via headless Chromium with an automated JavaScript probe that catches vertical overflow in real time.
- **Automated 1:1 Audit & Diff**: Uses `audit_pdf.py` to compare source and target documents across page count, vector layers, clause IDs, and anti-hallucination keywords.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/pdf-translate
```

Then ask your agent:
`Translate this PDF to Chinese, strictly preserving original layout and outputting as vector PDF.`

## Built-in Tools

### 1. Vector PDF Rendering (`scripts/render_pdf.py`)

Renders HTML containing CSS `@page` print rules to a vector PDF with headless Playwright, verifying bounding box heights:

```bash
pip install -r agent_skills/pdf-translate/scripts/requirements.txt
playwright install chromium
python agent_skills/pdf-translate/scripts/render_pdf.py input.html output.pdf
```

### 2. Automated 1:1 Comparison Audit (`scripts/audit_pdf.py`)

Audits the output PDF against the original document across page counts, clause numbers, and vector layer completeness:

```bash
python agent_skills/pdf-translate/scripts/audit_pdf.py --src original.pdf --tgt output.pdf
```

## Reference Repository

Developed and maintained at [lxsssssss/pdf-translate](https://github.com/lxsssssss/pdf-translate).
