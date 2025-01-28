from typing import Optional, List, Dict, Any
import os
import time
import streamlit as st
from openai import OpenAI
import anthropic
from dotenv import load_dotenv
from rich import print as rprint
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

# Model Constants
DEEPSEEK_MODEL: str = "deepseek-reasoner"
CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"

# Load environment variables
load_dotenv()

class ModelChain:
    """
    A class to handle interactions with DeepSeek and Claude models.
    """
    def __init__(self, deepseek_api_key: str, anthropic_api_key: str) -> None:
        """
        Initialize the ModelChain with API keys.
        
        Args:
            deepseek_api_key: API key for DeepSeek
            anthropic_api_key: API key for Anthropic
        """
        self.deepseek_client = OpenAI(
            api_key=deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        self.claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        self.deepseek_messages: List[Dict[str, str]] = []
        self.claude_messages: List[Dict[str, Any]] = []
        self.current_model: str = CLAUDE_MODEL
        self.show_reasoning = True

    def set_model(self, model_name):
        self.current_model = model_name

    def get_model_display_name(self):
        return self.current_model

    def get_deepseek_reasoning(self, user_input: str) -> str:
        """
        Get reasoning from DeepSeek model.
        
        Args:
            user_input: User's input text
            
        Returns:
            str: Reasoning content from DeepSeek
        """
        start_time = time.time()
        self.deepseek_messages.append({"role": "user", "content": user_input})

        if self.show_reasoning:
            rprint("\n[blue]Reasoning Process[/]")

        response = self.deepseek_client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            max_tokens=1,
            messages=self.deepseek_messages,
            stream=True
        )

        reasoning_content = ""
        final_content = ""
        reasoning_placeholder = st.empty()

        for chunk in response:
            if chunk.choices[0].delta.reasoning_content:
                reasoning_piece = chunk.choices[0].delta.reasoning_content
                reasoning_content += reasoning_piece
                reasoning_placeholder.markdown(reasoning_content)
                if self.show_reasoning:
                    print(reasoning_piece, end="", flush=True)
            elif chunk.choices[0].delta.content:
                final_content += chunk.choices[0].delta.content

        elapsed_time = time.time() - start_time
        if elapsed_time >= 60:
            time_str = f"{elapsed_time/60:.1f} minutes"
        else:
            time_str = f"{elapsed_time:.1f} seconds"
        rprint(f"\n\n[yellow]Thought for {time_str}[/]")

        if self.show_reasoning:
            print("\n")
        return reasoning_content

    def get_claude_response(self, user_input: str, reasoning: str) -> str:
        """
        Get response from Claude model.
        
        Args:
            user_input: User's input text
            reasoning: Reasoning from DeepSeek
            
        Returns:
            str: Claude's response
        """
        user_message = {
            "role": "user",
            "content": [{"type": "text", "text": user_input}]
        }

        assistant_prefill = {
            "role": "assistant",
            "content": [{"type": "text", "text": f"<thinking>{reasoning}</thinking>"}]
        }

        messages = [user_message, assistant_prefill]
        response_placeholder = st.empty()
        
        rprint(f"[green]{self.get_model_display_name()}[/]", end="")

        try:
            with self.claude_client.messages.stream(
                model=self.current_model,
                messages=messages,
                max_tokens=8000
            ) as stream:
                full_response = ""
                for text in stream.text_stream:
                    full_response += text
                    response_placeholder.markdown(full_response)

            self.claude_messages.extend([user_message, {
                "role": "assistant", 
                "content": [{"type": "text", "text": full_response}]
            }])
            self.deepseek_messages.append({"role": "assistant", "content": full_response})

            print("\n")
            return full_response

        except Exception as e:
            rprint(f"\n[red]Error in response: {str(e)}[/]")
            return "Error occurred while getting response"

def main() -> None:
    """Main function to run the Streamlit app."""
    st.title("AI Assistant")

    # Sidebar for API keys
    with st.sidebar:
        st.header("API Configuration")
        deepseek_api_key = st.text_input("DeepSeek API Key", type="password")
        anthropic_api_key = st.text_input("Anthropic API Key", type="password")
        show_reasoning = st.toggle("Show Reasoning Process", value=True)
        
        if st.button("Clear Chat History"):
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
            st.error("Please enter both API keys in the sidebar.")
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
                reasoning = chain.get_deepseek_reasoning(prompt)
            else:
                reasoning = ""
            
            response = chain.get_claude_response(prompt, reasoning)
            st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()