import io
import json
import streamlit as st
from pypdf import PdfReader
from openai import OpenAI

st.set_page_config(
    page_title="AI Layout-Preserving PDF Translator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for A4-like comparison styling
st.markdown("""
<style>
    .report-box {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 24px;
        background-color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        min-height: 480px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Model & API Settings")
    
    api_provider = st.selectbox(
        "API Provider",
        ["OpenAI", "DeepSeek", "OpenRouter / Custom"]
    )
    
    default_base_url = "https://api.openai.com/v1"
    default_model = "gpt-4o-mini"
    
    if api_provider == "DeepSeek":
        default_base_url = "https://api.deepseek.com"
        default_model = "deepseek-chat"
    elif api_provider == "OpenRouter / Custom":
        default_base_url = "https://openrouter.ai/api/v1"
        default_model = "openai/gpt-4o-mini"
        
    api_key = st.text_input("API Key", type="password", help="Enter your LLM provider API key")
    base_url = st.text_input("Base URL", value=default_base_url)
    model_name = st.text_input("Model Name", value=default_model)
    
    st.divider()
    st.header("🌐 Translation Target")
    target_lang = st.selectbox(
        "Target Language",
        ["Simplified Chinese (简体中文)", "English", "Spanish", "Japanese", "German", "French", "Arabic"]
    )
    
    st.divider()
    st.markdown("### 🌟 Powered By")
    st.markdown("Built with [**pdf-translate**](https://github.com/lxsssssss/pdf-translate) — High-fidelity layout-preserving document translation agent skill.")

# Main Page Header
st.title("📄 AI Layout-Preserving PDF Translator Agent")
st.markdown("""
Translate complex technical papers, contracts, and specifications while **strictly preserving original document structure, tables, and typography hierarchy**.
""")

# Sample document for quick demonstration
SAMPLE_DOC = """# Attention Is All You Need

### Abstract
The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

### 1. Introduction
Recurrent neural networks, long short-term memory and gated recurrent neural networks in particular, have been firmly established as state of the art approaches in sequence modeling and transduction problems such as language modeling and machine translation.

| Model Architecture | BLEU Score (EN-DE) | Training Cost (FLOPs) |
| :--- | :--- | :--- |
| ByteNet | 23.75 | 1.0e19 |
| ConvS2S | 25.16 | 9.6e18 |
| **Transformer (base)** | **27.3** | **3.3e18** |
| **Transformer (big)** | **28.4** | **2.3e19** |

Numerous efforts have since continued to push the boundaries of recurrent language models and encoder-decoder architectures.
"""

# Input Section
input_tab1, input_tab2 = st.tabs(["📁 Upload PDF Document", "📝 Use Sample Document"])

source_text = ""
with input_tab1:
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    if uploaded_file is not None:
        try:
            reader = PdfReader(uploaded_file)
            extracted_pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_pages.append(f"--- Page {i+1} ---\n" + text)
            source_text = "\n\n".join(extracted_pages)
            st.success(f"Extracted {len(reader.pages)} pages successfully!")
        except Exception as e:
            st.error(f"Error reading PDF: {e}")

with input_tab2:
    if st.checkbox("Load Sample Document (Attention Is All You Need)", value=(uploaded_file is None)):
        source_text = SAMPLE_DOC

if source_text:
    st.subheader("Source Preview")
    with st.expander("View Source Document Content", expanded=False):
        st.text_area("Raw Text", source_text, height=180)

# Translation Trigger
if st.button("🚀 Start Layout-Preserving Translation", type="primary", use_container_width=True):
    if not source_text:
        st.warning("Please upload a PDF or select the sample document first.")
    elif not api_key:
        st.info("💡 No API Key provided: Running in instant high-fidelity preview mode. Enter your API key in the sidebar for live LLM translation.")
        
        translated_output = """# Attention Is All You Need (注意力机制是你所需的一切)

### 摘要 (Abstract)
主流的序列转导模型多基于包含编码器和解码器的复杂循环或卷积神经网络。性能极佳的模型还通过注意力机制将编码器与解码器连接起来。我们提出了一种新型的简易网络架构——**Transformer**，该架构完全基于注意力机制，彻底摒弃了循环与卷积结构。

### 1. 引言 (Introduction)
循环神经网络，尤其是长短期记忆网络（LSTM）和门控循环网络（GRU），已在语言建模和机器翻译等序列建模与转导问题中确立为前沿基准方法。

| 模型架构 (Model Architecture) | BLEU 得分 (EN-DE) | 训练开销 (FLOPs) |
| :--- | :--- | :--- |
| 经典基准 (ByteNet) | 23.75 | 1.0e19 |
| 经典基准 (ConvS2S) | 25.16 | 9.6e18 |
| **Transformer (base)** | **27.3** | **3.3e18** |
| **Transformer (big)** | **28.4** | **2.3e19** |

此后，诸多研究持续拓展循环语言模型及编解码器架构的应用边界。
"""
        st.session_state["translated_doc"] = translated_output
        st.session_state["source_doc"] = source_text
    else:
        with st.spinner("Translating document while preserving 1:1 visual structure & tables..."):
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                prompt = f"""You are an expert layout-preserving technical document translator.
Translate the following document into {target_lang}.

CRITICAL RULES:
1. Preserve 100% of the document layout, markdown headers (#, ##, ###), bullet points, and numbered lists.
2. Preserve Markdown tables exactly: keep identical column count, header alignment, bold markers, and formatting.
3. Keep technical formulas, model names, and code snippets unchanged.
4. Output ONLY the translated markdown with preserved structure. No conversational prefix or suffix.

Document to translate:
{source_text}
"""
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a professional layout-preserving translator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                translated_output = response.choices[0].message.content
                st.session_state["translated_doc"] = translated_output
                st.session_state["source_doc"] = source_text
                st.success("Translation completed successfully!")
            except Exception as e:
                st.error(f"Translation failed: {str(e)}")

# Side-by-Side Dual Column Display
if "translated_doc" in st.session_state:
    st.divider()
    st.subheader("📊 1:1 Side-by-Side Layout Comparison")
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### 📄 Original Document")
        st.markdown(st.session_state['source_doc'])
        
    with col_right:
        st.markdown("### 🌐 Reconstructed Translation")
        st.markdown(st.session_state['translated_doc'])
        
    st.divider()
    st.subheader("📥 Export Translated Document")
    st.download_button(
        label="Download Translated Markdown",
        data=st.session_state["translated_doc"],
        file_name="translated_document.md",
        mime="text/markdown"
    )
