"""
🎮 AI Negotiation Battle Simulator

A real-time agent vs agent negotiation showdown using Google ADK.

Run with: streamlit run negotiation_app.py
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="🎮 AI Negotiation Battle",
    page_icon="🤝",
    layout="wide"
)

# Custom CSS for the battle arena
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .offer-bubble {
        background: rgba(102, 126, 234, 0.1);
        border-left: 4px solid #667eea;
        padding: 15px;
        border-radius: 0 10px 10px 0;
        margin: 10px 0;
    }
    .counter-bubble {
        background: rgba(220, 53, 69, 0.1);
        border-left: 4px solid #dc3545;
        padding: 15px;
        border-radius: 0 10px 10px 0;
        margin: 10px 0;
    }
    .deal-box {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        color: white;
    }
    .no-deal-box {
        background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# IMPORTS
# ============================================================================

from config.scenarios import SCENARIOS, get_scenario, format_item_description
from config.personalities import (
    BUYER_PERSONALITIES, 
    SELLER_PERSONALITIES, 
    get_personality_prompt
)
from agents import NegotiationOrchestrator


# ============================================================================
# SESSION STATE
# ============================================================================

if "negotiation_started" not in st.session_state:
    st.session_state.negotiation_started = False
if "negotiation_events" not in st.session_state:
    st.session_state.negotiation_events = []


# ============================================================================
# HEADER
# ============================================================================

st.markdown("# 🎮 AI Negotiation Battle Simulator")
st.markdown("*Watch two AI agents duke it out in an epic negotiation showdown!*")
st.divider()


# ============================================================================
# SIDEBAR - CONFIGURATION
# ============================================================================

with st.sidebar:
    st.header("⚙️ Battle Configuration")
    
    # API Key
    api_key = st.text_input(
        "🔑 Google AI API Key",
        type="password",
        value=os.environ.get("GOOGLE_API_KEY", ""),
        help="Get your key from https://aistudio.google.com/"
    )
    
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    
    st.divider()
    
    # Scenario Selection
    st.subheader("📋 Scenario")
    scenario_id = st.selectbox(
        "Choose your battlefield",
        options=list(SCENARIOS.keys()),
        format_func=lambda x: f"{SCENARIOS[x]['emoji']} {SCENARIOS[x]['title']}",
        disabled=st.session_state.negotiation_started
    )
    
    scenario = get_scenario(scenario_id)
    
    with st.expander("📖 Scenario Details"):
        st.markdown(f"**{scenario['description']}**")
        st.markdown(format_item_description(scenario))
        st.markdown(f"**Asking Price:** ${scenario['asking_price']:,}")
        st.markdown(f"**Fair Market Value:** ~${scenario['fair_market_value']:,}")
    
    st.divider()
    
    # Personality Selection
    st.subheader("🎭 Combatants")
    
    buyer_personality = st.selectbox(
        "🎯 Buyer",
        options=list(BUYER_PERSONALITIES.keys()),
        format_func=lambda x: f"{BUYER_PERSONALITIES[x]['emoji']} {BUYER_PERSONALITIES[x]['name']}",
        disabled=st.session_state.negotiation_started
    )
    st.caption(BUYER_PERSONALITIES[buyer_personality]["description"])
    
    seller_personality = st.selectbox(
        "💰 Seller",
        options=list(SELLER_PERSONALITIES.keys()),
        format_func=lambda x: f"{SELLER_PERSONALITIES[x]['emoji']} {SELLER_PERSONALITIES[x]['name']}",
        disabled=st.session_state.negotiation_started
    )
    st.caption(SELLER_PERSONALITIES[seller_personality]["description"])
    
    st.divider()
    
    # Battle Settings
    st.subheader("🎛️ Settings")
    max_rounds = st.slider(
        "Max Rounds", 
        3, 15, 8,
        disabled=st.session_state.negotiation_started
    )


# ============================================================================
# MAIN BATTLE ARENA
# ============================================================================

if not st.session_state.negotiation_started:
    # Pre-battle view
    st.markdown(f"""
    ## {scenario['emoji']} {scenario['title']}
    
    ### The Setup
    
    **Item:** {scenario['item']['name']}  
    **Asking Price:** ${scenario['asking_price']:,}  
    **Fair Market Value:** ~${scenario['fair_market_value']:,}
    
    ---
    
    **🎯 Buyer ({BUYER_PERSONALITIES[buyer_personality]['emoji']} {BUYER_PERSONALITIES[buyer_personality]['name']})**  
    Budget: ${scenario['buyer_budget']:,}  
    *{BUYER_PERSONALITIES[buyer_personality]['description']}*
    
    **💰 Seller ({SELLER_PERSONALITIES[seller_personality]['emoji']} {SELLER_PERSONALITIES[seller_personality]['name']})**  
    Minimum: ${scenario['seller_minimum']:,}  
    *{SELLER_PERSONALITIES[seller_personality]['description']}*
    
    ---
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⚔️ START THE BATTLE!", use_container_width=True, type="primary"):
            if not api_key:
                st.error("⚠️ Please enter your Google AI API key in the sidebar!")
            else:
                st.session_state.negotiation_started = True
                st.session_state.negotiation_events = []
                st.rerun()

