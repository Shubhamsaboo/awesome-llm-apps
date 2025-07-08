## 📈 AI Investment Agent
This Streamlit app is an AI-powered investment agent built with Agno's AI Agent framework that compares the performance of two stocks and generates detailed reports. By using GPT-4o with Yahoo Finance data, this app provides valuable insights to help you make informed investment decisions.

### Features
- Compare the performance of two stocks
- Retrieve comprehensive company information
- Get the latest company news and analyst recommendations

### How to get Started?

1. Clone the GitHub repository

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_investment_agent
```
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```
3. Get your OpenAI API Key

- Sign up for an [OpenAI account](https://platform.openai.com/) (or the LLM provider of your choice) and obtain your API key.

4. Run the Streamlit App
```bash
streamlit run investment_agent.py
```

### How it Works?

- Upon running the app, you will be prompted to enter your OpenAI API key. This key is used to authenticate and access the OpenAI language model.
- Once you provide a valid API key, an instance of the Assistant class is created. This assistant utilizes the GPT-4o language model from OpenAI and the YFinanceTools for accessing stock data.
- Enter the stock symbols of the two companies you want to compare in the provided text input fields.
- The assistant will perform the following steps:
    - Retrieve real-time stock prices and historical data using YFinanceTools
    - Fetch the latest company news and analyst recommendations
    - Gather comprehensive company information
    - Generate a detailed comparison report using the GPT-4 language model
- The generated report will be displayed in the app, providing you with valuable insights and analysis to guide your investment decisions.
