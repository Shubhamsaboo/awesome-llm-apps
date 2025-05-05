import streamlit as st
from openai import OpenAI
from agents import Agent, function_tool, Runner
import asyncio
import os
import base64
from typing import List, Dict, Any
from dotenv import load_dotenv
import re
from PIL import Image
import io

# Load environment variables from .env file
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="AI Creative Director",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to initialize OpenAI client with API key
def get_openai_client():
    api_key = st.session_state.get("openai_api_key", "")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY", "")
    
    if not api_key:
        st.sidebar.error("⚠️ No API key found. Please enter your OpenAI API key in the sidebar.")
        return None
    
    return OpenAI(api_key=api_key)

@function_tool
def generate_image(prompt: str) -> object:
    """Generates image(s) from text prompt using GPT Image model.
    
    Args:
        prompt: Detailed description of desired image(s)
        
    Returns:
        OpenAI API response object containing image data (e.g., b64_json or url).
    """
    client = get_openai_client()
    if not client:
        return "Error: No valid OpenAI API key provided"
    
    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            quality="high",
            n=3,
            size="1024x1024"
        )
        
        return result
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return f"Error: {str(e)}"


# Writing Agent that creates ad scripts
writing_agent = Agent(
    name="WritingAgent",
    instructions="""
You are a creative ad script writer on the AI Creative Director Agent Team. Your task is to create compelling, engaging scripts for advertisements.

When given a request to create an ad:
1. Create a script that is appropriate for the requested length (e.g., 15 seconds, 30 seconds).
2. Focus on creating memorable, impactful language that highlights the product's unique selling points.
3. Consider the target audience and adapt your tone accordingly.
4. Structure the script with clear sections (intro, body, call to action).
5. Include any sound effects or music cues in [brackets] if appropriate.

Your output MUST include:
1. The complete ad script
2. A brief explanation of why you chose this approach
3. Analysis of how this script would appeal to the target audience
4. Suggestions for tone, pacing, and delivery

Format your response as follows:

## Ad Script
[Your complete script here with any sound effects in brackets]

## Creative Rationale
[Explanation of your creative choices and approach]

## Target Audience Appeal
[Analysis of how this script connects with the intended audience]

## Delivery Notes
[Suggestions for how the script should be performed/delivered]
"""
)

# Design Agent with image generation capability
design_agent = Agent(
    name="DesignAgent",
    instructions="""
You are a visual design consultant on the AI Creative Director Agent Team. Your job is to take an ad script and provide visual inspiration for how it could be brought to life.

When given an ad script:
1. Analyze the tone, style, and key messages of the script.
2. Suggest minor tweaks or enhancements to make the script more visually impactful.
3. Create detailed prompts for 2-3 images that would complement the ad.
4. IMPORTANT: You MUST call the `generate_image` tool with the prompts you created to generate the visual concepts.
5. Explain your design choices and how they enhance the script's message in your final text output. DO NOT embed the image data itself in your text response.

Your response MUST be structured as follows:

## Visual Concept
[Brief overview of your visual approach and how it aligns with the script]

## Script Feedback
[Brief constructive feedback on the script with any suggested visual tweaks]

## Image Prompts Used
[List or describe the prompts you used for the `generate_image` tool call]

## Style Guide
- Color Palette: [Suggest 3-4 colors with hex codes if possible]
- Typography: [Font style recommendations]
- Visual Elements: [Key visual elements to include]
- Mood/Atmosphere: [Overall feeling the visuals should convey]

IMPORTANT: Ensure you call the `generate_image` tool. Your text output should focus on the design rationale and prompts used.
""",
    tools=[generate_image],
)

# Function to run the sequential agents
async def run_sequential_agents(user_prompt: str, target_audience: str, brand_info: str) -> Dict[str, Any]:
    """Run the writing agent followed by the design agent in sequence.
    
    Args:
        user_prompt: The user's initial prompt (e.g., "help me make a 15 sec ad for my makeup brand")
        target_audience: Information about the target audience
        brand_info: Information about the brand
        
    Returns:
        Dictionary containing the script, design feedback, and image URLs
    """
    # Enhance the prompt with additional information if provided
    enhanced_prompt = user_prompt
    if target_audience.strip():
        enhanced_prompt += f"\n\nTarget Audience: {target_audience}"
    if brand_info.strip():
        enhanced_prompt += f"\n\nBrand Information: {brand_info}"
    
    # Step 1: Run the writing agent to create the script
    with st.spinner("🖋️ Creative Director is writing your ad script..."):
        writing_result = await Runner.run(writing_agent, enhanced_prompt)
        script = writing_result.final_output
    
    # Step 2: Run the design agent with the script as input
    with st.spinner("🎨 Creative Director is designing visual concepts..."):
        design_prompt = f"Here's an ad script I'd like you to provide visual inspiration for: {script}"
        if target_audience.strip():
            design_prompt += f"\n\nTarget Audience: {target_audience}"
        if brand_info.strip():
            design_prompt += f"\n\nBrand Information: {brand_info}"
            
        design_result = await Runner.run(design_agent, design_prompt)
        design_feedback = design_result.final_output
        
        # --- Find the output from the generate_image tool call --- 
        # This part depends on how the 'agents' library structures the result.
        # We'll assume the tool outputs are stored in a list or dict within design_result.
        # Let's look for an attribute like 'tool_outputs' or 'tool_calls'
        # This is an educated guess - adjust based on actual library structure if needed.
        image_data_object = None
        if hasattr(design_result, 'tool_outputs') and design_result.tool_outputs:
             # Assuming tool_outputs is a list of outputs, find the one from generate_image
            for output in design_result.tool_outputs:
                # Check if the output corresponds to 'generate_image' 
                # (Needs specific check based on library's structure, maybe output.tool_name == 'generate_image')
                # For now, let's assume the *first* tool output is the one we want, 
                # if it looks like an OpenAI image response (has a 'data' attribute).
                if hasattr(output, 'data'): # Basic check for OpenAI image response structure
                    image_data_object = output
                    break # Found it
        elif hasattr(design_result, 'tool_calls') and design_result.tool_calls:
             # Alternative structure some libraries use
             for call in design_result.tool_calls:
                 if call.tool_name == 'generate_image' and hasattr(call, 'result') and hasattr(call.result, 'data'):
                     image_data_object = call.result
                     break
        # --- End Finding Tool Output --- 

    return {
        "script": script,
        "design_feedback": design_feedback, 
        "image_data": image_data_object # Pass the structured data object
    }

