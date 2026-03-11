"""Negotiation scenario configurations."""

from typing import TypedDict


class ScenarioConfig(TypedDict):
    """Configuration for a negotiation scenario."""
    id: str
    title: str
    emoji: str
    description: str
    
    # The item being negotiated
    item: dict  # name, details, condition, etc.
    
    # Pricing
    asking_price: int
    fair_market_value: int
    buyer_budget: int
    seller_minimum: int
    
    # Context
    buyer_context: str
    seller_context: str
    
    # Stakes
    buyer_stakes: str
    seller_stakes: str
    
    # Drama elements
    buyer_secret: str
    seller_secret: str
    twist: str  # Something that could be revealed mid-negotiation


# ============================================================================
# SCENARIOS
# ============================================================================

SCENARIOS: dict[str, ScenarioConfig] = {
    "craigslist_civic": {
        "id": "craigslist_civic",
        "title": "The Craigslist Showdown",
        "emoji": "🚗",
        "description": "A classic used car negotiation with secrets on both sides.",
        
        "item": {
            "name": "2019 Honda Civic EX",
            "year": 2019,
            "make": "Honda",
            "model": "Civic EX",
            "mileage": 45000,
            "color": "Lunar Silver Metallic",
            "condition": "Excellent",
            "issues": ["Minor scratch on rear bumper", "Small chip in windshield"],
            "positives": [
                "Single owner",
                "Full service records",
                "New tires (6 months ago)",
                "No accidents",
                "Garage kept"
            ]
        },
        
        "asking_price": 15500,
        "fair_market_value": 14000,
        "buyer_budget": 13000,
        "seller_minimum": 12500,
        
        "buyer_context": """
You're a recent college graduate who just landed your first real job. 
The commute is 25 miles each way, and public transit would take 2 hours.
You've saved up $13,000 over the past year, with a secret $500 emergency buffer.
You've been looking for 3 weeks and this is the best car you've seen.
""",
        
        "seller_context": """
You bought this Civic new for $24,000 and it's been your daily driver.
You're upgrading to an SUV because your family is growing.
KBB says private party value is $14,000-$15,000 for excellent condition.
You've already put a deposit on the new car and want to close this sale.
""",
        
        "buyer_stakes": "Job starts Monday. No car means either decline the job or brutal commute.",
        "seller_stakes": "New SUV deposit is non-refundable. Need this money for the down payment.",
        
        "buyer_secret": "You could technically go up to $13,500 using your emergency fund, but you really don't want to.",
        "seller_secret": "The 'other interested buyer' you might mention? They're very flaky and probably won't show.",
        
        "twist": "The seller's spouse mentioned at the test drive that they 'need this gone before the baby comes in 2 weeks.'"
    },
    
    "vintage_guitar": {
        "id": "vintage_guitar",
        "title": "The Vintage Axe",
        "emoji": "🎸",
        "description": "A musician hunts for their dream guitar at a local shop.",
        
        "item": {
            "name": "1978 Fender Stratocaster",
            "year": 1978,
            "make": "Fender",
            "model": "Stratocaster",
            "condition": "Very Good",
            "issues": ["Some fret wear", "Non-original tuning pegs", "Case shows age"],
            "positives": [
                "All original electronics",
                "Original pickups (legendary CBS-era)",
                "Great neck feel",
                "Authentic relic'd finish",
                "Plays beautifully"
            ]
        },
        
        "asking_price": 8500,
        "fair_market_value": 7500,
        "buyer_budget": 7000,
        "seller_minimum": 6500,
        
        "buyer_context": """
You're a professional session musician who's been searching for a late-70s Strat
with the right feel. You've played through dozens and this one just speaks to you.
Your budget is $7,000 but this is The One.
""",
        
        "seller_context": """
You run a vintage guitar shop. This Strat came from an estate sale where you
paid $4,500. It's been in the shop for 3 months and floor space is money.
You need at least $6,500 to keep margins healthy.
""",
        
        "buyer_stakes": "You have a big studio session next week. The right guitar could define your sound.",
        "seller_stakes": "Rent is due and you've got two more estate buys coming in that need funding.",
        
        "buyer_secret": "You could stretch to $7,500 by selling your backup amp, but you'd really rather not.",
        "seller_secret": "You've had this for 90 days and need to move inventory. Might take $6,200.",
        
        "twist": "The buyer mentions they're recording with a famous producer who loves vintage gear."
    },
    
    "apartment_sublet": {
        "id": "apartment_sublet",
        "title": "The Sublet Standoff",
        "emoji": "🏠",
        "description": "Negotiating rent for a 3-month summer sublet in a hot market.",
        
        "item": {
            "name": "Studio Apartment Sublet",
            "type": "Studio apartment",
            "location": "Downtown, 5 min walk to transit",
            "duration": "3 months (June-August)",
            "condition": "Recently renovated",
            "issues": ["Street noise", "No dishwasher", "Coin laundry"],
            "positives": [
                "Great location",
                "In-unit washer/dryer",
                "Rooftop access",
                "Utilities included",
                "Furnished"
            ]
        },
        
        "asking_price": 2200,  # per month
        "fair_market_value": 2000,
        "buyer_budget": 1800,
        "seller_minimum": 1700,
        
        "buyer_context": """
You're a summer intern at a tech company. They're paying $5,000/month stipend.
Housing eats into that significantly. You need something walkable to the office.
""",
        
        "seller_context": """
You're leaving for a 3-month work trip and need to cover rent while gone.
Your rent is $1,600/month. You're hoping to make a small profit or at least break even.
""",
        
        "buyer_stakes": "Your internship starts in 2 weeks. You need housing locked down.",
        "seller_stakes": "You leave in 10 days. Empty apartment means paying double rent.",
        
        "buyer_secret": "Company will reimburse up to $2,000/month but you'd love to pocket the difference.",
        "seller_secret": "You've had two other inquiries but they fell through. Getting nervous.",
        
        "twist": "The sublet includes your neighbor's cat-sitting duties (easy, cat is chill)."
    }
}


def get_scenario(scenario_id: str) -> ScenarioConfig:
    """Get a scenario by ID.
    
    Args:
        scenario_id: The scenario identifier
        
    Returns:
        The scenario configuration
        
    Raises:
        KeyError: If scenario not found
    """
    if scenario_id not in SCENARIOS:
        raise KeyError(f"Unknown scenario: {scenario_id}. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario_id]


def format_item_description(scenario: ScenarioConfig) -> str:
    """Format the item being negotiated into a readable description."""
    item = scenario["item"]
    
    lines = [
        f"**{item['name']}**",
        "",
        "Condition: " + item.get("condition", "Good"),
        "",
        "Positives:",
    ]
    
    for positive in item.get("positives", []):
        lines.append(f"  ✓ {positive}")
    
    lines.append("")
    lines.append("Issues to Note:")
    
    for issue in item.get("issues", []):
        lines.append(f"  • {issue}")
    
    return "\n".join(lines)
