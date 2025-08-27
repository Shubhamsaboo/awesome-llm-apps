import streamlit as st
import asyncio
import os
from datetime import datetime
from agents import Agent, Runner, SQLiteSession
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Session Management Demo",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize agents
@st.cache_resource
def initialize_agents():
    """Initialize AI agents for different use cases"""
    
    main_agent = Agent(
        name="Session Demo Assistant",
        instructions="""
        You are a helpful assistant demonstrating session memory capabilities.
        
        Remember previous conversation context and reference it when relevant.
        Reply concisely but show that you remember previous interactions.
        Be friendly and professional.
        """
    )
    
    support_agent = Agent(
        name="Support Agent",
        instructions="You are a customer support representative. Help with account and technical issues. Be helpful and solution-oriented."
    )
    
    sales_agent = Agent(
        name="Sales Agent", 
        instructions="You are a sales representative. Help with product information and purchases. Be enthusiastic and informative."
    )
    
    return main_agent, support_agent, sales_agent

# Session management functions
class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    def get_session(self, session_id: str, db_file: str = "demo_sessions.db"):
        """Get or create a session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = SQLiteSession(session_id, db_file)
        return self.sessions[session_id]
    
    async def clear_session(self, session_id: str):
        """Clear a specific session"""
        if session_id in self.sessions:
            await self.sessions[session_id].clear_session()
            del self.sessions[session_id]
    
    async def get_session_items(self, session_id: str, limit: int = None):
        """Get conversation items from a session"""
        if session_id in self.sessions:
            return await self.sessions[session_id].get_items(limit=limit)
        return []
    
    async def add_custom_items(self, session_id: str, items: list):
        """Add custom items to a session"""
        if session_id in self.sessions:
            await self.sessions[session_id].add_items(items)
    
    async def pop_last_item(self, session_id: str):
        """Remove the last item from a session"""
        if session_id in self.sessions:
            return await self.sessions[session_id].pop_item()
        return None

# Initialize session manager
if 'session_manager' not in st.session_state:
    st.session_state.session_manager = SessionManager()

# Main UI
def main():
    st.title("🔄 Session Management Demo")
    st.markdown("**Demonstrates OpenAI Agents SDK session capabilities**")
    
    # Initialize agents
    main_agent, support_agent, sales_agent = initialize_agents()
    
    # Sidebar for session configuration
    with st.sidebar:
        st.header("⚙️ Session Configuration")
        
        demo_type = st.selectbox(
            "Select Demo Type",
            ["Basic Sessions", "Memory Operations", "Multi Sessions"]
        )
        
        if demo_type == "Basic Sessions":
            session_type = st.radio(
                "Session Type",
                ["In-Memory", "Persistent"]
            )
        
        st.divider()
        
        # Session controls
        st.subheader("Session Controls")
        
        if st.button("🗑️ Clear All Sessions"):
            with st.spinner("Clearing sessions..."):
                for session_id in list(st.session_state.session_manager.sessions.keys()):
                    asyncio.run(st.session_state.session_manager.clear_session(session_id))
                st.success("All sessions cleared!")
                st.rerun()
    
    # Main content area
    if demo_type == "Basic Sessions":
        render_basic_sessions(main_agent)
    elif demo_type == "Memory Operations":
        render_memory_operations(main_agent)
    elif demo_type == "Multi Sessions":
        render_multi_sessions(support_agent, sales_agent)

def render_basic_sessions(agent):
    """Render the basic sessions demo"""
    st.header("📝 Basic Sessions Demo")
    st.markdown("Demonstrates fundamental session memory with automatic conversation history.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💾 In-Memory Session")
        st.caption("Temporary session storage (lost when app restarts)")
        
        session_id = "in_memory_demo"
        
        with st.form("in_memory_form"):
            user_input = st.text_input("Your message:", key="in_memory_input")
            submitted = st.form_submit_button("Send Message")
            
            if submitted and user_input:
                with st.spinner("Processing..."):
                    session = st.session_state.session_manager.get_session(session_id)
                    result = asyncio.run(Runner.run(agent, user_input, session=session))
                    
                    st.success("Message sent!")
                    st.write(f"**Assistant:** {result.final_output}")
        
        # Show conversation history
        if st.button("📋 Show Conversation", key="show_in_memory"):
            items = asyncio.run(st.session_state.session_manager.get_session_items(session_id))
            if items:
                st.write("**Conversation History:**")
                for i, item in enumerate(items, 1):
                    role_emoji = "👤" if item['role'] == 'user' else "🤖"
                    st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {item['content']}")
            else:
                st.info("No conversation history yet.")
    
    with col2:
        st.subheader("💽 Persistent Session")
        st.caption("File-based storage (survives app restarts)")
        
        session_id = "persistent_demo"
        
        with st.form("persistent_form"):
            user_input = st.text_input("Your message:", key="persistent_input")
            submitted = st.form_submit_button("Send Message")
            
            if submitted and user_input:
                with st.spinner("Processing..."):
                    session = st.session_state.session_manager.get_session(session_id, "persistent_demo.db")
                    result = asyncio.run(Runner.run(agent, user_input, session=session))
                    
                    st.success("Message sent!")
                    st.write(f"**Assistant:** {result.final_output}")
        
        # Show conversation history
        if st.button("📋 Show Conversation", key="show_persistent"):
            items = asyncio.run(st.session_state.session_manager.get_session_items(session_id))
            if items:
                st.write("**Conversation History:**")
                for i, item in enumerate(items, 1):
                    role_emoji = "👤" if item['role'] == 'user' else "🤖"
                    st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {item['content']}")
            else:
                st.info("No conversation history yet.")

def render_memory_operations(agent):
    """Render the memory operations demo"""
    st.header("🧠 Memory Operations Demo")
    st.markdown("Demonstrates advanced session memory operations including item manipulation and corrections.")
    
    session_id = "memory_operations_demo"
    
    # Main conversation area
    st.subheader("💬 Conversation")
    with st.form("memory_conversation"):
        user_input = st.text_input("Your message:")
        submitted = st.form_submit_button("Send Message")
        
        if submitted and user_input:
            with st.spinner("Processing..."):
                session = st.session_state.session_manager.get_session(session_id)
                result = asyncio.run(Runner.run(agent, user_input, session=session))
                
                st.success("Message sent!")
                st.write(f"**Assistant:** {result.final_output}")
    
    # Memory operations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Memory Inspection")
        
        if st.button("🔍 Get All Items"):
            items = asyncio.run(st.session_state.session_manager.get_session_items(session_id))
            if items:
                st.write(f"**Total items:** {len(items)}")
                for i, item in enumerate(items, 1):
                    role_emoji = "👤" if item['role'] == 'user' else "🤖"
                    content_preview = item['content'][:100] + "..." if len(item['content']) > 100 else item['content']
                    st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {content_preview}")
            else:
                st.info("No items in session yet.")
        
        # Get limited items
        limit = st.number_input("Get last N items:", min_value=1, max_value=20, value=3)
        if st.button("📋 Get Recent Items"):
            items = asyncio.run(st.session_state.session_manager.get_session_items(session_id, limit=limit))
            if items:
                st.write(f"**Last {len(items)} items:**")
                for i, item in enumerate(items, 1):
                    role_emoji = "👤" if item['role'] == 'user' else "🤖"
                    st.write(f"{i}. {role_emoji} **{item['role'].title()}:** {item['content']}")
            else:
                st.info("No items to show.")
    
    with col2:
        st.subheader("✏️ Memory Manipulation")
        
        # Add custom items
        st.write("**Add Custom Items:**")
        with st.form("add_items_form"):
            user_content = st.text_area("User message to add:")
            assistant_content = st.text_area("Assistant response to add:")
            add_submitted = st.form_submit_button("➕ Add Items")
            
            if add_submitted and user_content and assistant_content:
                custom_items = [
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": assistant_content}
                ]
                asyncio.run(st.session_state.session_manager.add_custom_items(session_id, custom_items))
                st.success("Custom items added!")
        
        # Pop last item (correction)
        if st.button("↶ Undo Last Response"):
            popped_item = asyncio.run(st.session_state.session_manager.pop_last_item(session_id))
            if popped_item:
                st.success(f"Removed: {popped_item['role']} - {popped_item['content'][:50]}...")
            else:
                st.warning("No items to remove.")
        
        # Clear session
        if st.button("🗑️ Clear Session"):
            asyncio.run(st.session_state.session_manager.clear_session(session_id))
            st.success("Session cleared!")

def render_multi_sessions(support_agent, sales_agent):
    """Render the multi-sessions demo"""
    st.header("👥 Multi Sessions Demo")
    st.markdown("Demonstrates managing multiple conversations and different agent contexts.")
    
    tab1, tab2, tab3 = st.tabs(["👤 Multi-User", "🏢 Context-Based", "🔄 Agent Handoff"])
    
    with tab1:
        st.subheader("Different Users, Separate Sessions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**👩 Alice's Session**")
            alice_session_id = "user_alice"
            
            with st.form("alice_form"):
                alice_input = st.text_input("Alice's message:", key="alice_input")
                alice_submitted = st.form_submit_button("Send as Alice")
                
                if alice_submitted and alice_input:
                    with st.spinner("Processing Alice's message..."):
                        session = st.session_state.session_manager.get_session(alice_session_id, "multi_user.db")
                        result = asyncio.run(Runner.run(support_agent, alice_input, session=session))
                        st.write(f"**Support:** {result.final_output}")
            
            if st.button("📋 Alice's History", key="alice_history"):
                items = asyncio.run(st.session_state.session_manager.get_session_items(alice_session_id))
                for item in items:
                    role_emoji = "👩" if item['role'] == 'user' else "🛠️"
                    st.write(f"{role_emoji} **{item['role'].title()}:** {item['content']}")
        
        with col2:
            st.write("**👨 Bob's Session**")
            bob_session_id = "user_bob"
            
            with st.form("bob_form"):
                bob_input = st.text_input("Bob's message:", key="bob_input")
                bob_submitted = st.form_submit_button("Send as Bob")
                
                if bob_submitted and bob_input:
                    with st.spinner("Processing Bob's message..."):
                        session = st.session_state.session_manager.get_session(bob_session_id, "multi_user.db")
                        result = asyncio.run(Runner.run(support_agent, bob_input, session=session))
                        st.write(f"**Support:** {result.final_output}")
            
            if st.button("📋 Bob's History", key="bob_history"):
                items = asyncio.run(st.session_state.session_manager.get_session_items(bob_session_id))
                for item in items:
                    role_emoji = "👨" if item['role'] == 'user' else "🛠️"
                    st.write(f"{role_emoji} **{item['role'].title()}:** {item['content']}")
    
    with tab2:
        st.subheader("Different Contexts, Different Sessions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🛠️ Support Context**")
            support_session_id = "support_context"
            
            with st.form("support_context_form"):
                support_input = st.text_input("Support question:", key="support_context_input")
                support_submitted = st.form_submit_button("Ask Support")
                
                if support_submitted and support_input:
                    with st.spinner("Processing support question..."):
                        session = st.session_state.session_manager.get_session(support_session_id, "contexts.db")
                        result = asyncio.run(Runner.run(support_agent, support_input, session=session))
                        st.write(f"**Support:** {result.final_output}")
        
        with col2:
            st.write("**💰 Sales Context**")
            sales_session_id = "sales_context"
            
            with st.form("sales_context_form"):
                sales_input = st.text_input("Sales inquiry:", key="sales_context_input")
                sales_submitted = st.form_submit_button("Ask Sales")
                
                if sales_submitted and sales_input:
                    with st.spinner("Processing sales inquiry..."):
                        session = st.session_state.session_manager.get_session(sales_session_id, "contexts.db")
                        result = asyncio.run(Runner.run(sales_agent, sales_input, session=session))
                        st.write(f"**Sales:** {result.final_output}")
    
    with tab3:
        st.subheader("Shared Session Across Different Agents")
        st.caption("Customer handoff scenario - same conversation, different agents")
        
        shared_session_id = "customer_handoff"
        
        # Agent selector
        selected_agent = st.radio(
            "Select Agent:",
            ["Sales Agent", "Support Agent"],
            horizontal=True
        )
        
        agent = sales_agent if selected_agent == "Sales Agent" else support_agent
        
        with st.form("handoff_form"):
            handoff_input = st.text_input("Customer message:")
            handoff_submitted = st.form_submit_button(f"Send to {selected_agent}")
            
            if handoff_submitted and handoff_input:
                with st.spinner(f"Processing with {selected_agent}..."):
                    session = st.session_state.session_manager.get_session(shared_session_id, "shared.db")
                    result = asyncio.run(Runner.run(agent, handoff_input, session=session))
                    st.write(f"**{selected_agent}:** {result.final_output}")
        
        # Show shared conversation history
        if st.button("📋 Show Shared Conversation"):
            items = asyncio.run(st.session_state.session_manager.get_session_items(shared_session_id))
            if items:
                st.write("**Shared Conversation History:**")
                for i, item in enumerate(items, 1):
                    if item['role'] == 'user':
                        st.write(f"{i}. 👤 **Customer:** {item['content']}")
                    else:
                        # Try to determine which agent responded based on content
                        agent_emoji = "💰" if "sales" in item['content'].lower() or "price" in item['content'].lower() else "🛠️"
                        st.write(f"{i}. {agent_emoji} **Agent:** {item['content']}")
            else:
                st.info("No conversation history yet.")

# Footer
def render_footer():
    st.divider()
    st.markdown("""
    ### 🎯 Session Capabilities Demonstrated
    
    1. **Basic Sessions**: In-memory vs persistent storage
    2. **Memory Operations**: get_items(), add_items(), pop_item(), clear_session()
    3. **Multi Sessions**: Multiple users, contexts, and agent handoffs
    
    **Key Benefits:**
    - Automatic conversation history management
    - Flexible session organization strategies
    - Memory manipulation for corrections and custom flows
    - Multi-agent conversation support
    """)

if __name__ == "__main__":
    main()
    render_footer()
