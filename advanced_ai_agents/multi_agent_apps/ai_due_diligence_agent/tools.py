"""Custom tools for the Due Diligence Pipeline.

Provides HTML report generation, financial charts, and infographic creation.
"""

import logging
import io
from pathlib import Path
from datetime import datetime
from google.adk.tools import ToolContext
from google.genai import types, Client

logger = logging.getLogger("DueDiligencePipeline")

# Create outputs directory for generated files
OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


async def generate_financial_chart(
    company_name: str,
    current_arr: float,
    bear_rates: str,
    base_rates: str,
    bull_rates: str,
    tool_context: ToolContext
) -> dict:
    """Generate a revenue projection chart and save as ADK artifact.

    Args:
        company_name: Name of the company being analyzed
        current_arr: Current ARR in millions (e.g., 1.2 for $1.2M)
        bear_rates: Comma-separated YoY growth rates for bear case
        base_rates: Comma-separated YoY growth rates for base case
        bull_rates: Comma-separated YoY growth rates for bull case
        tool_context: ADK tool context for artifact saving

    Returns:
        dict with status and artifact info
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')
        
        # Parse growth rates
        bear = [float(x.strip()) for x in bear_rates.split(",")]
        base = [float(x.strip()) for x in base_rates.split(",")]
        bull = [float(x.strip()) for x in bull_rates.split(",")]
        
        # Calculate projections
        years = list(range(2025, 2025 + len(base) + 1))
        
        def project_arr(start, rates):
            arr = [start]
            for rate in rates:
                arr.append(arr[-1] * rate)
            return arr
        
        bear_arr = project_arr(current_arr, bear)
        base_arr = project_arr(current_arr, base)
        bull_arr = project_arr(current_arr, bull)
        
        # Create professional chart
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(years, bear_arr, 'o-', color='#dc2626', linewidth=2, markersize=8, label='Bear Case')
        ax.plot(years, base_arr, 's-', color='#1a365d', linewidth=3, markersize=10, label='Base Case')
        ax.plot(years, bull_arr, '^-', color='#16a34a', linewidth=2, markersize=8, label='Bull Case')
        ax.fill_between(years, bear_arr, bull_arr, alpha=0.1, color='#1a365d')
        
        ax.set_title(f'{company_name} - Revenue Projection Analysis', fontsize=16, fontweight='bold', color='#1a365d')
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('ARR ($ Millions)', fontsize=12)
        ax.legend(loc='upper left', fontsize=11)
        
        for x, y in zip(years, base_arr):
            ax.annotate(f'${y:.1f}M', (x, y), textcoords="offset points", 
                       xytext=(0, 10), ha='center', fontsize=9, color='#1a365d')
        
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buffer.seek(0)
        image_bytes = buffer.read()
        plt.close()
        
        # Save as ADK artifact (MUST await)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        artifact_name = f"revenue_chart_{timestamp}.png"
        chart_artifact = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
        
        version = await tool_context.save_artifact(filename=artifact_name, artifact=chart_artifact)
        logger.info(f"Saved chart artifact: {artifact_name} (version {version})")
        
        # Also save to outputs folder
        filepath = OUTPUTS_DIR / artifact_name
        filepath.write_bytes(image_bytes)
        
        return {
            "status": "success",
            "message": f"Chart saved as '{artifact_name}' - view in Artifacts tab",
            "artifact": artifact_name,
            "version": version,
            "summary": {
                "year_5_bear": f"${bear_arr[-1]:.1f}M",
                "year_5_base": f"${base_arr[-1]:.1f}M",
                "year_5_bull": f"${bull_arr[-1]:.1f}M"
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        return {"status": "error", "message": str(e)}


async def generate_html_report(
    report_data: str,
    tool_context: ToolContext
) -> dict:
    """Generate a professional HTML investment report.

    Args:
        report_data: The investor memo content to format as HTML
        tool_context: ADK tool context for artifact saving

    Returns:
        dict with status and artifact info
    """
    current_date = datetime.now().strftime("%B %d, %Y")
    
    prompt = f"""Generate a professional investment due diligence report in HTML format.

