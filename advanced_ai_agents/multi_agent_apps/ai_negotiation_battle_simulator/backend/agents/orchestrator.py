"""Orchestrator for managing negotiation flow between buyer and seller agents."""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Optional, Literal, Generator
from datetime import datetime

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from .buyer_agent import create_buyer_agent
from .seller_agent import create_seller_agent


# ============================================================================
# NEGOTIATION STATE
# ============================================================================

@dataclass
class NegotiationRound:
    """A single round of negotiation."""
    round_number: int
    buyer_offer: Optional[int] = None
    buyer_message: str = ""
    buyer_reasoning: str = ""
    seller_action: Optional[str] = None  # "counter", "accept", "reject", "walk"
    seller_counter: Optional[int] = None
    seller_message: str = ""
    seller_reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class NegotiationState:
    """Full state of the negotiation."""
    scenario_id: str
    status: Literal["ongoing", "deal", "buyer_walked", "seller_walked", "no_deal"] = "ongoing"
    asking_price: int = 0
    current_offer: int = 0
    rounds: list[NegotiationRound] = field(default_factory=list)
    final_price: Optional[int] = None
    max_rounds: int = 10
    
    @property
    def round_count(self) -> int:
        return len(self.rounds)
    
    @property
    def is_complete(self) -> bool:
        return self.status != "ongoing"
    
    def get_negotiation_history(self) -> str:
        """Format the negotiation history for agent context."""
        if not self.rounds:
            return "No offers yet. This is the opening round."
        
        lines = []
        for r in self.rounds:
            lines.append(f"Round {r.round_number}:")
            if r.buyer_offer:
                lines.append(f"  Buyer offered: ${r.buyer_offer:,}")
                lines.append(f"  Buyer said: \"{r.buyer_message}\"")
            if r.seller_action:
                if r.seller_action == "accept":
                    lines.append(f"  Seller ACCEPTED!")
                elif r.seller_action == "counter" and r.seller_counter:
                    lines.append(f"  Seller countered: ${r.seller_counter:,}")
                elif r.seller_action == "reject":
                    lines.append(f"  Seller rejected the offer")
                elif r.seller_action == "walk":
                    lines.append(f"  Seller walked away!")
                if r.seller_message:
                    lines.append(f"  Seller said: \"{r.seller_message}\"")
            lines.append("")
        
        return "\n".join(lines)


# ============================================================================
# RESPONSE PARSERS
# ============================================================================

def parse_buyer_response(response_text: str) -> dict:
    """Parse buyer agent response into structured data."""
    # Try to extract JSON from the response
    try:
        # Look for JSON in the response
        if "{" in response_text and "}" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            data = json.loads(json_str)
            return {
                "offer_amount": data.get("offer_amount", 0),
                "message": data.get("message", ""),
                "reasoning": data.get("reasoning", ""),
                "confidence": data.get("confidence", 5),
                "willing_to_walk": data.get("willing_to_walk", False)
            }
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Fallback: extract offer from text
    import re
    amount_match = re.search(r'\$?([\d,]+)', response_text)
    offer = int(amount_match.group(1).replace(",", "")) if amount_match else 0
    
    return {
        "offer_amount": offer,
        "message": response_text[:500],
        "reasoning": "Extracted from response",
        "confidence": 5,
        "willing_to_walk": False
    }


def parse_seller_response(response_text: str) -> dict:
    """Parse seller agent response into structured data."""
    try:
        if "{" in response_text and "}" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            data = json.loads(json_str)
            return {
                "action": data.get("action", "counter").lower(),
                "counter_amount": data.get("counter_amount"),
                "message": data.get("message", ""),
                "reasoning": data.get("reasoning", ""),
                "firmness": data.get("firmness", 5)
            }
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Fallback parsing
    response_lower = response_text.lower()
    action = "counter"
    if "accept" in response_lower or "deal" in response_lower:
        action = "accept"
    elif "walk" in response_lower or "goodbye" in response_lower:
        action = "walk"
    elif "reject" in response_lower:
        action = "reject"
    
    import re
    amount_match = re.search(r'\$?([\d,]+)', response_text)
    counter = int(amount_match.group(1).replace(",", "")) if amount_match else None
    
    return {
        "action": action,
        "counter_amount": counter,
        "message": response_text[:500],
        "reasoning": "Extracted from response",
        "firmness": 5
    }


