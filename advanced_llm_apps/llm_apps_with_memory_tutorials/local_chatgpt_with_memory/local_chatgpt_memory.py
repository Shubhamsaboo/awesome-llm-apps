import streamlit as st
from mem0 import Memory
from litellm import completion

# Configuration for Memory
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "local-chatgpt-memory",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 768,
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.1:latest",
            "temperature": 0,
            "max_tokens": 8000,
            "ollama_base_url": "http://localhost:11434",  # Ensure this URL is correct
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            # Alternatively, you can use "snowflake-arctic-embed:latest"
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "version": "v1.1"
}

st.title("Local ChatGPT using Llama 3.1 with Personal Memory 🧠")
st.caption("Each user gets their own personalized memory space!")

# Initialize session state for chat history and previous user ID
if "messages" not in st.session_state:
    st.session_state.messages = []
if "previous_user_id" not in st.session_state:
    st.session_state.previous_user_id = None

# Sidebar for user authentication
with st.sidebar:
    st.title("User Settings")
    user_id = st.text_input("Enter your Username", key="user_id")
    
    # Check if user ID has changed
    if user_id != st.session_state.previous_user_id:
        st.session_state.messages = []  # Clear chat history
        st.session_state.previous_user_id = user_id  # Update previous user ID
    
    if user_id:
        st.success(f"Logged in as: {user_id}")
        
        # Initialize Memory with the configuration
        m = Memory.from_config(config)
        
        # Memory viewing section
        st.header("Memory Context")
        if st.button("View My Memory"):
            memories = m.get_all(user_id=user_id)
            if memories and "results" in memories:
                st.write(f"Memory history for **{user_id}**:")
                for memory in memories["results"]:
                    if "memory" in memory:
                        st.write(f"- {memory['memory']}")

# Main chat interface
if user_id:  # Only show chat interface if user is "logged in"
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("What is your message?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Add to memory
        m.add(prompt, user_id=user_id)
        
        # Get context from memory
        memories = m.get_all(user_id=user_id)
        context = ""
        if memories and "results" in memories:
            for memory in memories["results"]:
                if "memory" in memory:
                    context += f"- {memory['memory']}\n"

        # Generate assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            try:
                response = completion(
                    model="ollama/llama3.1:latest",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant with access to past conversations. Use the context provided to give personalized responses."},
                        {"role": "user", "content": f"Context from previous conversations with {user_id}: {context}\nCurrent message: {prompt}"}
                    ],
                    api_base="http://localhost:11434",
                    stream=True
                )
                
                # Process streaming response
                for chunk in response:
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.get('content', '')
                        if content:
                            full_response += content
                            message_placeholder.markdown(full_response + "▌")
                
                # Final update
                message_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")
                full_response = "I apologize, but I encountered an error generating the response."
                message_placeholder.markdown(full_response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # Add response to memory
        m.add(f"Assistant: {full_response}", user_id=user_id)

else:
    st.info("👈 Please enter your username in the sidebar to start chatting!")