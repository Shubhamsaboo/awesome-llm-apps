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
    
    # Maintain a list of all versions for this asset
    asset_history_key = f"{asset_name}_history"
    if asset_history_key not in tool_context.state:
        tool_context.state[asset_history_key] = []
    tool_context.state[asset_history_key].append({"version": version, "filename": filename})


def create_versioned_filename(asset_name: str, version: int, file_extension: str = "png") -> str:
    """Create a versioned filename for an asset."""
    return f"{asset_name}_v{version}.{file_extension}"


def get_asset_versions_info(tool_context: ToolContext) -> str:
    """Get information about all asset versions in the session."""
    asset_versions = tool_context.state.get("asset_versions", {})
    if not asset_versions:
        return "No renovation renderings have been created yet."
    
    info_lines = ["Current renovation renderings:"]
    for asset_name, current_version in asset_versions.items():
        history_key = f"{asset_name}_history"
        history = tool_context.state.get(history_key, [])
        total_versions = len(history)
        latest_filename = tool_context.state.get("asset_filenames", {}).get(asset_name, "Unknown")
        info_lines.append(f"  • {asset_name}: {total_versions} version(s), latest is v{current_version} ({latest_filename})")
    
    return "\n".join(info_lines)


def get_reference_images_info(tool_context: ToolContext) -> str:
    """Get information about all reference images (current room/inspiration) uploaded in the session."""
    reference_images = tool_context.state.get("reference_images", {})
    if not reference_images:
        return "No reference images have been uploaded yet."
    
    info_lines = ["Available reference images (current room photos & inspiration):"]
    for filename, info in reference_images.items():
        version = info.get("version", "Unknown")
        image_type = info.get("type", "reference")
        info_lines.append(f"  • {filename} ({image_type} v{version})")
    
    return "\n".join(info_lines)


async def load_reference_image(tool_context: ToolContext, filename: str):
    """Load a reference image artifact by filename."""
    try:
        loaded_part = await tool_context.load_artifact(filename)
        if loaded_part:
            logger.info(f"Successfully loaded reference image: {filename}")
            return loaded_part
        else:
            logger.warning(f"Reference image not found: {filename}")
            return None
    except Exception as e:
        logger.error(f"Error loading reference image {filename}: {e}")
        return None


def get_latest_reference_image_filename(tool_context: ToolContext) -> str:
    """Get the filename of the most recently uploaded reference image."""
    return tool_context.state.get("latest_reference_image")


# ============================================================================
# Pydantic Input Models
# ============================================================================

class GenerateRenovationRenderingInput(BaseModel):
    prompt: str = Field(..., description="A detailed description of the renovated space to generate. Include room type, style, colors, materials, fixtures, lighting, and layout.")
    aspect_ratio: str = Field(default="16:9", description="The desired aspect ratio, e.g., '1:1', '16:9', '9:16'. Default is 16:9 for room photos.")
    asset_name: str = Field(default="renovation_rendering", description="Base name for the rendering (will be versioned automatically). Use descriptive names like 'kitchen_modern_farmhouse' or 'bathroom_spa'.")
    current_room_photo: str = Field(default=None, description="Optional: filename of the current room photo to use as reference for layout/structure.")
    inspiration_image: str = Field(default=None, description="Optional: filename of an inspiration image to guide the style. Use 'latest' for most recent upload.")


class EditRenovationRenderingInput(BaseModel):
    artifact_filename: str = Field(default=None, description="The filename of the rendering artifact to edit. If not provided, uses the last generated rendering.")
    prompt: str = Field(..., description="The prompt describing the desired changes (e.g., 'make cabinets darker', 'add pendant lights', 'change floor to hardwood').")
    asset_name: str = Field(default=None, description="Optional: specify asset name for the new version (defaults to incrementing current asset).")
    reference_image_filename: str = Field(default=None, description="Optional: filename of a reference image to guide the edit. Use 'latest' for most recent upload.")


# ============================================================================
# Image Generation Tool
# ============================================================================

