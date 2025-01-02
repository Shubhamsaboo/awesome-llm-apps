import os
import random
from autogen import ConversableAgent

# Function to get OpenAI API key from user input
def get_openai_api_key():
    api_key = input("Please enter your OpenAI API key: ").strip()
    if not api_key:
        raise ValueError("API key cannot be empty.")
    return api_key

# Set OpenAI API key as environment variable
OPENAI_API_KEY = get_openai_api_key()

# Initialize deck
suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
deck = [{'rank': rank, 'suit': suit} for suit in suits for rank in ranks]

# Function to deal a card
def deal_card(deck):
    return deck.pop()

# Function to calculate hand value
def calculate_hand_value(hand):
    value = 0
    aces = 0
    for card in hand:
        rank = card['rank']
        if rank in ['J', 'Q', 'K']:
            value += 10
        elif rank == 'A':
            value += 11
            aces += 1
        else:
            value += int(rank)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

# Define the Player AI using AutoGen
player_ai = ConversableAgent(
    "player_ai",
    system_message="""
    You are the Player AI in a game of Blackjack. Your goal is to maximize your winnings by making strategic decisions.
    - You will receive your current hand and the dealer's upcard.
    - Decide whether to 'Hit' or 'Stand'.
    - Respond with only 'H' for Hit or 'S' for Stand.
    """,
    llm_config={"config_list": [{"model": "gpt-4", "temperature": 0.2, "api_key": OPENAI_API_KEY}]},
    human_input_mode="NEVER",
)

# Define the Dealer AI using AutoGen
dealer_ai = ConversableAgent(
    "dealer_ai",
    system_message="""
    You are the Dealer AI in a game of Blackjack. Follow these rules:
    - You will receive your current hand and the player's final hand value.
    - Decide whether to 'Hit' or 'Stand' based on the rules of Blackjack.
    - You must hit until your hand value is at least 17.
    - If your hand value exceeds 21, you bust.
    - Respond with only 'H' for Hit or 'S' for Stand.
    """,
    llm_config={"config_list": [{"model": "gpt-4", "temperature": 0.2, "api_key": OPENAI_API_KEY}]},
    human_input_mode="NEVER",
)

# Define the Judge AI using AutoGen
judge_ai = ConversableAgent(
    "judge_ai",
    system_message="""
    You are the Judge AI in a game of Blackjack. You will be provided with the player's final hand and the dealer's final hand. 
    Your job is to determine the winner based on the rules of Blackjack:

    Rules:
    - The player with the hand value closest to 21 without exceeding it wins.
    - If both players have the same hand value, it's a tie.
    - If both players bust (exceed 21), the dealer wins.

    Respond with:
    - "Player" if the player wins.
    - "Dealer" if the dealer wins.
    - "Tie" if it's a tie.
    """,
    llm_config={"config_list": [{"model": "gpt-4", "temperature": 0.2, "api_key": OPENAI_API_KEY}]},
    human_input_mode="NEVER",
)

# Function to play a game of Blackjack
def play_blackjack(player_ai, dealer_ai, judge_ai, max_rounds=5):
    for round_number in range(1, max_rounds + 1):
        print(f"\n--- Round {round_number} ---")
        random.shuffle(deck)
        player_hand = [deal_card(deck), deal_card(deck)]
        dealer_hand = [deal_card(deck), deal_card(deck)]

        # Player's turn
        while True:
            player_value = calculate_hand_value(player_hand)
            dealer_upcard = dealer_hand[0]
            print(f"Player's Hand: {player_hand} (Value: {player_value})")
            print(f"Dealer's Upcard: {dealer_upcard}")

            # Player AI decides to Hit or Stand
            player_ai_message = f"Your current hand is {player_hand} (Value: {player_value}). Dealer's upcard is {dealer_upcard}. Do you want to Hit or Stand? (H/S)"
            player_decision = player_ai.initiate_chat(
                dealer_ai,
                message=player_ai_message,
                max_turns=1,
            )
            # Extract the Player AI's decision
            if player_decision not in ['H', 'S']:
                # Fallback decision if response is invalid
                player_decision = 'S'

            if player_decision == 'H':  # Hit
                player_hand.append(deal_card(deck))
                print(f"Player draws: {player_hand[-1]}")
                player_value = calculate_hand_value(player_hand)
                if player_value > 21:
                    print(f"Player Busts! Hand: {player_hand} (Value: {player_value})")
                    break
            elif player_decision == 'S':  # Stand
                print(f"Player stands with hand: {player_hand} (Value: {player_value})")
                break

        # Dealer's turn
        dealer_value = calculate_hand_value(dealer_hand)
        print(f"Dealer reveals hidden card: {dealer_hand[1]}")
        print(f"Dealer's Hand: {dealer_hand} (Value: {dealer_value})")
        while True:
            # Dealer AI decides to Hit or Stand
            dealer_ai_message = f"Your current hand is {dealer_hand} (Value: {dealer_value}). The player's final hand value is {player_value}. Do you want to Hit or Stand? (H/S)"
            dealer_decision = dealer_ai.initiate_chat(
                player_ai,  # Communicating with the player AI
                message=dealer_ai_message,
                max_turns=1,
            )
            # Extract the Dealer AI's decision
            if dealer_decision not in ['H', 'S']:
                # Fallback decision if response is invalid
                dealer_decision = 'S'

            if dealer_decision == 'H':
                dealer_hand.append(deal_card(deck))
                dealer_value = calculate_hand_value(dealer_hand)
                print(f"Dealer draws: {dealer_hand[-1]}")
                if dealer_value > 21:
                    print(f"Dealer Busts! Hand: {dealer_hand} (Value: {dealer_value})")
                    break
            elif dealer_decision == 'S':
                print(f"Dealer stands with hand: {dealer_hand} (Value: {dealer_value})")
                break

        # Judge determines the winner
        judge_ai_message = f"Player's final hand: {player_hand} (Value: {player_value}). Dealer's final hand: {dealer_hand} (Value: {dealer_value}). Who wins?"
        winner = judge_ai.generate_reply(messages=[{"content": judge_ai_message, "role": "user"}]) 
        print(f"\n{winner} Wins!")

# Run the game
play_blackjack(player_ai, dealer_ai, judge_ai)