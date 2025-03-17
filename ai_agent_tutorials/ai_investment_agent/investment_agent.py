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
