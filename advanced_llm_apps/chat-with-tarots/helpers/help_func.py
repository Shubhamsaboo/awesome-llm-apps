import random
from langchain_ollama import ChatOllama


# --- Funzione per generare un'estrazione casuale di carte ---
def genera_estrazione_casuale(numero_carte, nomi_carte_dataset):
    """
    Genera una lista di dizionari rappresentanti un'estrazione casuale di carte.

    Args:
        numero_carte (int): Il numero di carte da includere nell'estrazione (3, 5 o 7).
        nomi_carte_dataset (list): Una lista di stringhe contenenti i nomi delle carte disponibili nel dataset.

    Returns:
        list: Una lista di dizionari, dove ogni dizionario ha la chiave "nome" (il nome della carta estratta)
              e una chiave opzionale "rovesciata" (True se la carta è rovesciata, altrimenti assente).
    """
    if numero_carte not in [3, 5, 7]:
        raise ValueError("Il numero di carte deve essere 3, 5 o 7.")

    estrazione = []
    carte_estratte = random.sample(nomi_carte_dataset, numero_carte)

    for nome_carta in carte_estratte:
        carta = {"nome": nome_carta}
        if random.choice([True, False]):
            carta["rovesciata"] = True
        estrazione.append(carta)

    return estrazione

# --- Funzioni Helper per la catena LangChain ---
def format_card_details_for_prompt(cards_data, card_meanings_dict):
    """Formatta i dettagli delle carte (nome + significato dritto/rovescio) per il prompt."""
    details = []
    for card_info in cards_data:
        card_name = card_info['nome']
        is_reversed = card_info.get('rovesciata', False)
        if card_name in card_meanings_dict:
            meanings = card_meanings_dict[card_name]
            if is_reversed and 'rovescio' in meanings:
                meaning = meanings['rovescio']
                orientation = "(rovesciata)"
            else:
                meaning = meanings['dritto']
                orientation = "(dritta)"
            details.append(f"Carta: {card_name} {orientation} - Significato: {meaning}")
        else:
            details.append(f"Significato di '{card_name}' non trovato nel dataset.")
    return "\n".join(details)

def prepare_prompt_input(input_dict, meanings_dict):
    """Prepara l'input per il prompt recuperando i dettagli delle carte."""
    cards_list = input_dict['carte']
    contesto = input_dict['contesto']
    formatted_details = format_card_details_for_prompt(cards_list, meanings_dict)
    # Estrai e concatena il simbolismo di ogni carta
    simbolismi = []
    for card_info in cards_list:
        card_name = card_info['nome']
        if card_name in meanings_dict:
            simbolismo = meanings_dict[card_name].get('simbolismo', '')
            if simbolismo:
                simbolismi.append(f"{card_name}: {simbolismo}")
    simbolismo_str = "\n".join(simbolismi)
    return {"card_details": formatted_details, "contesto": contesto, "simbolismo": simbolismo_str}

# --- Configura il modello LLM ---
llm = ChatOllama(
    base_url ="http://localhost:11434",
    model = "phi4",
    temperature = 0.8,
)
print(f"\nModello LLM '{llm.model}' configurato.")


print("\nCatena 'analizzatore' definita.")