async def generate_renovation_rendering(tool_context: ToolContext, inputs: GenerateRenovationRenderingInput) -> str:
    """
    Generates a photorealistic rendering of a renovated space based on the design plan.
    
    This tool uses Gemini 3 Pro's image generation capabilities to create visual 
    representations of renovation plans. It can optionally use current room photos 
    and inspiration images as references.
    """
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")

    logger.info("Starting renovation rendering generation")
    try:
        client = genai.Client()
        
        # Handle inputs that might come as dict instead of Pydantic model
        if isinstance(inputs, dict):
            inputs = GenerateRenovationRenderingInput(**inputs)
        
        # Handle reference images (current room photo or inspiration)
        reference_images = []
        
        if inputs.current_room_photo:
            current_photo_part = await load_reference_image(tool_context, inputs.current_room_photo)
            if current_photo_part:
                reference_images.append(current_photo_part)
                logger.info(f"Using current room photo: {inputs.current_room_photo}")
        
        if inputs.inspiration_image:
            if inputs.inspiration_image == "latest":
                insp_filename = get_latest_reference_image_filename(tool_context)
            else:
                insp_filename = inputs.inspiration_image
            
            if insp_filename:
                inspiration_part = await load_reference_image(tool_context, insp_filename)
                if inspiration_part:
                    reference_images.append(inspiration_part)
                    logger.info(f"Using inspiration image: {insp_filename}")
        
        # Build the enhanced prompt
        base_rewrite_prompt = f"""
        Create a highly detailed, photorealistic prompt for generating an interior design image.
        
        Original description: {inputs.prompt}
        
        **CRITICAL REQUIREMENT - PRESERVE EXACT LAYOUT:**
        The generated image MUST maintain the EXACT same room layout, structure, and spatial arrangement described in the prompt:
        - Keep all windows, doors, skylights in their exact positions
        - Keep all cabinets, counters, appliances in their exact positions
        - Keep the same room dimensions and proportions
        - Keep the same camera angle/perspective
        - ONLY change surface finishes: paint colors, cabinet colors, countertop materials, flooring, backsplash, hardware, and decorative elements
        - DO NOT move, add, or remove any structural elements or major fixtures
        
        Enhance this to be a professional interior photography prompt that includes:
        - Specific camera angle (match original photo perspective if described)
        - Exact colors and materials mentioned (apply to existing surfaces)
        - Realistic lighting (natural light from existing windows, fixture types)
        - Maintain existing spatial layout and dimensions
        - Texture and finish details for the new materials
        - Professional interior design photography quality
        
        Aspect ratio: {inputs.aspect_ratio}
        """
        
        if reference_images:
            base_rewrite_prompt += "\n\n**Reference Image Layout:** The reference image shows the EXACT layout that must be preserved. Match the camera angle, room structure, window/door positions, and furniture/appliance placement EXACTLY. Only change the surface finishes and colors."
        
        base_rewrite_prompt += "\n\n**Important:** Output your prompt as a single detailed paragraph optimized for photorealistic interior rendering. Emphasize that the layout must remain unchanged."
        
        # Get enhanced prompt
        rewritten_prompt_response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=base_rewrite_prompt
        )
        rewritten_prompt = rewritten_prompt_response.text
        logger.info(f"Enhanced prompt: {rewritten_prompt}")

        model = "gemini-3-pro-image-preview"
        
        # Build content parts
        content_parts = [types.Part.from_text(text=rewritten_prompt)]
        content_parts.extend(reference_images)

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

        # Generate versioned filename
        version = get_next_version_number(tool_context, inputs.asset_name)
        artifact_filename = create_versioned_filename(inputs.asset_name, version)
        logger.info(f"Generating rendering with artifact filename: {artifact_filename} (version {version})")

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
                
                # Create a Part object from the inline data
                # The inline_data already contains the mime_type from the API response
                image_part = types.Part(inline_data=inline_data)
                
                try:
                    # Save the image as an artifact
                    version = await tool_context.save_artifact(
                        filename=artifact_filename, 
                        artifact=image_part
                    )
                    
                    # Update version tracking
                    update_asset_version(tool_context, inputs.asset_name, version, artifact_filename)
                    
                    # Store in session state
                    tool_context.state["last_generated_rendering"] = artifact_filename
                    tool_context.state["current_asset_name"] = inputs.asset_name
                    
                    logger.info(f"Saved rendering as artifact '{artifact_filename}' (version {version})")
                    
                    return f"✅ Renovation rendering generated successfully!\n\nThe rendering has been saved and is available in the artifacts panel. Artifact name: {inputs.asset_name} (version {version}).\n\nNote: The image is stored as an artifact and can be accessed through the session artifacts, not as a direct image link."
                    
                except Exception as e:
                    logger.error(f"Error saving artifact: {e}")
                    return f"Error saving rendering as artifact: {e}"
            else:
                # Log any text responses
                if hasattr(chunk, 'text') and chunk.text:
                    logger.info(f"Model response: {chunk.text}")
                
        return "No rendering was generated. Please try again with a more detailed prompt."
        
    except Exception as e:
        logger.error(f"Error in generate_renovation_rendering: {e}")
        return f"An error occurred while generating the rendering: {e}"


# ============================================================================
# Image Editing Tool
# ============================================================================