else:
    # Battle in progress or complete
    st.markdown(f"## {scenario['emoji']} {scenario['title']}")
    st.markdown(f"**{scenario['item']['name']}** | Asking: **${scenario['asking_price']:,}**")
    st.divider()
    
    # Run negotiation if not already done
    if not st.session_state.negotiation_events:
        
        buyer_prompt = get_personality_prompt("buyer", buyer_personality)
        seller_prompt = get_personality_prompt("seller", seller_personality)
        
        orchestrator = NegotiationOrchestrator(
            scenario=scenario,
            buyer_personality=buyer_prompt,
            seller_personality=seller_prompt,
            max_rounds=max_rounds,
            model="gemini-3-flash-preview"
        )
        
        # Create progress container
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        events = []
        round_count = 0
        
        try:
            for event in orchestrator.run_negotiation_sync():
                events.append(event)
                
                if event["type"] == "buyer_offer":
                    round_count = event["data"]["round"]
                    progress = min(round_count / max_rounds, 0.95)
                    progress_bar.progress(progress)
                    progress_text.markdown(f"🤝 **Round {round_count}** - Agents negotiating...")
                
                elif event["type"] in ["deal", "no_deal", "walk"]:
                    progress_bar.progress(1.0)
                    progress_text.empty()
            
            st.session_state.negotiation_events = events
            
        except Exception as e:
            st.error(f"❌ Error during negotiation: {str(e)}")
            st.session_state.negotiation_events = [{"type": "error", "data": {"error": str(e)}}]
        
        st.rerun()
    
    # Display results
    events = st.session_state.negotiation_events
    
    # Group events by round
    rounds = {}
    outcome = None
    
    for event in events:
        if event["type"] == "buyer_offer":
            round_num = event["data"]["round"]
            rounds[round_num] = {"buyer": event["data"]}
        elif event["type"] == "seller_response":
            round_num = event["data"]["round"]
            if round_num in rounds:
                rounds[round_num]["seller"] = event["data"]
        elif event["type"] in ["deal", "no_deal", "walk"]:
            outcome = event
    
    # Display each round
    for round_num in sorted(rounds.keys()):
        round_data = rounds[round_num]
        
        st.markdown(f"### Round {round_num}")
        
        col1, col2 = st.columns(2)
        
        # Buyer offer
        with col1:
            if "buyer" in round_data:
                buyer = round_data["buyer"]
                st.markdown(f"""
                <div class="offer-bubble">
                <strong>🎯 Buyer Offers: ${buyer['offer']:,}</strong><br>
                <em>"{buyer['message']}"</em><br>
                <small>Confidence: {'🔥' * (buyer['confidence'] // 2)}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Seller response
        with col2:
            if "seller" in round_data:
                seller = round_data["seller"]
                action_text = seller["action"].upper()
                if seller["action"] == "counter" and seller["counter"]:
                    action_text = f"COUNTERS: ${seller['counter']:,}"
                
                st.markdown(f"""
                <div class="counter-bubble">
                <strong>💰 Seller {action_text}</strong><br>
                <em>"{seller['message']}"</em><br>
                <small>Firmness: {'💪' * (seller['firmness'] // 2)}</small>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
    
    # Show outcome
    if outcome:
        if outcome["type"] == "deal":
            data = outcome["data"]
            st.markdown(f"""
            <div class="deal-box">
            <h1>🎉 DEAL CLOSED!</h1>
            <h2>Final Price: ${data['final_price']:,}</h2>
            <p>
            Buyer saved: <strong>${data['savings']:,}</strong> ({data['percent_off']}% off asking)<br>
            Rounds: <strong>{data['rounds']}</strong>
            </p>
            </div>
            """, unsafe_allow_html=True)
        
        elif outcome["type"] == "walk":
            data = outcome["data"]
            st.markdown(f"""
            <div class="no-deal-box">
            <h1>🚪 {data['who'].upper()} WALKED AWAY</h1>
            <h2>No Deal</h2>
            <p>Last offer on the table: ${data['last_offer']:,}</p>
            </div>
            """, unsafe_allow_html=True)
        
        elif outcome["type"] == "no_deal":
            data = outcome["data"]
            st.markdown(f"""
            <div class="no-deal-box">
            <h1>⏰ TIME'S UP</h1>
            <h2>Max Rounds Reached - No Deal</h2>
            <p>Last offer: ${data['last_offer']:,} after {data['rounds']} rounds</p>
            </div>
            """, unsafe_allow_html=True)
    
    # New battle button
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 New Battle", use_container_width=True):
            st.session_state.negotiation_started = False
            st.session_state.negotiation_events = []
            st.rerun()
    
    # Show full log
    with st.expander("📜 Full Negotiation Log (JSON)"):
        for i, event in enumerate(events):
            st.json(event)


# ============================================================================
# FOOTER
# ============================================================================

st.divider()
st.markdown("""
<div style='text-align: center; color: #888;'>
    <p>Built with <strong>Google ADK</strong> + <strong>Streamlit</strong> | 
    <a href='https://github.com/Shubhamsaboo/awesome-llm-apps' target='_blank'>awesome-llm-apps</a></p>
    <p>🎮 May the best negotiator win!</p>
</div>
""", unsafe_allow_html=True)
