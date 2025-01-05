# AI Data Visualization Agent

This Assistant is designed to help anyone create and visualize data using natural language commands, and it is built using Together AI and E2B Code Interpreter. User gets to upload a dataset and ask questions to the LLM to get the data visualized. This demo can be considered as a demo for the E2B Code Interpreter and Together AI, for anyone who's getting started with these libraries!

## Demo

https://github.com/user-attachments/assets/d8414c37-5edd-4e4d-a7b1-b9ab500bd8cd

## Features

- 🎨 Natural language-driven visualization creation
- 📊 Support for multiple chart types (line, bar, scatter, pie, bubble)
- 📈 Automatic data preprocessing and cleaning
- 🎯 Available Models:
  - Meta-Llama 3.1 405B
  - DeepSeek V3
  - Qwen 2.5 7B
  - Meta-Llama 3.3 70B
- 📱 The Code runs in the E2B Sandbox environment, so it is secure and fast
- Streamlit for clear and interactive user interface

## How to Run

Follow the steps below to set up and run the application:
Before anything else, Please get a free Together AI API Key here: https://api.together.ai/signin
Get a free E2B API Key here: https://e2b.dev/ ; https://e2b.dev/docs/legacy/getting-started/api-key

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_data_visualisation_agent
   ```

2. **Install the dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the Streamlit app**
    ```bash
    streamlit run ai_data_visualisation_agent.py
    ```

