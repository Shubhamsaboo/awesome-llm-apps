"""Custom tools for the Battle Card Pipeline.

Provides HTML battle card generation and comparison chart creation.
"""

import logging
from pathlib import Path
from datetime import datetime
from google.adk.tools import ToolContext
from google.genai import types, Client

logger = logging.getLogger("BattleCardPipeline")

# Create outputs directory for generated files
OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


async def generate_battle_card_html(
    battle_card_data: str,
    tool_context: ToolContext
) -> dict:
    """Generate a professional HTML battle card for sales teams.

    Args:
        battle_card_data: Compiled competitive intelligence data
        tool_context: ADK tool context for artifact saving

    Returns:
        dict with status and artifact info
    """
    current_date = datetime.now().strftime("%B %d, %Y")
    
    prompt = f"""Generate a professional sales battle card in HTML format.

**DATE: {current_date}**

This is a competitive battle card for sales reps to use during deals.

Style it for SALES TEAMS with:
- Clean, scannable design (reps glance at this during calls)
- Color coding: GREEN for our advantages, RED for competitor strengths
- Collapsible sections for detailed content
- Quick-reference format at the top
- Dark blue (#1e3a5f) and orange (#f97316) color scheme
- Print-friendly layout

COMPETITIVE INTELLIGENCE DATA:
{battle_card_data}

**REQUIRED SECTIONS:**

1. **Header** - Competitor name, logo placeholder, last updated date
2. **Quick Stats** - 5-6 one-liner facts about the competitor
3. **At a Glance** - 3 columns: They Win | We Win | Toss-up
4. **Feature Comparison** - Table with checkmarks/X marks
5. **Positioning** - How to position against them (2-3 sentences)
6. **Their Strengths** - Honest list with red indicators
7. **Their Weaknesses** - List with green indicators (our opportunities)
8. **Objection Handling** - Top 5 objections with quick responses
9. **Killer Questions** - Questions to ask prospects
10. **Landmines** - Traps to set in competitive deals

Make it visually impressive but FAST TO SCAN. Sales reps have seconds, not minutes.

Generate complete, valid HTML with embedded CSS and JavaScript for collapsible sections."""

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

        # Save as ADK artifact
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        artifact_name = f"battle_card_{timestamp}.html"
        html_artifact = types.Part.from_bytes(
            data=html_content.encode('utf-8'),
            mime_type="text/html"
        )
        
        version = await tool_context.save_artifact(filename=artifact_name, artifact=html_artifact)
        logger.info(f"Saved battle card artifact: {artifact_name} (version {version})")

        # Also save to outputs folder
        filepath = OUTPUTS_DIR / artifact_name
        filepath.write_text(html_content, encoding='utf-8')
        
        return {
            "status": "success",
            "message": f"Battle card saved as '{artifact_name}' - view in Artifacts tab",
            "artifact": artifact_name,
            "version": version
        }

    except Exception as e:
        logger.error(f"Error generating battle card: {e}")
        return {"status": "error", "message": str(e)}


async def generate_comparison_chart(
    competitor_name: str,
    your_product_name: str,
    comparison_data: str,
    tool_context: ToolContext
) -> dict:
    """Generate a visual comparison infographic using Gemini image generation.

    Args:
        competitor_name: Name of the competitor
        your_product_name: Name of your product
        comparison_data: Feature comparison data with scores and highlights
        tool_context: ADK tool context for artifact saving

    Returns:
        dict with status and artifact info
    """
    prompt = f"""Create a professional competitive comparison infographic.

**COMPARISON: {your_product_name} vs {competitor_name}**

Style: Clean, modern, sales-ready infographic
Colors: 
- Green (#22c55e) for {your_product_name} (your product)
- Red (#ef4444) for {competitor_name} (competitor)
- Dark blue (#1e3a5f) for headers and text
- White background

**DATA TO VISUALIZE:**
{comparison_data}

**INFOGRAPHIC LAYOUT:**

1. **Header** - "{your_product_name} vs {competitor_name}" prominently at top
2. **Score Overview** - Large visual showing overall winner
3. **Feature Comparison** - Side-by-side bars or ratings for each feature
4. **Key Differentiators** - Icons highlighting where {your_product_name} wins
5. **Bottom Line** - Clear verdict/recommendation badge

**DESIGN REQUIREMENTS:**
- Professional, enterprise-ready aesthetic
- Easy to read at a glance
- Color-coded clearly (green = us, red = them)
- Include checkmarks for wins, X marks for losses
- Make it look like a Gartner or Forrester comparison graphic
- Data-rich but not cluttered

Generate a visually compelling infographic that sales reps can share with prospects."""

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
                
                # Save as ADK artifact
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = "png" if "png" in mime_type else "jpg"
                artifact_name = f"comparison_infographic_{timestamp}.{ext}"
                
                image_artifact = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                version = await tool_context.save_artifact(filename=artifact_name, artifact=image_artifact)
                logger.info(f"Saved comparison infographic: {artifact_name} (version {version})")
                
                # Also save to outputs folder
                filepath = OUTPUTS_DIR / artifact_name
                filepath.write_bytes(image_bytes)
                
                return {
                    "status": "success",
                    "message": f"Comparison infographic saved as '{artifact_name}' - view in Artifacts tab",
                    "artifact": artifact_name,
                    "version": version,
                    "comparison": f"{your_product_name} vs {competitor_name}"
                }

        return {
            "status": "partial",
            "message": "Image generation not available, text description provided",
            "description": response.text if response.text else "No content generated"
        }

    except Exception as e:
        logger.error(f"Error generating comparison infographic: {e}")
        return {"status": "error", "message": str(e)}

