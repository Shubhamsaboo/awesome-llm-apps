# 🚀 Quick Start Guide

## 1. Setup

```bash
# Navigate to the project directory
cd awesome-llm-apps/rag_tutorials/dingo_data_quality_evaluation

# Install dependencies
pip install streamlit pandas plotly numpy

# Optional: Install full requirements for advanced features
pip install -r requirements.txt
```

## 2. Run the Application

```bash
streamlit run dingo_quality_assessment.py
```

The app will open in your browser at `http://localhost:8501`

## 3. Test with Sample Data

1. Select "Sample Data" in the Data Input tab
2. Click "Run Quality Evaluation"
3. View results in the Evaluation Results tab
4. Check recommendations in Quality Insights tab

## 4. Upload Your Own Data

### Supported Formats:
- **JSONL**: `{"text": "your content"}`
- **JSON**: `[{"text": "content1"}, {"text": "content2"}]`
- **CSV**: With columns containing text data
- **TXT**: One sample per line

### Example JSONL file:
```json
{"text": "High-quality, complete sentence with proper grammar."}
{"text": "Incomplete sentence without"}
{"text": "Factual information: Paris is the capital of France."}
```

Use the provided `sample_data.jsonl` for testing!

## 5. Configure Advanced Features

- **Evaluation Groups**: Choose appropriate group for your data type
- **LLM Integration**: Enable for advanced quality assessment
- **API Keys**: Required for LLM-based evaluation

## Next Steps

- Explore different evaluation groups
- Try LLM-based evaluation with your API keys
- Integrate actual Dingo library for production use
