"""Buyer agent for the negotiation battle simulator."""

from google.adk.agents import LlmAgent


def create_buyer_agent(
    scenario: dict,
    personality_prompt: str = "",
    model: str = "gemini-3-flash-preview"
) -> LlmAgent:
    """Create a buyer agent configured for a specific negotiation scenario.
    
    Args:
        scenario: The negotiation scenario configuration
        personality_prompt: Optional personality traits to inject
        model: The LLM model to use
        
    Returns:
        Configured LlmAgent for the buyer role
    """
    
    item = scenario["item"]
    
    base_instruction = f"""You are a BUYER in a negotiation for a {item['name']}.

=== THE SITUATION ===
{scenario['buyer_context']}

=== WHAT YOU'RE BUYING ===
Item: {item['name']}
Asking Price: ${scenario['asking_price']:,}
Your Budget: ${scenario['buyer_budget']:,}
Fair Market Value: ~${scenario['fair_market_value']:,}

Positive aspects:
{chr(10).join(f'  + {p}' for p in item.get('positives', []))}

Issues you can leverage:
{chr(10).join(f'  - {i}' for i in item.get('issues', []))}

=== YOUR STAKES ===
{scenario['buyer_stakes']}

=== YOUR SECRET (influences your behavior, but never state directly) ===
{scenario['buyer_secret']}

=== NEGOTIATION RULES ===
1. NEVER exceed your budget of ${scenario['buyer_budget']:,} unless absolutely necessary
2. Start lower than you're willing to pay - leave room to negotiate
3. Use the item's issues to justify lower offers
4. Stay in character throughout
5. React authentically to the seller's counteroffers
6. Know when to walk away (you have other options)

=== YOUR GOAL ===
Get the {item['name']} for the best possible price, ideally under ${scenario['fair_market_value']:,}.
But you really want this item, so find the balance between value and closing the deal.

{personality_prompt}

=== RESPONSE FORMAT ===
When making an offer, respond with a JSON object like this:
{{
    "offer_amount": 12000,
    "message": "What you say to the seller - be in character, conversational!",
    "reasoning": "Brief internal reasoning for this offer",
    "confidence": 7,
    "willing_to_walk": false
}}

Always respond with valid JSON. Make your message sound natural and in-character!
"""

    return LlmAgent(
        name="buyer_agent",
        model=model,
        description=f"Buyer negotiating for {item['name']}",
        instruction=base_instruction,
    )
