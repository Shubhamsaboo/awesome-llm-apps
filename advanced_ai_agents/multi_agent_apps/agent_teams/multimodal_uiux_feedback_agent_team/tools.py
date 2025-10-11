import os
import logging
from google import genai
from google.genai import types
from google.adk.tools import ToolContext
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# Helper Functions for Asset Version Management
# ============================================================================

def get_next_version_number(tool_context: ToolContext, asset_name: str) -> int:
    """Get the next version number for a given asset name."""
    asset_versions = tool_context.state.get("asset_versions", {})
    current_version = asset_versions.get(asset_name, 0)
    next_version = current_version + 1
    return next_version


def update_asset_version(tool_context: ToolContext, asset_name: str, version: int, filename: str) -> None:
    """Update the version tracking for an asset."""
    if "asset_versions" not in tool_context.state:
        tool_context.state["asset_versions"] = {}
    if "asset_filenames" not in tool_context.state:
        tool_context.state["asset_filenames"] = {}
    
    tool_context.state["asset_versions"][asset_name] = version
    tool_context.state["asset_filenames"][asset_name] = filename


def create_versioned_filename(asset_name: str, version: int, file_extension: str = "png") -> str:
    """Create a versioned filename for an asset."""
    return f"{asset_name}_v{version}.{file_extension}"


async def load_landing_page_image(tool_context: ToolContext, filename: str):
    """Load a landing page image artifact by filename."""
    try:
        loaded_part = await tool_context.load_artifact(filename)
        if loaded_part:
            logger.info(f"Successfully loaded landing page image: {filename}")
            return loaded_part
        else:
            logger.warning(f"Landing page image not found: {filename}")
            return None
    except Exception as e:
        logger.error(f"Error loading landing page image {filename}: {e}")
        return None


# ============================================================================
# Pydantic Input Models
# ============================================================================

class EditLandingPageInput(BaseModel):
    artifact_filename: str = Field(..., description="The filename of the landing page artifact to edit.")
    prompt: str = Field(..., description="Detailed description of UI/UX improvements to apply.")
    asset_name: str = Field(default=None, description="Optional: specify asset name for the new version.")


class GenerateImprovedLandingPageInput(BaseModel):
    prompt: str = Field(..., description="A detailed description of the improved landing page based on feedback.")
    aspect_ratio: str = Field(default="16:9", description="The desired aspect ratio. Default is 16:9.")
    asset_name: str = Field(default="landing_page_improved", description="Base name for the improved design.")
    reference_image: str = Field(default=None, description="Optional: filename of the original landing page to use as reference.")


# ============================================================================
# NOTE: Image Analysis is handled directly by agents with vision capabilities
# Agents with gemini-2.5-flash can see and analyze uploaded images automatically
# No separate image analysis tool is needed
# ============================================================================


# ============================================================================
# Image Editing Tool
# ============================================================================

