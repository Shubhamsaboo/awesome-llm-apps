"""
AI Negotiation Battle Simulator - Backend Agent

This module creates an ADK agent wrapped with AG-UI middleware for
real-time negotiation between AI buyer and seller agents.
"""

import os
from typing import Optional
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, ToolContext
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint

from config.scenarios import SCENARIOS, get_scenario
from config.personalities import (
    BUYER_PERSONALITIES, 
    SELLER_PERSONALITIES,
    get_personality_prompt
)

# Load environment variables
load_dotenv()


# ============================================================================
# NEGOTIATION STATE (shared between tools)
# ============================================================================

class NegotiationState:
    """Tracks the state of the negotiation."""
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.scenario_id = "craigslist_civic"
        self.buyer_personality = "cool_hand_casey"
        self.seller_personality = "by_the_book_beth"
        self.rounds = []
        self.current_round = 0
        self.status = "setup"  # setup, negotiating, deal, no_deal
        self.final_price = None
        self.buyer_budget = 13000
        self.seller_minimum = 12500
        self.asking_price = 15500

# Global state
negotiation_state = NegotiationState()


# ============================================================================
# NEGOTIATION TOOLS
# ============================================================================

def configure_negotiation(
    scenario_id: str = "craigslist_civic",
    buyer_personality: str = "cool_hand_casey",
    seller_personality: str = "by_the_book_beth",
    tool_context: Optional[ToolContext] = None
) -> dict:
    """
    Configure the negotiation scenario and personalities.
    
    Args:
        scenario_id: The scenario to use (craigslist_civic, vintage_guitar, apartment_sublet)
        buyer_personality: Buyer's personality (desperate_dan, analytical_alex, cool_hand_casey, fair_deal_fran)
        seller_personality: Seller's personality (shark_steve, by_the_book_beth, motivated_mike, drama_queen_diana)
    
    Returns:
        Configuration summary
    """
    scenario = get_scenario(scenario_id)
    
    negotiation_state.reset()
    negotiation_state.scenario_id = scenario_id
    negotiation_state.buyer_personality = buyer_personality
    negotiation_state.seller_personality = seller_personality
    negotiation_state.asking_price = scenario["asking_price"]
    negotiation_state.buyer_budget = scenario["buyer_budget"]
    negotiation_state.seller_minimum = scenario["seller_minimum"]
    negotiation_state.status = "ready"
    
    buyer_p = BUYER_PERSONALITIES[buyer_personality]
    seller_p = SELLER_PERSONALITIES[seller_personality]
    
    return {
        "status": "configured",
        "scenario": {
            "title": scenario["title"],
            "item": scenario["item"]["name"],
            "asking_price": scenario["asking_price"],
            "fair_market_value": scenario["fair_market_value"]
        },
        "buyer": {
            "name": buyer_p["name"],
            "emoji": buyer_p["emoji"],
            "budget": scenario["buyer_budget"]
        },
        "seller": {
            "name": seller_p["name"],
            "emoji": seller_p["emoji"],
            "minimum": scenario["seller_minimum"]
        }
    }


def start_negotiation(tool_context: Optional[ToolContext] = None) -> dict:
    """
    Start the negotiation battle!
    
    Returns:
        Initial negotiation state and instructions
    """
    if negotiation_state.status != "ready":
        return {"error": "Please configure the negotiation first using configure_negotiation"}
    
    scenario = get_scenario(negotiation_state.scenario_id)
    negotiation_state.status = "negotiating"
    negotiation_state.current_round = 1
    
    return {
        "status": "started",
        "round": 1,
        "scenario": scenario["title"],
        "item": scenario["item"]["name"],
        "asking_price": scenario["asking_price"],
        "message": f"🔔 NEGOTIATION BEGINS! The battle for the {scenario['item']['name']} is ON!"
    }


