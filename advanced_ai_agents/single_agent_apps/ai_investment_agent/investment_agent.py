import streamlit as st
import inspect
from agno.tools.yfinance import YFinanceTools
from agno.agent import Agent
from agno.models.openai import OpenAIChat  # fallback if Gemini isn't available

st.set_page_config(page_title="AI Investment Agent", layout="wide")
st.title("AI Investment Agent 📈🤖")
st.caption("Compare performance of two stocks and generate a detailed investment report.")

# UI: let user choose provider; default to Gemini as you requested
provider = st.selectbox("Model provider", ["Gemini (Google)", "OpenAI"], index=0)

# Single API key input used for whichever provider selected.
# For Gemini you might need a Google API key / service account — show a helpful placeholder.
api_key = st.text_input(
    "Model API key / credentials (for Gemini: Google API key or service account info)",
    type="password",
)

############### Helper: safe YFinance toolkit ###############
def safe_make_yfinance_toolkit(desired):
    try:
        return YFinanceTools(tools=desired)
    except TypeError:
        try:
            return YFinanceTools(desired)
        except TypeError:
            return YFinanceTools()

############### Helper: safe Agent creation ###############
def safe_make_agent(model, tools, description=None, instructions=None, show_tool_calls=False):
    sig = inspect.signature(Agent.__init__)
    accepted = [p for p in sig.parameters.keys() if p != "self"]
    wanted = {
        "model": model,
        "tools": tools,
        "description": description,
        "instructions": instructions,
        "show_tool_calls": show_tool_calls,
    }
    filtered = {k: v for k, v in wanted.items() if k in accepted and v is not None}
    return Agent(**filtered)

############### Helper: try many ways to get a Gemini model ###############
def make_gemini_model(api_key):
    """
    Try multiple common ways to instantiate a Gemini-compatible model wrapper.
    Returns a model instance or raises an informative Exception.
    """
    errors = []

    # 1) Try if agno provides a Gemini model class (common naming guesses)
    possible_imports = [
        ("agno.models.gemini", "GeminiChat"),
        ("agno.models.gemini", "GeminiModel"),
        ("agno.models.google", "Gemini"),
        ("agno.models.google", "GeminiChat"),
    ]
    for mod_name, cls_name in possible_imports:
        try:
            module = __import__(mod_name, fromlist=[cls_name])
            cls = getattr(module, cls_name)
            # many wrappers accept id / api_key / credentials — try common signatures
            try:
                return cls(id="gemini", api_key=api_key)
            except TypeError:
                try:
                    return cls(api_key=api_key)
                except TypeError:
                    try:
                        return cls(credentials=api_key)
                    except TypeError as e:
                        errors.append(f"{mod_name}.{cls_name} exists but couldn't be constructed: {e}")
                        continue
        except Exception as e:
            errors.append(f"import {mod_name}.{cls_name} failed: {e}")

    # 2) Try using google generative ai official client (if installed)
    try:
        import google.generativeai as genai  # type: ignore
        # Example lightweight wrapper object expected by agno: we make a minimal shim.
        class _GenAIWrapper:
            def __init__(self, api_key):
                # set API key for the google generative ai lib
                genai.configure(api_key=api_key)
                self.id = "gemini"
                self._lib = genai

            def generate(self, *args, **kwargs):
                # a very small pass-through example (may need adapting to agno expectations)
                return genai.generate(*args, **kwargs)

        return _GenAIWrapper(api_key)
    except Exception as e:
        errors.append(f"google.generativeai import/usage failed: {e}")

    # 3) If nothing worked, raise an informative error including attempts
    raise RuntimeError(
        "Could not instantiate a Gemini model wrapper from the environment. "
        "Attempts:\n" + "\n".join(errors)
        + (
            "\n\nPossible fixes:\n"
            "- Install an `agno` version that includes a Gemini model wrapper (check package docs).\n"
            "- Install and configure `google-generativeai` and provide appropriate credentials.\n"
            "- If you want to keep using OpenAI, choose the OpenAI provider.\n"
            "If you paste the printed errors here I can adapt the script precisely."
        )
    )

############### Build model & agent when API key is provided ###############
if api_key:
    # Build the YFinance toolkit (compatible across versions)
    try:
        yfinance_toolkit = safe_make_yfinance_toolkit(
            ["stock_price", "analyst_recommendations", "stock_fundamentals"]
        )
    except Exception as e:
        st.error(f"Failed to instantiate YFinanceTools: {e}")
        raise

    # Build the chosen model (Gemini preferred)
    model = None
    model_error = None
    if provider.startswith("Gemini"):
        try:
            model = make_gemini_model(api_key)
            st.success("Gemini model wrapper instantiated.")
        except Exception as e:
            model_error = e
            st.error("Failed to create Gemini model wrapper. Falling back to OpenAI (if available).")
            st.write(e)

    if model is None:
        # Fallback: try OpenAIChat (if user picks OpenAI or Gemini failed)
        try:
            model = OpenAIChat(id="gpt-4o", api_key=api_key)
            st.info("Using OpenAI model as fallback.")
        except Exception as e:
            st.error(f"Failed to instantiate fallback OpenAI model: {e}")
            raise

    # Create agent safely (will ignore unsupported kwargs)
    try:
        assistant = safe_make_agent(
            model=model,
            tools=[yfinance_toolkit],
            description=(
                "You are an investment analyst that researches stock prices, "
                "analyst recommendations, and stock fundamentals."
            ),
            instructions=[
                "Format your response using markdown and use tables to display data where possible."
            ],
            show_tool_calls=True,
        )
    except Exception as e:
        st.error(f"Failed to create Agent: {e}")
        st.write("Agent.__init__ signature:", inspect.signature(Agent.__init__))
        raise

    # UI for stocks
    col1, col2 = st.columns(2)
    with col1:
        stock1 = st.text_input("Enter first stock symbol (e.g. AAPL)").strip().upper()
    with col2:
        stock2 = st.text_input("Enter second stock symbol (e.g. MSFT)").strip().upper()

    if stock1 and stock2:
        with st.spinner(f"Analyzing {stock1} and {stock2}..."):
            query = (
                f"Compare both the stocks - {stock1} and {stock2} and make a detailed "
                "report for an investor trying to compare these stocks."
            )
            try:
                response = assistant.run(query, stream=False)
                if isinstance(response, str):
                    st.markdown(response)
                elif hasattr(response, "content"):
                    st.markdown(response.content)
                elif isinstance(response, dict) and "content" in response:
                    st.markdown(response["content"])
                else:
                    st.markdown(str(response))
            except Exception as e:
                st.error(f"Error running agent: {e}")

else:
    st.info("Enter your model API key / credentials above to start (Gemini selected by default).")
