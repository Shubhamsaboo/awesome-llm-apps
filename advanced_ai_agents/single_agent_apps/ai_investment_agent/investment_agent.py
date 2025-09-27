import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.yfinance import YFinanceTools

st.title("AI Investment Agent 📈🤖")
st.caption("This app allows you to compare the performance of two stocks and generate detailed reports.")

openai_api_key = st.text_input("OpenAI API Key", type="password")

if openai_api_key:
    assistant = Agent(
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        tools=[
            YFinanceTools(stock_price=True, analyst_recommendations=True, stock_fundamentals=True)
        ],
        show_tool_calls=True,
        description="You are an investment analyst that researches stock prices, analyst recommendations, and stock fundamentals.",
        instructions=[
            "Format your response using markdown and use tables to display data where possible."
        ],
    )

    col1, col2 = st.columns(2)
    with col1:
        stock1 = st.text_input("Enter first stock symbol (e.g. AAPL)")
    with col2:
        stock2 = st.text_input("Enter second stock symbol (e.g. MSFT)")

    if stock1 and stock2:
        with st.spinner(f"Analyzing {stock1} and {stock2}..."):
            query = f"Compare both the stocks - {stock1} and {stock2} and make a detailed report for an investment trying to invest and compare these stocks"
            response = assistant.run(query, stream=False)
            st.markdown(response.content)
import inspect

# Defer importing heavy or third-party libraries that may not be installed in
# all environments until runtime to reduce static linter warnings in IDEs.
try:
    from agno.tools.yfinance import YFinanceTools
except Exception:  # pragma: no cover - optional runtime import
    YFinanceTools = None

try:
    from agno.agent import Agent
except Exception:  # pragma: no cover - optional runtime import
    Agent = None

try:
    from agno.models.openai import OpenAIChat  # fallback if Gemini isn't available
except Exception:  # pragma: no cover - optional runtime import
    OpenAIChat = None

# Runtime dependency checks: show actionable Streamlit errors and stop execution
# early if essential components are missing. This helps users install required
# packages when running the app locally.
missing_deps = []
if YFinanceTools is None:
    missing_deps.append("agno")
if Agent is None:
    if "agno" not in missing_deps:
        missing_deps.append("agno")
if OpenAIChat is None:
    # OpenAIChat is optional (fallback), but warn the user if it's needed later
    missing_deps.append("agno (openai model wrapper)")

if missing_deps:
    deps_list = ", ".join(sorted(set(missing_deps)))
    st.error(
        "Missing required dependencies: "
        + deps_list
        + ".\n\nInstall with: `pip install agno google-generativeai streamlit`\n"
        "If you already installed them, make sure you're running the app in the same virtual environment."
    )
    st.stop()

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
            # many wrappers accept api_key, credentials, or id — try common signatures
            try:
                return cls(api_key=api_key)
            except TypeError:
                try:
                    return cls(credentials=api_key)
                except TypeError:
                    try:
                        # last resort: try passing just an id (some wrappers accept this)
                        return cls(id="gemini")
                    except TypeError as e:
                        errors.append(f"{mod_name}.{cls_name} exists but couldn't be constructed: {e}")
                        continue
        except Exception as e:
            errors.append(f"import {mod_name}.{cls_name} failed: {e}")

    # 2) Try using google generative ai official client (if installed)
    try:
        import google.generativeai as genai  # type: ignore

        # Lightweight wrapper expected by the rest of the code. This wrapper will:
        # - configure the library with the provided key
        # - attempt to discover a usable model id via list_models (if available)
        # - ensure a `model` kwarg is present on generate() calls to avoid 404s
        class _GenAIWrapper:
            def __init__(self, api_key):
                # set API key for the google generative ai lib
                genai.configure(api_key=api_key)
                self._lib = genai
                self.id = None

                # Try to discover available models and pick a reasonable default.
                # list_models may return different shapes depending on client version,
                # so guard carefully.
                discovered = None
                try:
                    if hasattr(genai, "list_models"):
                        models_resp = genai.list_models()
                        # models_resp may be a dict with 'models' or a list
                        candidates = []
                        if isinstance(models_resp, dict):
                            candidates = models_resp.get("models") or []
                        elif isinstance(models_resp, (list, tuple)):
                            candidates = models_resp

                        for m in candidates:
                            # m might be a dict or an object; try several ways to read its name
                            name = None
                            if isinstance(m, dict):
                                name = m.get("name") or m.get("id")
                            else:
                                name = getattr(m, "name", None) or getattr(m, "id", None)

                            if not name:
                                continue
                            low = name.lower()
                            # prefer chat/text/gemini/bison style models
                            if any(k in low for k in ("chat", "gemini", "bison", "text")):
                                discovered = name
                                break
                except Exception:
                    # ignore discovery failures; we'll fall back to sensible defaults
                    discovered = None

                # sensible fallbacks if discovery didn't work
                for candidate in (
                    "models/chat-bison-001",
                    "models/text-bison-001",
                    "models/gemini-1.0",
                    "gemini",
                ):
                    if discovered:
                        break
                    # assign candidate as default; we don't validate by calling network here
                    discovered = candidate

                self.id = discovered

            def generate(self, *args, **kwargs):
                """
                Ensure a `model` kwarg is present (from discovered default) before
                delegating to the underlying library to avoid the 404 "models/... not found" error.
                """
                if "model" not in kwargs or not kwargs.get("model"):
                    if self.id:
                        kwargs["model"] = self.id
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
            # If the wrapper exposes an `id` attribute, show it so users know
            # which model identifier will be used (helps debug 404 model not found).
            model_id = getattr(model, "id", None)
            if model_id:
                st.success(f"Gemini model wrapper instantiated (using model: {model_id}).")
            else:
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