def buyer_make_offer(
    offer_amount: int,
    message: str,
    reasoning: str = "",
    tool_context: Optional[ToolContext] = None
) -> dict:
    """
    Buyer makes an offer to the seller.
    
    Args:
        offer_amount: The dollar amount being offered
        message: What the buyer says to the seller
        reasoning: Internal reasoning for this offer
    
    Returns:
        Offer details and status
    """
    if negotiation_state.status != "negotiating":
        return {"error": "Negotiation not in progress"}
    
    scenario = get_scenario(negotiation_state.scenario_id)
    buyer_p = BUYER_PERSONALITIES[negotiation_state.buyer_personality]
    
    round_data = {
        "round": negotiation_state.current_round,
        "type": "buyer_offer",
        "offer_amount": offer_amount,
        "message": message,
        "reasoning": reasoning,
        "buyer_name": buyer_p["name"],
        "buyer_emoji": buyer_p["emoji"]
    }
    
    negotiation_state.rounds.append(round_data)
    
    return {
        "status": "offer_made",
        "round": negotiation_state.current_round,
        "offer": offer_amount,
        "message": message,
        "buyer": f"{buyer_p['emoji']} {buyer_p['name']}",
        "percent_of_asking": round(offer_amount / scenario["asking_price"] * 100, 1)
    }


def seller_respond(
    action: str,
    counter_amount: Optional[int] = None,
    message: str = "",
    reasoning: str = "",
    tool_context: Optional[ToolContext] = None
) -> dict:
    """
    Seller responds to the buyer's offer.
    
    Args:
        action: One of 'accept', 'counter', 'reject', 'walk'
        counter_amount: If countering, the counter offer amount
        message: What the seller says to the buyer
        reasoning: Internal reasoning for this decision
    
    Returns:
        Response details and updated negotiation status
    """
    if negotiation_state.status != "negotiating":
        return {"error": "Negotiation not in progress"}
    
    scenario = get_scenario(negotiation_state.scenario_id)
    seller_p = SELLER_PERSONALITIES[negotiation_state.seller_personality]
    
    round_data = {
        "round": negotiation_state.current_round,
        "type": "seller_response",
        "action": action,
        "counter_amount": counter_amount,
        "message": message,
        "reasoning": reasoning,
        "seller_name": seller_p["name"],
        "seller_emoji": seller_p["emoji"]
    }
    
    negotiation_state.rounds.append(round_data)
    
    result = {
        "status": "response_given",
        "round": negotiation_state.current_round,
        "action": action,
        "message": message,
        "seller": f"{seller_p['emoji']} {seller_p['name']}"
    }
    
    if action == "accept":
        # Get the last buyer offer
        last_offer = None
        for r in reversed(negotiation_state.rounds):
            if r["type"] == "buyer_offer":
                last_offer = r["offer_amount"]
                break
        
        negotiation_state.status = "deal"
        negotiation_state.final_price = last_offer
        
        result["outcome"] = "DEAL"
        result["final_price"] = last_offer
        result["savings"] = scenario["asking_price"] - last_offer
        result["percent_off"] = round((scenario["asking_price"] - last_offer) / scenario["asking_price"] * 100, 1)
    
    elif action == "walk":
        negotiation_state.status = "no_deal"
        result["outcome"] = "SELLER_WALKED"
    
    elif action == "counter":
        result["counter_amount"] = counter_amount
        negotiation_state.current_round += 1
    
    else:  # reject
        negotiation_state.current_round += 1
    
    return result


def get_negotiation_state(tool_context: Optional[ToolContext] = None) -> dict:
    """
    Get the current state of the negotiation.
    
    Returns:
        Full negotiation state including history
    """
    scenario = get_scenario(negotiation_state.scenario_id)
    buyer_p = BUYER_PERSONALITIES[negotiation_state.buyer_personality]
    seller_p = SELLER_PERSONALITIES[negotiation_state.seller_personality]
    
    return {
        "status": negotiation_state.status,
        "scenario": scenario["title"],
        "item": scenario["item"]["name"],
        "asking_price": scenario["asking_price"],
        "current_round": negotiation_state.current_round,
        "buyer": {
            "name": buyer_p["name"],
            "emoji": buyer_p["emoji"],
            "budget": negotiation_state.buyer_budget
        },
        "seller": {
            "name": seller_p["name"],
            "emoji": seller_p["emoji"],
            "minimum": negotiation_state.seller_minimum
        },
        "rounds": negotiation_state.rounds,
        "final_price": negotiation_state.final_price
    }


