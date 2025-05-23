from langchain.prompts import PromptTemplate
import pandas as pd
from langchain_core.runnables import RunnableParallel, RunnableLambda # Import necessario per LCEL
import random
import streamlit as st
import helpers.help_func as hf



# --- Carica il dataset ---
csv_file_path = 'data/tarocchi.csv'
try:
    # Read CSV file
    df = pd.read_csv(csv_file_path, sep=';', encoding='latin1')
    print(f"CSV dataset loaded successfully: {csv_file_path}. Row numbers: {len(df)}")
    
    # Clean and normalize column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Debug: Show column details
    print("\nDetails after cleanup:")
    for col in df.columns:
        print(f"Colonna: '{col}' (lunghezza: {len(col)})")
    
    # Define required columns (in lowercase)
    required_columns = ['carte', 'dritto', 'rovescio', 'simbolismo']
    
    # Verify all required columns are present
    available_columns = set(df.columns)
    missing_columns = [col for col in required_columns if col not in available_columns]
    
    if missing_columns:
        raise ValueError(
            f"Missing columns in CSV file: {', '.join(missing_columns)}\n"
            f"Available columns: {', '.join(available_columns)}"
        )
    
    # Create card meanings dictionary with cleaned data
    card_meanings = {}
    for _, row in df.iterrows():
        card_name = row['carte'].strip()
        card_meanings[card_name] = {
            'dritto': str(row['dritto']).strip() if pd.notna(row['dritto']) else '',
            'rovescio': str(row['rovescio']).strip() if pd.notna(row['rovescio']) else '',
            'simbolismo': str(row['simbolismo']).strip() if pd.notna(row['simbolismo']) else ''
        }
    
    print(f"\nKnowledge base created with {len(card_meanings)} cards, meaning and symbolisms.")
    
except FileNotFoundError:
    print(f"Error: CSV File not found: {csv_file_path}")
    raise
except ValueError as e:
    print(f"Validation Error: {str(e)}")
    raise
except Exception as e:
    print(f"Unexpected error: {str(e)}")
    raise



# --- Definisci il Prompt Template ---
prompt_analisi = PromptTemplate.from_template("""
Analyze the following tarot cards, based on the meanings provided (also considering if they are reversed):
{card_details}
Pay attenrtion to these  aspects:
- Provide a detailed analysis of the meaning of each card (upright or reversed).
- Then offer a general interpretation of the answer based on the cards, linking it to the context: {contesto}.
- Be mystical and provide information on the interpretation related to the symbolism of the cards, based on the specific column: {simbolismo}.
- At the end of the reading, always offer advice to improve or address the situation. Also, base it on your knowledge of psychology.
IMPORTANT:  if someone is writing in Italian, translate the final output into Italian language.
""")
print("\nPrompt Template 'prompt_analisi' definito.")

# --- Crea la Catena LangChain ---
analizzatore = (
    RunnableParallel(
        carte=lambda x: x['carte'],
        contesto=lambda x: x['contesto']
    )
    | (lambda x: hf.prepare_prompt_input(x, card_meanings))
    | prompt_analisi
    | hf.llm
)


# --- Frontend Streamlit ---
st.set_page_config(
    page_title="🔮 Interactive Tarot Reading",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("🔮 Interactive Tarot Reading")
st.markdown("Welcome to your personalized tarot consultation!")
st.markdown("---")

numero_carte = st.selectbox("🃏 Select the number of cards for your spread (3 for a more focused answer, 7 for a more general overview).)", [3, 5, 7])
contesto_domanda = st.text_area("✍️ Please enter your context or your question here. You can speak in natural language.", height=100)

if st.button("✨ Light your path: Draw and Analyze the Cards."):
    if not contesto_domanda:
        st.warning("For a more precise reading, please enter your context or question.")
    else:
        try:
            nomi_carte_nel_dataset = df['carte'].unique().tolist()
            lista_di_carte_estratte = hf.genera_estrazione_casuale(numero_carte, nomi_carte_nel_dataset)
            st.subheader("✨ Your Cards Revealed:")
            st.markdown("---")

            cols = st.columns(len(lista_di_carte_estratte))
            for i, carta_info in enumerate(lista_di_carte_estratte):
                with cols[i]:
                    nome_carta = carta_info['nome'].replace(" ", "_")
                    immagine_path = f"images/{nome_carta}.jpg"
                    rovesciata_label = "(R)" if 'rovesciata' in carta_info else ""
                    caption = f"{carta_info['nome']} {rovesciata_label}"

                    try:
                        st.image(immagine_path, caption=caption, width=150)
                    except FileNotFoundError:
                        st.info(f"Simbolo: {carta_info['nome']} {rovesciata_label}")

            st.markdown("---")
            with st.spinner("🔮 Unveiling the meanings..."):
                risultato_analisi = analizzatore.invoke({"carte": lista_di_carte_estratte, "contesto": contesto_domanda})
                st.subheader("📜 The Interpretation:")
                st.write(risultato_analisi.content)

        except Exception as e:
            st.error(f"An error has occurred: {e}")
            st.error(f"Error details: {e}")

st.markdown("---")
st.info("Remember, the cards offer insights and reflections; your future is in your hands.")