async def edit_renovation_rendering(tool_context: ToolContext, inputs: EditRenovationRenderingInput) -> str:
    """
    Edits an existing renovation rendering based on feedback or refinements.
    
    This tool allows iterative improvements to the rendered image, such as 
    changing colors, materials, lighting, or layout elements.
    """
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set.")

    logger.info("Starting renovation rendering edit")

    try:
        client = genai.Client()
        
        # Handle inputs that might come as dict instead of Pydantic model
        if isinstance(inputs, dict):
            inputs = EditRenovationRenderingInput(**inputs)
        
        # Get artifact_filename from session state if not provided
        artifact_filename = inputs.artifact_filename
        if not artifact_filename:
            artifact_filename = tool_context.state.get("last_generated_rendering")
            if not artifact_filename:
                return "❌ No artifact_filename provided and no previous rendering found in session. Please generate a rendering first or specify the artifact filename."
            logger.info(f"Using last generated rendering from session: {artifact_filename}")
        
        # Load the existing rendering
        logger.info(f"Loading artifact: {artifact_filename}")
        try:
            loaded_image_part = await tool_context.load_artifact(artifact_filename)
            if not loaded_image_part:
                return f"❌ Could not find rendering artifact: {artifact_filename}"
        except Exception as e:
            logger.error(f"Error loading artifact: {e}")
            return f"Error loading rendering artifact: {e}"

        # Handle reference image if specified
        reference_image_part = None
        if inputs.reference_image_filename:
            if inputs.reference_image_filename == "latest":
                ref_filename = get_latest_reference_image_filename(tool_context)
            else:
                ref_filename = inputs.reference_image_filename
            
            if ref_filename:
                reference_image_part = await load_reference_image(tool_context, ref_filename)
                if reference_image_part:
                    logger.info(f"Using reference image for editing: {ref_filename}")

        model = "gemini-3-pro-image-preview"

        # Build content parts
        content_parts = [loaded_image_part, types.Part.from_text(text=inputs.prompt)]
        if reference_image_part:
            content_parts.append(reference_image_part)

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
                # Extract from filename
                base_name = artifact_filename.split('_v')[0] if '_v' in artifact_filename else "renovation_rendering"
                asset_name = base_name
        
        version = get_next_version_number(tool_context, asset_name)
        edited_artifact_filename = create_versioned_filename(asset_name, version)
        logger.info(f"Editing rendering with artifact filename: {edited_artifact_filename} (version {version})")

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
                # The inline_data already contains the mime_type from the API response
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
                    tool_context.state["last_generated_rendering"] = edited_artifact_filename
                    tool_context.state["current_asset_name"] = asset_name
                    
                    logger.info(f"Saved edited rendering as artifact '{edited_artifact_filename}' (version {version})")
                    
                    return f"✅ Rendering edited successfully!\n\nThe updated rendering has been saved and is available in the artifacts panel. Artifact name: {asset_name} (version {version}).\n\nNote: The image is stored as an artifact and can be accessed through the session artifacts, not as a direct image link."
                    
                except Exception as e:
                    logger.error(f"Error saving edited artifact: {e}")
                    return f"Error saving edited rendering as artifact: {e}"
            else:
                # Log any text responses
                if hasattr(chunk, 'text') and chunk.text:
                    logger.info(f"Model response: {chunk.text}")
                
        return "No edited rendering was generated. Please try again."
        
    except Exception as e:
        logger.error(f"Error in edit_renovation_rendering: {e}")
        return f"An error occurred while editing the rendering: {e}"


# ============================================================================
# Utility Tools
# ============================================================================

async def list_renovation_renderings(tool_context: ToolContext) -> str:
    """Lists all renovation renderings created in this session."""
    return get_asset_versions_info(tool_context)


async def list_reference_images(tool_context: ToolContext) -> str:
    """Lists all reference images (current room photos & inspiration) uploaded in this session."""
    return get_reference_images_info(tool_context)


async def save_uploaded_image_as_artifact(
    tool_context: ToolContext,
    image_data: str,
    artifact_name: str,
    image_type: str = "current_room"
) -> str:
    """
    Saves an uploaded image as a named artifact for later use in editing.
    
    This tool is used when the Visual Assessor detects an uploaded image
    and wants to make it available for the Project Coordinator to edit.
    
    Args:
        tool_context: The tool context
        image_data: Base64 encoded image data or image bytes
        artifact_name: Name to save the artifact as (e.g., "current_room_1", "inspiration_1")
        image_type: Type of image ("current_room" or "inspiration")
    
    Returns:
        Success message with the artifact filename
    """
    try:
        # Create a Part from the image data
        # Note: This assumes image_data is already in the right format
        # In practice, we'll get this from the message content
        
        # Save as artifact
        await tool_context.save_artifact(
            filename=artifact_name,
            artifact=image_data
        )
        
        # Track in state
        if "uploaded_images" not in tool_context.state:
            tool_context.state["uploaded_images"] = {}
        
        tool_context.state["uploaded_images"][artifact_name] = {
            "type": image_type,
            "filename": artifact_name
        }
        
        if image_type == "current_room":
            tool_context.state["current_room_artifact"] = artifact_name
        elif image_type == "inspiration":
            tool_context.state["inspiration_artifact"] = artifact_name
        
        logger.info(f"Saved uploaded image as artifact: {artifact_name}")
        
        return f"✅ Image saved as artifact: {artifact_name} (type: {image_type}). This can now be used for editing."
        
    except Exception as e:
        logger.error(f"Error saving uploaded image: {e}")
        return f"❌ Error saving uploaded image: {e}"