def get_available_scenarios(tool_context: Optional[ToolContext] = None) -> dict:
    """
    Get all available negotiation scenarios.
    
    Returns:
        List of available scenarios with details
    """
    scenarios = []
    for key, s in SCENARIOS.items():
        scenarios.append({
            "id": key,
            "title": s["title"],
            "emoji": s["emoji"],
            "description": s["description"],
            "item": s["item"]["name"],
            "asking_price": s["asking_price"]
        })
    return {"scenarios": scenarios}


def get_available_personalities(tool_context: Optional[ToolContext] = None) -> dict:
    """
    Get all available buyer and seller personalities.
    
    Returns:
        Available personalities for both buyer and seller
    """
    buyers = []
    for key, p in BUYER_PERSONALITIES.items():
        buyers.append({
            "id": key,
            "name": p["name"],
            "emoji": p["emoji"],
            "description": p["description"]
        })
    
    sellers = []
    for key, p in SELLER_PERSONALITIES.items():
        sellers.append({
            "id": key,
            "name": p["name"],
            "emoji": p["emoji"],
            "description": p["description"]
        })
    
    return {"buyers": buyers, "sellers": sellers}


# ============================================================================
# ADK AGENT DEFINITION
# ============================================================================

negotiation_agent = LlmAgent(
    name="NegotiationBattleAgent",
    model="gemini-3-flash-preview",
    description="AI Negotiation Battle Simulator - orchestrates dramatic negotiations between buyer and seller agents",
    instruction="""
You are the NEGOTIATION BATTLE MASTER! 🎮 You orchestrate epic negotiations between AI buyer and seller agents.

YOUR ROLE:
You manage a negotiation battle where a Buyer agent and a Seller agent negotiate over an item.
You play BOTH roles, switching between them to create a dramatic back-and-forth negotiation.

AVAILABLE TOOLS:
- get_available_scenarios: See what scenarios are available
- get_available_personalities: See buyer/seller personality options  
- configure_negotiation: Set up the scenario and personalities
- start_negotiation: Begin the battle!
- buyer_make_offer: Make an offer as the buyer
- seller_respond: Respond as the seller (accept/counter/reject/walk)
- get_negotiation_state: Check current negotiation status

HOW TO RUN A NEGOTIATION:
1. First, use configure_negotiation to set up the scenario and personalities
2. Use start_negotiation to begin
3. Alternate between buyer_make_offer and seller_respond
4. Play each role authentically based on their personality!
5. Continue until a deal is reached or someone walks away

PERSONALITY GUIDELINES:
- Each personality has distinct traits - embody them fully!
- Buyers have budgets they shouldn't exceed
- Sellers have minimums they won't go below
- Create DRAMA and tension in the negotiation
- Make the dialogue feel real and entertaining

IMPORTANT:
- When the user asks to start a negotiation, first show them the options
- Let them pick scenario and personalities, or use defaults
- Once configured, run the full negotiation automatically
- Provide colorful commentary between rounds
- Celebrate deals and mourn walkways dramatically!

Be entertaining, dramatic, and make this feel like a real negotiation showdown! 🎭
""",
    tools=[
        FunctionTool(get_available_scenarios),
        FunctionTool(get_available_personalities),
        FunctionTool(configure_negotiation),
        FunctionTool(start_negotiation),
        FunctionTool(buyer_make_offer),
        FunctionTool(seller_respond),
        FunctionTool(get_negotiation_state),
    ]
)


# ============================================================================
# AG-UI + FASTAPI SETUP
# ============================================================================

# Create ADK middleware agent
adk_negotiation_agent = ADKAgent(
    adk_agent=negotiation_agent,
    app_name="negotiation_battle",
    user_id="battle_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True
)

# Create FastAPI app
app = FastAPI(
    title="AI Negotiation Battle Simulator",
    description="Watch AI agents battle it out in epic negotiations!",
    version="1.0.0"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add AG-UI endpoint
add_adk_fastapi_endpoint(app, adk_negotiation_agent, path="/")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY not set!")
        print("   Get your key from: https://aistudio.google.com/")
        print()
    
    port = int(os.getenv("PORT", 8000))
    print(f"🎮 AI Negotiation Battle Simulator starting on port {port}")
    print(f"   AG-UI endpoint: http://localhost:{port}/")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