# ============================================================================
# NEGOTIATION ORCHESTRATOR
# ============================================================================

class NegotiationOrchestrator:
    """Manages the negotiation between buyer and seller agents."""
    
    def __init__(
        self,
        scenario: dict,
        buyer_personality: str = "",
        seller_personality: str = "",
        max_rounds: int = 10,
        model: str = "gemini-3-flash-preview"
    ):
        self.scenario = scenario
        self.model = model
        self.max_rounds = max_rounds
        
        # Create agents
        self.buyer_agent = create_buyer_agent(scenario, buyer_personality, model)
        self.seller_agent = create_seller_agent(scenario, seller_personality, model)
        
        # Create runners
        self.buyer_runner = InMemoryRunner(
            agent=self.buyer_agent,
            app_name="negotiation_buyer"
        )
        self.seller_runner = InMemoryRunner(
            agent=self.seller_agent,
            app_name="negotiation_seller"
        )
        
        # Session IDs
        self.buyer_session_id = "buyer_session"
        self.seller_session_id = "seller_session"
        
        # Initialize state
        self.state = NegotiationState(
            scenario_id=scenario["id"],
            asking_price=scenario["asking_price"],
            max_rounds=max_rounds
        )
    
    async def _run_agent(self, runner: InMemoryRunner, session_id: str, prompt: str) -> str:
        """Run an agent and return its response."""
        user_content = types.Content(
            role='user',
            parts=[types.Part(text=prompt)]
        )
        
        response_text = ""
        async for event in runner.run_async(
            user_id="negotiation",
            session_id=session_id,
            new_message=user_content
        ):
            if event.is_final_response() and event.content:
                response_text = event.content.parts[0].text.strip()
        
        return response_text
    
    async def _get_buyer_offer(self, context: str) -> dict:
        """Get an offer from the buyer agent."""
        prompt = f"""
=== CURRENT NEGOTIATION STATUS ===
Asking Price: ${self.state.asking_price:,}
Rounds so far: {self.state.round_count}
Max rounds before walkaway: {self.max_rounds}

=== HISTORY ===
{self.state.get_negotiation_history()}

=== YOUR TURN ===
{context}

Respond with a JSON object containing:
- "offer_amount": your offer in dollars (integer)
- "message": what you say to the seller (be in character!)
- "reasoning": brief explanation of your strategy
- "confidence": how confident you are 1-10
- "willing_to_walk": true/false if you'd walk away if rejected
"""
        
        response = await self._run_agent(self.buyer_runner, self.buyer_session_id, prompt)
        return parse_buyer_response(response)
    
    async def _get_seller_response(self, offer: int, buyer_message: str) -> dict:
        """Get a response from the seller agent."""
        prompt = f"""
=== CURRENT NEGOTIATION STATUS ===
Your Asking Price: ${self.state.asking_price:,}
Rounds so far: {self.state.round_count}
Max rounds: {self.max_rounds}

=== HISTORY ===
{self.state.get_negotiation_history()}

=== BUYER'S CURRENT OFFER ===
Amount: ${offer:,}
What they said: "{buyer_message}"

=== YOUR TURN ===
Decide how to respond. You can ACCEPT, COUNTER, REJECT, or WALK.

Respond with a JSON object containing:
- "action": one of "accept", "counter", "reject", "walk"
- "counter_amount": if countering, your counter price (integer) 
- "message": what you say to the buyer (be in character!)
- "reasoning": brief explanation of your decision
- "firmness": how firm you are on this position 1-10
"""
        
        response = await self._run_agent(self.seller_runner, self.seller_session_id, prompt)
        return parse_seller_response(response)
    
    def run_negotiation_sync(self) -> Generator[dict, None, None]:
        """Run the full negotiation synchronously, yielding events.
        
        Yields dicts with:
            - type: "start", "buyer_offer", "seller_response", "deal", "no_deal", "walk"
            - data: relevant data for the event
        """
        
        async def _run():
            events = []
            
            events.append({
                "type": "start",
                "data": {
                    "scenario": self.scenario["title"],
                    "item": self.scenario["item"]["name"],
                    "asking_price": self.state.asking_price,
                    "max_rounds": self.max_rounds
                }
            })
            
            # Initial context for buyer
            buyer_context = "Make your opening offer for this item. Start strong but leave room to negotiate."
            
            while not self.state.is_complete and self.state.round_count < self.max_rounds:
                round_num = self.state.round_count + 1
                current_round = NegotiationRound(round_number=round_num)
                
                # Get buyer's offer
                try:
                    buyer_data = await self._get_buyer_offer(buyer_context)
                    current_round.buyer_offer = buyer_data["offer_amount"]
                    current_round.buyer_message = buyer_data["message"]
                    current_round.buyer_reasoning = buyer_data["reasoning"]
                    self.state.current_offer = buyer_data["offer_amount"]
                    
                    events.append({
                        "type": "buyer_offer",
                        "data": {
                            "round": round_num,
                            "offer": buyer_data["offer_amount"],
                            "message": buyer_data["message"],
                            "reasoning": buyer_data["reasoning"],
                            "confidence": buyer_data["confidence"],
                            "willing_to_walk": buyer_data["willing_to_walk"]
                        }
                    })
                    
                except Exception as e:
                    events.append({"type": "error", "data": {"agent": "buyer", "error": str(e)}})
                    break
                
                # Get seller's response
                try:
                    seller_data = await self._get_seller_response(
                        buyer_data["offer_amount"],
                        buyer_data["message"]
                    )
                    
                    current_round.seller_action = seller_data["action"]
                    current_round.seller_message = seller_data["message"]
                    current_round.seller_reasoning = seller_data["reasoning"]
                    if seller_data["counter_amount"]:
                        current_round.seller_counter = seller_data["counter_amount"]
                    
                    events.append({
                        "type": "seller_response",
                        "data": {
                            "round": round_num,
                            "action": seller_data["action"],
                            "counter": seller_data["counter_amount"],
                            "message": seller_data["message"],
                            "reasoning": seller_data["reasoning"],
                            "firmness": seller_data["firmness"]
                        }
                    })
                    
                    # Handle seller's decision
                    if seller_data["action"] == "accept":
                        self.state.status = "deal"
                        self.state.final_price = buyer_data["offer_amount"]
                        self.state.rounds.append(current_round)
                        
                        events.append({
                            "type": "deal",
                            "data": {
                                "final_price": buyer_data["offer_amount"],
                                "rounds": round_num,
                                "savings": self.state.asking_price - buyer_data["offer_amount"],
                                "percent_off": round((self.state.asking_price - buyer_data["offer_amount"]) / self.state.asking_price * 100, 1)
                            }
                        })
                        break
                    
                    elif seller_data["action"] == "walk":
                        self.state.status = "seller_walked"
                        self.state.rounds.append(current_round)
                        
                        events.append({
                            "type": "walk",
                            "data": {
                                "who": "seller",
                                "round": round_num,
                                "last_offer": buyer_data["offer_amount"]
                            }
                        })
                        break
                    
                    elif seller_data["action"] == "reject":
                        buyer_context = f"Your offer of ${buyer_data['offer_amount']:,} was rejected. The seller said: \"{seller_data['message']}\". Make a new offer or walk away."
                    
                    else:  # counter
                        buyer_context = f"The seller countered with ${seller_data['counter_amount']:,}. They said: \"{seller_data['message']}\". Make your next move."
                    
                except Exception as e:
                    events.append({"type": "error", "data": {"agent": "seller", "error": str(e)}})
                    break
                
                self.state.rounds.append(current_round)
            
            # Max rounds reached
            if self.state.status == "ongoing":
                self.state.status = "no_deal"
                events.append({
                    "type": "no_deal",
                    "data": {
                        "reason": "max_rounds",
                        "rounds": self.state.round_count,
                        "last_offer": self.state.current_offer
                    }
                })
            
            return events
        
        # Run the async function and yield events
        events = asyncio.run(_run())
        for event in events:
            yield event
    
    def get_summary(self) -> dict:
        """Get a summary of the negotiation."""
        return {
            "scenario": self.scenario["title"],
            "item": self.scenario["item"]["name"],
            "status": self.state.status,
            "asking_price": self.state.asking_price,
            "final_price": self.state.final_price,
            "rounds": self.state.round_count,
            "savings": (self.state.asking_price - self.state.final_price) if self.state.final_price else None
        }
