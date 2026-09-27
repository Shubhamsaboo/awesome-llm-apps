# 📊 AI Data Analysis Agent

### 🎓 FREE Step-by-Step Tutorial 
**👉 [Click here to follow our complete step-by-step tutorial](https://www.theunwindai.com/p/build-an-ai-data-analysis-agent) and learn how to build this from scratch with detailed code walkthroughs, explanations, and best practices.**

An AI data analysis Agent built using the Agno Agent framework and Openai's gpt-4o model. This agent helps users analyze their data - csv, excel files through natural language queries, powered by OpenAI's language models and DuckDB for efficient data processing - making data analysis accessible to users regardless of their SQL expertise.

## Features

- 📤 **File Upload Support**: 
  - Upload CSV and Excel files
  - Automatic data type detection and schema inference
  - Support for multiple file formats

- 💬 **Natural Language Queries**: 
  - Convert natural language questions into SQL queries
  - Get instant answers about your data
  - No SQL knowledge required

- 🤔 **Asks Before Assuming**:
  - When a question is ambiguous, the agent asks what you mean instead of guessing, and runs no queries until you answer
  - It treats a question as ambiguous when it:
    - uses a vague measure that could map to different columns, such as "best", "top", "doing well", "performance" or "growth"
    - leaves the time period or comparison unclear in a way that changes the answer
    - asks for something the data cannot measure directly, such as profit when there is no cost column
  - The clarifying question comes with 2–4 suggested options based on the actual columns in your file
  - You can pick an option, choose "Something else" and describe it in your own words, or click "Answer anyway with assumptions" to let the agent choose the most reasonable interpretation and state its assumptions at the top of the answer
  - Your original question and your answer are sent to the agent together, and it answers without asking again
  - The answer shows the question with the meaning you chose, for example "Which region is doing best? (Highest total revenue)"
  - Clear questions are answered straight away, with no extra step

- 🔍 **Advanced Analysis**:
  - Perform complex data aggregations
  - Filter and sort data
  - Generate statistical summaries
  - Create data visualizations

- 📈 **Automatic Charts**:
  - Every answer is paired with an interactive chart of the data behind it
  - The chart is built from the agent's last successful SQL query, re-run against DuckDB, so it shows the actual result table rather than numbers parsed from text
  - Picks a sensible default: line chart for dates, bar chart (sorted by value) for categories, scatter plot for purely numeric results
  - Single-row results, such as a total or an average, are shown as metric tiles instead of a chart
  - Switch the chart type (Bar, Line, Area, Scatter), X axis and one or more Y axis columns; multiple Y columns are drawn as colored series
  - Hover for tooltips, and zoom or pan the chart
  - Expand "Query and result data" to see the SQL that was charted and its result table
  - Built with Altair, which ships with Streamlit, so no extra dependencies are needed

- 🎯 **Interactive UI**:
  - User-friendly Streamlit interface
  - Real-time query processing
  - Clear result presentation

## How to Run

1. **Setup Environment**
   ```bash
   # Clone the repository
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/starter_ai_agents/ai_data_analysis_agent

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - Get OpenAI API key from [OpenAI Platform](https://platform.openai.com)

3. **Run the Application**
   ```bash
   streamlit run ai_data_analyst.py
   ```

## Usage

1. Launch the application using the command above
2. Provide your OpenAI API key in the sidebar of Streamlit
3. Upload your CSV or Excel file through the Streamlit interface
4. Ask questions about your data in natural language
   - If the agent asks for more detail, pick an option or describe what you meant and click "Continue"
   - To skip the question, click "Answer anyway with assumptions"
5. Read the answer, then use the chart below it to explore the result
   - Adjust the chart type and axes; the answer stays on screen while you do
   - Questions that group or aggregate data (for example "total revenue by region" or "monthly sales over time") give the most useful charts
   - If the agent's queries returned no table, only the text answer is shown

## Example Questions

These use the included `sample_sales.csv` (sales by date, region and product, January to early March 2025).

**Clear questions**, answered directly:
- "What is the total revenue by region?"
- "Show monthly revenue over time"
- "How many units of each product were sold?"

**Ambiguous questions**, where the agent should ask for more detail first:

| Question | Why it is ambiguous |
| --- | --- |
| "Which region is doing best?" | Best by revenue, units sold, or growth? |
| "What's our star product?" | Security earns the most revenue, but Analytics sells the most units |
| "Are we growing?" | Compared over which period? March has only one sale, so a month-by-month comparison is misleading |
| "Which product is most profitable?" | There is no cost column, so profit cannot be calculated; the agent should offer revenue instead |
| "Who's underperforming?" | Measured by what, and compared with what? |

Whether a question counts as ambiguous is decided by the model, so it may occasionally answer a vague question directly or ask about a clear one.