# Streamlit UI
async def main():
    # Sidebar for API key and settings
    with st.sidebar:
        st.title("AI Creative Director Agent Team")
        st.markdown("---")
        
        # API Key input
        st.subheader("🔑 API Settings")
        api_key = st.text_input(
            "OpenAI API Key", 
            type="password",
            placeholder="sk-...",
            help="Enter your OpenAI API key. Your key is not stored and is only used for this session.",
            key="openai_api_key"
        )
        
        if api_key:
            st.success("API Key provided! ✅")
        
        st.markdown("---")
        
        # About section
        st.subheader("ℹ️ About")
        st.markdown("""
        **AI Creative Director** helps you create professional ad concepts with:
        - Script writing
        - Visual design
        - Image generation
        
        Created with OpenAI Agents SDK & GPT Image 1
        """)
        
        st.markdown("---")
        st.caption("© 2025 AI Creative Director Team")
    
    # Main content area
    st.title("🎬 AI Creative Director Agent Team")
    st.subheader("From Concept to Visual in Seconds")
    
    st.info(
        "**How it works:** Enter your ad concept below, and our AI Creative Director team will craft a professional script and generate visual inspiration for your advertisement."
    )
    
    # Create two columns for input fields
    col1, col2 = st.columns(2)
    
    with col1:
        prompt = st.text_area(
            "📝 Describe the ad you want to create:", 
            placeholder="Help me make a 15 sec ad for my makeup brand",
            height=100
        )
        
    with col2:
        target_audience = st.text_area(
            "👥 Target Audience (optional):",
            placeholder="E.g., Women 25-34 interested in beauty and self-care",
            height=100
        )
        
    brand_info = st.text_area(
        "🏢 Brand Information (optional):",
        placeholder="E.g., ColorBurst is a new makeup brand focused on natural ingredients and vibrant colors",
        height=75
    )
    
    # Create button with custom styling
    if st.button("✨ Create Ad Concept", type="primary", use_container_width=True):
        if not prompt.strip():
            st.error("Please enter an ad description")
            return
            
        if not get_openai_client():
            st.error("Please provide a valid OpenAI API key in the sidebar")
            return
        
        try:
            # Run the agents
            result = await run_sequential_agents(prompt, target_audience, brand_info)
            
            # Display results
            st.markdown("--- ")
            st.subheader("✨ Creative Results")
            
            # Use tabs for better organization
            script_tab, visual_tab = st.tabs(["🖋️ Ad Script", "🎨 Visual Concept"])
            
            with script_tab:
                st.markdown(result.get("script", "No script generated."))
            
            with visual_tab:
                design_text = result.get("design_feedback", "No visual feedback generated.")
                st.markdown(design_text)
                
                # --- Display images from structured data --- 
                st.markdown("--- ")
                st.markdown("### 🖼️ Generated Images")
                
                image_data = result.get("image_data")
                
                if image_data and hasattr(image_data, 'data') and image_data.data:
                    cols = st.columns(len(image_data.data))
                    for i, img_obj in enumerate(image_data.data):
                        if hasattr(img_obj, 'b64_json') and img_obj.b64_json:
                            try:
                                # Decode base64
                                image_bytes = base64.b64decode(img_obj.b64_json)
                                
                                # Use PIL to open the image from bytes
                                pil_image = Image.open(io.BytesIO(image_bytes))
                                
                                with cols[i]:
                                    st.image(pil_image, caption=f"Generated Concept {i+1}", use_column_width=True)
                            except Exception as e:
                                with cols[i]:
                                    st.warning(f"Could not decode/display image {i+1}: {e}")
                        else:
                             with cols[i]:
                                 st.info(f"Image {i+1} data not in expected format (b64_json).")
                else:
                    st.info("No generated image data found or it's in an unexpected format.")
                # --- End Display images --- 
                
            # Add a success message
            st.success("✅ Ad concept created successfully! Explore the tabs above to see the results.")
            
        except Exception as e:
            st.error(f"Error creating ad concept: {str(e)}")

# Command-line interface for testing
async def cli_main():
    user_prompt = input("Enter your ad request: ")
    print("\nProcessing your request...\n")
    
    result = await run_sequential_agents(user_prompt)
    
    print("\n=== AD SCRIPT ===\n")
    print(result["script"])
    
    print("\n=== VISUAL INSPIRATION ===\n")
    print(result["design_feedback"])

if __name__ == "__main__":
    # Check if running in Streamlit
    import sys
    if 'streamlit' in sys.modules:
        asyncio.run(main())
    else:
        # Run CLI version for testing
        asyncio.run(cli_main())