async def edit_landing_page_image(tool_context: ToolContext, inputs: EditLandingPageInput) -> str:
    """
    Edits a landing page image by applying UI/UX improvements.
    
    This tool uses Gemini 2.5 Flash's image generation capabilities to create
    an improved version of the landing page based on feedback.
    """
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")

    logger.info("Starting landing page image editing")

    try:
        client = genai.Client()
        inputs = EditLandingPageInput(**inputs)
        
        # Load the existing landing page image
        logger.info(f"Loading artifact: {inputs.artifact_filename}")
        try:
            loaded_image_part = await tool_context.load_artifact(inputs.artifact_filename)
            if not loaded_image_part:
                return f"❌ Could not find landing page artifact: {inputs.artifact_filename}"
        except Exception as e:
            logger.error(f"Error loading artifact: {e}")
            return f"Error loading landing page artifact: {e}"

        model = "gemini-2.5-flash-image"

        # Build edit prompt with UI/UX best practices
        enhanced_prompt = f"""
{inputs.prompt}

**Apply these UI/UX best practices while editing:**
- Maintain visual hierarchy (size, color, spacing)
- Ensure sufficient whitespace for breathing room
- Use consistent alignment and grid system
- Make CTAs prominent with contrasting colors
- Improve readability (font size, line height, contrast)
- Follow modern web design principles
- Keep the overall brand aesthetic

Make the improvements look natural and professional.
"""

        # Build content parts
        content_parts = [loaded_image_part, types.Part.from_text(text=enhanced_prompt)]

        contents = [
            types.Content(
                role="user",
                parts=content_parts,
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
        )

        # Determine asset name and generate versioned filename
        if inputs.asset_name:
            asset_name = inputs.asset_name
        else:
            current_asset_name = tool_context.state.get("current_asset_name")
            if current_asset_name:
                asset_name = current_asset_name
            else:
                base_name = inputs.artifact_filename.split('_v')[0] if '_v' in inputs.artifact_filename else "landing_page"
                asset_name = base_name
        
        version = get_next_version_number(tool_context, asset_name)
        edited_artifact_filename = create_versioned_filename(asset_name, version)
        logger.info(f"Editing landing page with artifact filename: {edited_artifact_filename} (version {version})")

        # Edit the image
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            
            if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                
                # Create a Part object from the inline data
                edited_image_part = types.Part(inline_data=inline_data)
                
                try:
                    # Save the edited image as an artifact
                    version = await tool_context.save_artifact(
                        filename=edited_artifact_filename, 
                        artifact=edited_image_part
                    )
                    
                    # Update version tracking
                    update_asset_version(tool_context, asset_name, version, edited_artifact_filename)
                    
                    # Store in session state
                    tool_context.state["last_edited_landing_page"] = edited_artifact_filename
                    tool_context.state["current_asset_name"] = asset_name
                    
                    logger.info(f"Saved edited landing page as artifact '{edited_artifact_filename}' (version {version})")
                    
                    return f"✅ **Landing page edited successfully!**\n\nSaved as: **{edited_artifact_filename}** (version {version} of {asset_name})\n\nThe landing page has been improved with the UI/UX enhancements."
                    
                except Exception as e:
                    logger.error(f"Error saving edited artifact: {e}")
                    return f"Error saving edited landing page as artifact: {e}"
            else:
                if hasattr(chunk, 'text') and chunk.text:
                    logger.info(f"Model response: {chunk.text}")
                
        return "No edited landing page was generated. Please try again."
        
    except Exception as e:
        logger.error(f"Error in edit_landing_page_image: {e}")
        return f"An error occurred while editing the landing page: {e}"


# ============================================================================
# Generate Improved Landing Page Tool
# ============================================================================

async def generate_improved_landing_page(tool_context: ToolContext, inputs: GenerateImprovedLandingPageInput) -> str:
    """
    Generates an improved landing page based on the analysis and feedback.
    
    This tool creates a new landing page design incorporating all the recommended
    UI/UX improvements. Can work with or without a reference image.
    """
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")

    logger.info("Starting improved landing page generation")
    
    try:
        client = genai.Client()
        inputs = GenerateImprovedLandingPageInput(**inputs)
        
        # Note: Reference images from the conversation are automatically available to agents
        # This parameter is kept for backwards compatibility with saved artifacts
        reference_part = None
        if inputs.reference_image:
            try:
                reference_part = await load_landing_page_image(tool_context, inputs.reference_image)
                if reference_part:
                    logger.info(f"Using reference image artifact: {inputs.reference_image}")
            except Exception as e:
                logger.warning(f"Could not load reference image, proceeding without it: {e}")
        
        # Get the analysis from state to incorporate feedback
        latest_analysis = tool_context.state.get("latest_analysis", "")
        
        # Build enhanced prompt
        enhancement_prompt = f"""
Create a professional landing page design that incorporates these improvements:

{inputs.prompt}

**Previous Analysis Insights:**
{latest_analysis[:500] if latest_analysis else "No previous analysis available"}

**Design Requirements:**
- Modern, clean aesthetic
- Clear visual hierarchy
- Prominent, well-designed CTAs
- Proper whitespace and breathing room
- Professional typography with clear hierarchy
- Accessible color contrast (WCAG AA)
- Mobile-first responsive considerations
- Follow the latest UI/UX best practices
- High-quality, photorealistic rendering

Aspect ratio: {inputs.aspect_ratio}

Create a professional UI/UX design that would be magazine-quality.
"""
        
        # Prepare content parts
        content_parts = [types.Part.from_text(text=enhancement_prompt)]
        if reference_part:
            content_parts.append(reference_part)
        
        # Generate enhanced prompt first
        rewritten_prompt_response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=enhancement_prompt
        )
        rewritten_prompt = rewritten_prompt_response.text
        logger.info(f"Enhanced prompt: {rewritten_prompt}")

        model = "gemini-2.5-flash-image"
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=rewritten_prompt)] + ([reference_part] if reference_part else []),
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
        )

        # Generate versioned filename
        version = get_next_version_number(tool_context, inputs.asset_name)
        artifact_filename = create_versioned_filename(inputs.asset_name, version)
        logger.info(f"Generating improved landing page with filename: {artifact_filename} (version {version})")

        # Generate the image
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            
            if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                
                image_part = types.Part(inline_data=inline_data)
                
                try:
                    version = await tool_context.save_artifact(
                        filename=artifact_filename, 
                        artifact=image_part
                    )
                    
                    update_asset_version(tool_context, inputs.asset_name, version, artifact_filename)
                    
                    tool_context.state["last_generated_landing_page"] = artifact_filename
                    tool_context.state["current_asset_name"] = inputs.asset_name
                    
                    logger.info(f"Saved improved landing page as artifact '{artifact_filename}' (version {version})")
                    
                    return f"✅ **Improved landing page generated successfully!**\n\nSaved as: **{artifact_filename}** (version {version} of {inputs.asset_name})\n\nThis design incorporates all the recommended UI/UX improvements."
                    
                except Exception as e:
                    logger.error(f"Error saving artifact: {e}")
                    return f"Error saving improved landing page as artifact: {e}"
            else:
                if hasattr(chunk, 'text') and chunk.text:
                    logger.info(f"Model response: {chunk.text}")
                
        return "No improved landing page was generated. Please try again with a more detailed prompt."
        
    except Exception as e:
        logger.error(f"Error in generate_improved_landing_page: {e}")
        return f"An error occurred while generating the improved landing page: {e}"


# ============================================================================
# Note: No utility tools needed - agents handle everything directly
# ============================================================================


