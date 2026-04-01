import os
import requests
from dotenv import load_dotenv

load_dotenv()

DOGRAH_API_KEY = os.getenv("DOGRAH_API_KEY")
DOGRAH_AGENT_URL = os.getenv("DOGRAH_AGENT_URL")


def trigger_voice_agent(phone_number: str, initial_context: dict = None):
    """
    Trigger a Dograh voice agent to make an outbound call.

    Args:
        phone_number: The phone number to call in E.164 format (e.g. +14155550100)
        initial_context: Optional dict of context variables accessible in your
                         agent's prompt via {{initial_context.key}} syntax

    Setup:
        1. Sign up at app.dograh.com and get your API key from Settings -> API Keys
        2. Create an agent, add an API Trigger node to your workflow
        3. Copy the endpoint URL from the API Trigger node
        4. Set DOGRAH_API_KEY and DOGRAH_AGENT_URL in your .env file
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": DOGRAH_API_KEY,
    }

    payload = {
        "phone_number": phone_number,
        "initial_context": initial_context or {},
    }

    response = requests.post(DOGRAH_AGENT_URL, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    # Example: trigger a call with dynamic context
    # Context variables are accessible in your agent prompt as:
    # {{initial_context.customer_name}}, {{initial_context.order_id}}, etc.
    result = trigger_voice_agent(
        phone_number="+14155550100",
        initial_context={
            "customer_name": "Jane Smith",
            "order_id": "ORD-001",
            "issue": "delivery delay",
        },
    )

    print("Voice agent triggered successfully!")
    print(f"Response: {result}")