**IMPORTANT: Use this exact date: {current_date}**

Style it like a McKinsey or Goldman Sachs investment memo with:
- Clean, professional design with dark blue (#1a365d) and gold (#d4af37) colors
- Executive summary at the top with DATE: {current_date}
- Clear section headers with good typography
- Data tables for metrics
- Print-friendly layout

DATA TO FORMAT:
{report_data}

SECTIONS TO INCLUDE:
1. Executive Summary (Date: {current_date})
2. Company Overview
3. Market Opportunity
4. Financial Analysis
5. Risk Assessment
6. Investment Recommendation

Generate complete, valid HTML with embedded CSS."""

    try:
        client = Client()
        response = await client.aio.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )

        html_content = response.text

        # Clean up markdown wrapping if present
        if "```html" in html_content:
            start = html_content.find("```html") + 7
            end = html_content.rfind("```")
            html_content = html_content[start:end].strip()
        elif "```" in html_content:
            start = html_content.find("```") + 3
            end = html_content.rfind("```")
            html_content = html_content[start:end].strip()

        # Save as ADK artifact (MUST await)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        artifact_name = f"investment_report_{timestamp}.html"
        html_artifact = types.Part.from_bytes(
            data=html_content.encode('utf-8'),
            mime_type="text/html"
        )
        
        version = await tool_context.save_artifact(filename=artifact_name, artifact=html_artifact)
        logger.info(f"Saved HTML artifact: {artifact_name} (version {version})")

        # Also save to outputs folder
        filepath = OUTPUTS_DIR / artifact_name
        filepath.write_text(html_content, encoding='utf-8')
        
        return {
            "status": "success",
            "message": f"Report saved as '{artifact_name}' - view in Artifacts tab",
            "artifact": artifact_name,
            "version": version
        }

    except Exception as e:
        logger.error(f"Error generating HTML report: {e}")
        return {"status": "error", "message": str(e)}


async def generate_infographic(
    data_summary: str,
    tool_context: ToolContext
) -> dict:
    """Generate an investment infographic using Gemini's image generation.

    Args:
        data_summary: Key metrics and data to visualize
        tool_context: ADK tool context for artifact saving

    Returns:
        dict with status and artifact info
    """
    prompt = f"""Create a professional investment infographic.

Style: Clean, modern, investment banking aesthetic
Colors: Dark blue (#1a365d) primary, gold (#d4af37) accent, white background

Content to visualize:
{data_summary}

Include:
1. Company name prominently at top
2. Key metrics in large, bold numbers
3. Market size visualization
4. Risk score indicator (1-10 scale)
5. Investment recommendation badge

Make it look like a Goldman Sachs one-pager. Professional, data-rich."""

    try:
        client = Client()
        response = await client.aio.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        # Look for image in response
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type
                
                # Save as ADK artifact (MUST await)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = "png" if "png" in mime_type else "jpg"
                artifact_name = f"infographic_{timestamp}.{ext}"
                
                image_artifact = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                version = await tool_context.save_artifact(filename=artifact_name, artifact=image_artifact)
                logger.info(f"Saved infographic artifact: {artifact_name} (version {version})")
                
                # Also save to outputs folder
                filepath = OUTPUTS_DIR / artifact_name
                filepath.write_bytes(image_bytes)
                
                return {
                    "status": "success",
                    "message": f"Infographic saved as '{artifact_name}' - view in Artifacts tab",
                    "artifact": artifact_name,
                    "version": version
                }

        return {
            "status": "partial",
            "message": "Image generation not available",
            "description": response.text if response.text else "No content"
        }

    except Exception as e:
        logger.error(f"Error generating infographic: {e}")
        return {"status": "error", "message": str(e)}
