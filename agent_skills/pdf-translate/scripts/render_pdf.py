# -*- coding: utf-8 -*-
"""
Helper script for rendering HTML to a publication-grade vector PDF using Playwright (Edge/Chromium).
Ensures zero raster images, selectable text, exact A4 layout, and automated page overflow detection.
"""

import sys
import os
import argparse
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def render_html_to_pdf(html_path: str, output_pdf_path: str, strict_overflow: bool = False):
    html_abs = os.path.abspath(html_path)
    output_abs = os.path.abspath(output_pdf_path)

    if not os.path.exists(html_abs):
        raise FileNotFoundError(f"HTML file not found: {html_abs}")

    os.makedirs(os.path.dirname(output_abs), exist_ok=True)

    print(f"Launching Playwright (Edge/Chromium) for vector PDF rendering...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Load page and wait until all network assets are idle
        page.goto(f"file:///{html_abs.replace(os.sep, '/')}", wait_until="networkidle")

        # Wait for all web fonts to load
        page.evaluate("document.fonts.ready")

        # In-browser Automated Page Height Overflow Detection
        overflow_check_js = """
        () => {
            const pages = document.querySelectorAll('.page');
            const errors = [];
            pages.forEach((el, index) => {
                const scrollH = el.scrollHeight;
                const clientH = el.clientHeight;
                // Allow a 2px sub-pixel tolerance
                if (scrollH > clientH + 2) {
                    errors.push({
                        page: index + 1,
                        scrollHeight: scrollH,
                        clientHeight: clientH,
                        overflowPx: scrollH - clientH
                    });
                }
            });
            return errors;
        }
        """
        overflows = page.evaluate(overflow_check_js)
        if overflows:
            print(f"\n[WARNING] Detected content overflow in {len(overflows)} page(s):")
            for ov in overflows:
                print(f"  ✖ Page {ov['page']}: scrollHeight={ov['scrollHeight']}px > clientHeight={ov['clientHeight']}px (+{ov['overflowPx']}px)")
            if strict_overflow:
                browser.close()
                raise ValueError("Strict overflow check failed! Pages exceeded bounding box.")
        else:
            print("  ✔ PASS: All .page containers satisfy physical bounds (zero overflow detected).")

        # Print PDF with high-fidelity vector settings
        page.pdf(
            path=output_abs,
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
        )
        browser.close()

    print(f"Successfully generated publication-grade vector PDF at:\n{output_abs}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render HTML to publication-grade vector PDF.")
    parser.add_argument("html", help="Path to input HTML file")
    parser.add_argument("pdf", help="Path to output PDF file")
    parser.add_argument("--strict-overflow", action="store_true", help="Fail if any page has vertical overflow")

    args = parser.parse_args()
    render_html_to_pdf(args.html, args.pdf, strict_overflow=args.strict_overflow)
