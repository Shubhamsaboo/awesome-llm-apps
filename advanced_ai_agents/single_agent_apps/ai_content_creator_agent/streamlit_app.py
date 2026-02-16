import os

import streamlit as st

from agent_tools import _create_agent
from helper_functions import clear_temp_data


def main() -> None:
    st.set_page_config(page_title="Content Creator AI Agent", layout="centered")

    st.sidebar.title("API Keys")
    pexels_api_key = st.sidebar.text_input("Pexels API Key", type="password")
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

    st.sidebar.title("Instructions")
    st.sidebar.write(
        "Describe your idea, and this app will automatically generate either a multi-clip vertical video (reel) using stock video and voiceover, or a square image with text over a stock photo. Just enter your concept—like a motivational topic, a quote, or a theme—and let the AI create either a dynamic video or an eye-catching image using the Pexels library."
    )

    st.sidebar.caption(
        "Images and videos are sourced from Pexels. See the [Pexels License](https://www.pexels.com/license/) for usage terms and policy."
    )

    st.title("Content Creator AI Agent")
    

    user_prompt = st.text_area(
        "Describe the content (image or video or both) you want to create:",
        height=160,
        placeholder=(
            "Example: A motivational reel about staying consistent at the gym, "
            "or a quote image about focus and discipline..."
        ),
    )

    if st.button("Generate Content"):
        if not pexels_api_key:
            st.error("Please enter your Pexels API key in the sidebar.")
            return
        if not openai_api_key:
            st.error("Please enter your OpenAI API key in the sidebar.")
            return
        if not user_prompt.strip():
            st.error("Please enter a description for your content.")
            return

        # Initialize session state to track if agent has run
        st.session_state.agent_executed = False
        st.session_state.agent_result = None

        # Only execute agent if not already done
        if not st.session_state.agent_executed:
            
            agent = _create_agent(openai_api_key, pexels_api_key)
            all_updates = []

            with st.status("Analyzing prompt...", expanded=True) as status:
                st.write("Starting agent...")
                for chunk in agent.stream(
                    {"messages": [{"role": "user", "content": user_prompt.strip()}]},
                    stream_mode="updates",
                ):
                    
                    all_updates.append(chunk)
                    
                    # Derive status message from chunk type
                    for step, data in chunk.items():
                        messages = data.get("messages", [])
                        
                        if messages:
                            content_blocks = getattr(messages[-1], "content_blocks", [])
                            
                            for block in content_blocks:
                                b_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
                                
                                if b_type == "tool_call":
                                    name = block.get("name", "tool") if isinstance(block, dict) else getattr(block, "name", "tool")
                                    args = block.get("args", {}) if isinstance(block, dict) else getattr(block, "args", {})
                                    st.write(f"Calling **{name}**...")
                                    if args:
                                        st.caption("Inputs")
                                        st.json(args)
                                
                                elif b_type == "text":
                                    text_content = block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "")
                                    if text_content:
                                        with st.chat_message("assistant"):
                                            st.write(text_content)
                        else:
                            st.write(f"Processing step: **{step}**...")

                status.update(
                    label="Generation complete!",
                    state="complete",
                    expanded=False,
                )

            st.session_state.agent_executed = True
            st.session_state.agent_result = all_updates
                
    
    if st.session_state.get('agent_executed', False) and st.session_state.get('agent_result'):
        tool_names = []

        # Parse the chunks to find tool name and result
        for chunk in st.session_state.agent_result:
            for step, data in chunk.items():
                messages = data.get('messages', [])
                if messages:
                    content_blocks = messages[-1].content_blocks
                    
                    # Check for tool_call (tells us which tool was used)
                    for block in content_blocks:
                        if isinstance(block, dict) and block.get('type') == 'tool_call':
                            tool_name = block.get('name')
                            tool_names.append(tool_name)
                            st.write(f"🔧 Tool used: **{tool_name}**")
                        

        # Display based on tool type
        if 'create_reel' in tool_names:
            video_path = './output/generated_reel.mp4'
            if os.path.exists(video_path):
                st.success("✅ Reel saved successfully!")
                st.write("Reel preview (saved in output folder as generated_reel.mp4):")
                st.video(video_path)
                with open(video_path, "rb") as video_file:
                    st.download_button(
                        label="📥 Download Reel",
                        data=video_file.read(),
                        file_name="generated_reel.mp4",
                        mime="video/mp4",
                    )
            else:
                st.error("❌ Video file not found. Check the logs.")
        
        if 'create_image' in tool_names:
            image_path = './output/generated_image.jpg'
            if os.path.exists(image_path):                
                st.success("✅ Image saved successfully!")
                st.write("Image preview (saved in output folder as generated_image.jpg):")
                st.image(image_path, use_container_width=True)
                with open(image_path, "rb") as img_file:
                    st.download_button(
                        label="📥 Download Image",
                        data=img_file.read(),
                        file_name="generated_image.jpg",
                        mime="image/jpeg",
                    )
            else:
                st.error("❌ Image file not found. Check the logs.")
        
        if tool_names == []:
            st.warning("⚠️ No tool was called or tool result not found.")
            # Optionally show debug info
            with st.expander("Debug Info"):
                for chunk in st.session_state.agent_result:
                    st.write(chunk)
        
        # Clear temporary data (comment out if you want to keep the temp data)
        
        if st.button("Clear Temporary Data", width="stretch"):
            try:
                clear_temp_data()
                st.success("✅ Temporary data cleared successfully!")
            except Exception as e:
                st.error(f"❌ Error clearing temporary data: {e}")
       
    


if __name__ == "__main__":
    main()

