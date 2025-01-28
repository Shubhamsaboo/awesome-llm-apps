from typing import Optional, List, Dict, Any
import os
import time
import streamlit as st
from openai import OpenAI
import anthropic
from dotenv import load_dotenv
import json

# Model Constants
DEEPSEEK_MODEL: str = "deepseek-reasoner"
CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"

# Load environment variables
load_dotenv()

class ModelChain:
    def __init__(self, deepseek_api_key: str, anthropic_api_key: str) -> None:
        self.client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"  # Added /v1 to the base URL
        )
        self.claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        self.deepseek_messages: List[Dict[str, str]] = []
        self.claude_messages: List[Dict[str, Any]] = []
        self.current_model: str = CLAUDE_MODEL
        self.show_reasoning = True

    def get_deepseek_reasoning(self, user_input: str) -> str:    
        start_time = time.time()

        try:
            # Debug print
            st.write("Sending request to DeepSeek with messages:", json.dumps(self.deepseek_messages, indent=2))
            
            deepseek_response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at reasoning and thinking from first principles."},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=1,
                temperature=0.7,  # Added temperature
                stream=False      # Explicitly set stream to False
            )
            
            # Debug print
            st.write("Raw response from DeepSeek:", deepseek_response)
            
            reasoning_content = deepseek_response.choices[0].message.reasoning_content
            
            # Create expander for reasoning
            with st.expander("💭 Reasoning Process", expanded=True):
                st.markdown(reasoning_content)
                elapsed_time = time.time() - start_time
                time_str = f"{elapsed_time/60:.1f} minutes" if elapsed_time >= 60 else f"{elapsed_time:.1f} seconds"
                st.caption(f"⏱️ Thought for {time_str}")

            return reasoning_content

        except Exception as e:
            st.error(f"Error getting DeepSeek reasoning: {str(e)}")
            st.error("Full error details:")
            st.exception(e)
            return "Error occurred while getting reasoning"

    def get_claude_response(self, user_input: str, reasoning: str) -> str:
        user_message = {
            "role": "user",
            "content": [{"type": "text", "text": user_input}]
        }

        assistant_prefill = {
            "role": "assistant",
            "content": [{"type": "text", "text": f"<thinking>{reasoning}</thinking>"}]
        }

        messages = [user_message, assistant_prefill]
        
        try:
            # Create expander for Claude's response
            with st.expander("🤖 Claude's Response", expanded=True):
                response_placeholder = st.empty()
                
                with self.claude_client.messages.stream(
                    model=self.current_model,
                    messages=messages,
                    max_tokens=8000
                ) as stream:
                    full_response = ""
                    for text in stream.text_stream:
                        full_response += text
                        response_placeholder.markdown(full_response)

                # Store the messages in Claude's history only
                self.claude_messages.extend([user_message, {
                    "role": "assistant", 
                    "content": [{"type": "text", "text": full_response}]
                }])

                return full_response

        except Exception as e:
            st.error(f"Error in Claude response: {str(e)}")
            return "Error occurred while getting response"

def main() -> None:
    """Main function to run the Streamlit app."""
    st.title("🤖 AI Assistant")

    # Sidebar for API keys
    with st.sidebar:
        st.header("⚙️ Configuration")
        deepseek_api_key = st.text_input("DeepSeek API Key", type="password")
        anthropic_api_key = st.text_input("Anthropic API Key", type="password")
        show_reasoning = st.toggle("Show Reasoning Process", value=True)
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.experimental_rerun()

    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        if not deepseek_api_key or not anthropic_api_key:
            st.error("⚠️ Please enter both API keys in the sidebar.")
            return

        # Initialize ModelChain
        chain = ModelChain(deepseek_api_key, anthropic_api_key)

        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            if show_reasoning:
                with st.spinner("🤔 Thinking..."):
                    reasoning = chain.get_deepseek_reasoning(prompt)
            else:
                reasoning = ""
            
            with st.spinner("✍️ Responding..."):
                response = chain.get_claude_response(prompt, reasoning)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()