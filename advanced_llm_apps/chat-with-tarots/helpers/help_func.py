import random
from langchain_ollama import ChatOllama


# --- Function to generate a random draw of cards ---
def generate_random_draw(num_cards, card_names_dataset):
    """
    Generates a list of dictionaries representing a random draw of cards.

    Args:
        num_cards (int): The number of cards to include in the draw (3, 5, or 7).
        card_names_dataset (list): A list of strings containing the names of the available cards in the dataset.

    Returns:
        list: A list of dictionaries, where each dictionary has the key "name" (the name of the drawn card)
              and an optional "is_reversed" key (True if the card is reversed, otherwise absent).
    """
    if num_cards not in [3, 5, 7]:
        raise ValueError("The number of cards must be 3, 5, or 7.")

    drawn_cards = []
    drawn_cards_sample = random.sample(card_names_dataset, num_cards)

    for card_name in drawn_cards_sample:
        card = {"name": card_name}
        if random.choice([True, False]):
            card["is_reversed"] = True
        drawn_cards.append(card)

    return drawn_cards

# --- Helper Functions for LangChain Chain ---
def format_card_details_for_prompt(card_data, card_meanings):
    """Formats card details (name + upright/reversed meaning) for the prompt."""
    details = []
    for card_info in card_data:
        card_name = card_info['name']
        is_reversed = card_info.get('is_reversed', False)
        if card_name in card_meanings:
            meanings = card_meanings[card_name]
            if is_reversed and 'reversed' in meanings:
                meaning = meanings['reversed']
                orientation = "(reversed)"
            else:
                meaning = meanings['upright']
                orientation = "(upright)"
            details.append(f"Card: {card_name} {orientation} - Meaning: {meaning}")
        else:
            details.append(f"Meaning of '{card_name}' not found in the dataset.")
    return "\n".join(details)

def prepare_prompt_input(input_dict, meanings_dict):
    """Prepares the input for the prompt by retrieving card details."""
    card_list = input_dict['cards']
    context = input_dict['context']
    formatted_details = format_card_details_for_prompt(card_list, meanings_dict)
    # Extract and concatenate the symbolism of each card
    symbolisms = []
    for card_info in card_list:
        card_name = card_info['name']
        if card_name in meanings_dict:
            symbolism = meanings_dict[card_name].get('symbolism', '')
            if symbolism:
                symbolisms.append(f"{card_name}: {symbolism}")
    symbolism_str = "\n".join(symbolisms)
    return {"card_details": formatted_details, "context": context, "symbolism": symbolism_str}

# --- Configure the LLM model ---
llm = ChatOllama(
    base_url ="http://localhost:11434",
    model = "phi4",
    temperature = 0.8,
)
print(f"\nLLM model '{llm.model}' configured.")


print("\nChain 'analyzer' defined.")
