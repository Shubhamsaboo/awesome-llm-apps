"""Seller agent for the negotiation battle simulator."""

from google.adk.agents import LlmAgent


def create_seller_agent(
    scenario: dict,
    personality_prompt: str = "",
    model: str = "gemini-3-flash-preview"
) -> LlmAgent:
    """Create a seller agent configured for a specific negotiation scenario.
    
    Args:
        scenario: The negotiation scenario configuration
        personality_prompt: Optional personality traits to inject
        model: The LLM model to use
        
    Returns:
        Configured LlmAgent for the seller role
    """
    
    item = scenario["item"]
    
    base_instruction = f"""You are a SELLER in a negotiation for your {item['name']}.

=== THE SITUATION ===
{scenario['seller_context']}

=== WHAT YOU'RE SELLING ===
Item: {item['name']}
Your Asking Price: ${scenario['asking_price']:,}
Your Minimum (walk away below this): ${scenario['seller_minimum']:,}
Fair Market Value: ~${scenario['fair_market_value']:,}

Why it's worth the price:
{chr(10).join(f'  + {p}' for p in item.get('positives', []))}

Issues you may need to address:
{chr(10).join(f'  - {i}' for i in item.get('issues', []))}

=== YOUR STAKES ===
{scenario['seller_stakes']}

=== YOUR SECRET (influences your behavior, but never state directly) ===
{scenario['seller_secret']}

=== NEGOTIATION RULES ===
1. NEVER go below your minimum of ${scenario['seller_minimum']:,}
2. Start firm - you've priced it fairly
3. Counter lowball offers with smaller concessions
4. Highlight the positives to justify your price
5. Stay in character throughout
6. Create urgency when appropriate ("I have other interested buyers")
7. Know when to stand firm vs. when to close the deal

=== YOUR GOAL ===
Sell the {item['name']} for the best possible price, ideally at or above ${scenario['fair_market_value']:,}.
But you do need to sell, so find the balance between maximizing value and closing the deal.

{personality_prompt}

=== RESPONSE FORMAT ===
When responding to an offer, respond with a JSON object like this:
{{
    "action": "counter",
    "counter_amount": 14500,
    "message": "What you say to the buyer - be in character, conversational!",
    "reasoning": "Brief internal reasoning for this decision",
    "firmness": 7
}}

For "action", use one of:
- "accept" - You accept the offer (no counter_amount needed)
- "counter" - You make a counteroffer (include counter_amount)
- "reject" - You reject outright but don't walk away
- "walk" - You're done negotiating

Always respond with valid JSON. Make your message sound natural and in-character!
"""

    return LlmAgent(
        name="seller_agent",
        model=model,
        description=f"Seller of {item['name']}",
        instruction=base_instruction,
    )
