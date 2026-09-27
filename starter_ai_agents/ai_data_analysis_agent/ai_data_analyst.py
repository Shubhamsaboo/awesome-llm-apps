import os
import re
import tempfile
import csv
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import altair as alt
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckdb import DuckDbTools
from agno.tools.pandas import PandasTools

load_dotenv(Path(__file__).with_name(".env"))

# Marker the agent uses when it needs more detail instead of assuming
CLARIFY_MARKER = "CLARIFY:"

# Function to preprocess and save the uploaded file
def preprocess_and_save(file):
    try:
        # Read the uploaded file into a DataFrame
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8', na_values=['NA', 'N/A', 'missing'])
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file, na_values=['NA', 'N/A', 'missing'])
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return None, None, None
        
        # Parse dates and numeric columns
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    # Keep as is if conversion fails
                    pass
        
        # Create a temporary file to save the preprocessed data
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            temp_path = temp_file.name
            # Save the DataFrame to the temporary CSV file with quotes around string fields
            df.to_csv(temp_path, index=False, quoting=csv.QUOTE_ALL)
        
        return temp_path, df.columns.tolist(), df  # Return the DataFrame as well
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None, None

# Re-run the agent's last successful SQL query to get its result as a DataFrame
def get_result_dataframe(response, duckdb_tools):
    for tool in reversed(getattr(response, "tools", None) or []):
        query = (tool.tool_args or {}).get("query")
        if tool.tool_name != "run_query" or not query:
            continue
        # Same formatting DuckDbTools.run_query applies before executing
        sql = query.replace("`", "").split(";")[0]
        try:
            return sql, duckdb_tools.connection.sql(sql).df()
        except Exception:
            # Skip queries that failed or returned no result set
            continue
    return None, None

# Detect a clarifying question and split it into the question and its options
def parse_clarification(content):
    lines = [line.strip() for line in content.strip().splitlines() if line.strip()]
    if not lines:
        return None
    # Tolerate markdown decoration such as **CLARIFY:** or ### CLARIFY:
    first_line = re.sub(r"^[#>*_\s]+", "", lines[0])
    match = re.match(r"CLARIFY[*_]*\s*:[*_]*\s*(.*)", first_line, re.IGNORECASE)
    if not match:
        return None

    question_parts = [match.group(1).strip()]
    options = []
    for line in lines[1:]:
        option = re.match(r"^(?:[-*•]|\d+[.)])\s+(.*)", line)
        if option:
            options.append(option.group(1).strip())
        else:
            question_parts.append(line)
    question = " ".join(part for part in question_parts if part)
    return question or "Could you give a bit more detail about what you want to know?", options

# Escape characters Vega-Lite treats as nested field access
def altair_field(name):
    return str(name).replace(".", "\\.").replace("[", "\\[").replace("]", "\\]")

# Render the query result as an interactive Altair chart
def render_result_chart(result_df):
    numeric_cols = result_df.select_dtypes(include="number").columns.tolist()
    if result_df.empty or not numeric_cols:
        st.caption("The query result has no numeric columns to chart.")
        return

    # A single-row result (e.g. a total or average) reads better as metrics
    if len(result_df) == 1:
        metric_cols = st.columns(min(len(numeric_cols), 4))
        for i, col in enumerate(numeric_cols):
            value = result_df[col].iloc[0]
            value_format = ",.0f" if pd.api.types.is_integer_dtype(result_df[col]) else ",.2f"
            metric_cols[i % len(metric_cols)].metric(str(col), format(value, value_format))
        return

    datetime_cols = result_df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    category_cols = [c for c in result_df.columns if c not in numeric_cols and c not in datetime_cols]

    # Pick sensible defaults: time series -> line, categories -> bar, numbers only -> scatter
    if datetime_cols:
        default_x, default_type = datetime_cols[0], "Line"
    elif category_cols:
        default_x, default_type = category_cols[0], "Bar"
    else:
        default_x, default_type = result_df.columns[0], "Scatter"

    chart_types = ["Bar", "Line", "Area", "Scatter"]
    all_cols = result_df.columns.tolist()
    ctrl_type, ctrl_x, ctrl_y = st.columns([1, 1, 2])
    chart_type = ctrl_type.selectbox("Chart type", chart_types, index=chart_types.index(default_type))
    x_col = ctrl_x.selectbox("X axis", all_cols, index=all_cols.index(default_x))
    y_options = [c for c in numeric_cols if c != x_col]
    if not y_options:
        st.caption("Pick a different X axis to leave a numeric column for the Y axis.")
        return
    y_cols = ctrl_y.multiselect("Y axis", y_options, default=y_options[:1])
    if not y_cols:
        st.caption("Select at least one Y axis column.")
        return

    # Long format lets several Y columns share one chart, colored by series
    long_df = result_df.melt(id_vars=[x_col], value_vars=y_cols, var_name="series", value_name="value")

    if x_col in datetime_cols:
        x_type = "temporal"
    elif x_col in numeric_cols:
        x_type = "quantitative"
    else:
        x_type = "nominal"
    x_sort = "-y" if chart_type == "Bar" and x_type == "nominal" and len(y_cols) == 1 else None

    marks = {
        "Bar": alt.Chart(long_df).mark_bar(),
        "Line": alt.Chart(long_df).mark_line(point=True),
        "Area": alt.Chart(long_df).mark_area(opacity=0.6),
        "Scatter": alt.Chart(long_df).mark_circle(size=80),
    }
    encoding = {
        "x": alt.X(field=altair_field(x_col), type=x_type, title=str(x_col), sort=x_sort),
        "y": alt.Y("value:Q", title=y_cols[0] if len(y_cols) == 1 else "Value", stack=None if chart_type == "Area" else "zero"),
        "tooltip": [
            alt.Tooltip(field=altair_field(x_col), type=x_type, title=str(x_col)),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("value:Q", title="Value", format=",.2f"),
        ],
    }
    if len(y_cols) > 1:
        encoding["color"] = alt.Color("series:N", title=None)
        if chart_type == "Bar":
            encoding["xOffset"] = "series:N"

    st.altair_chart(marks[chart_type].encode(**encoding).interactive(), use_container_width=True)

# Streamlit app
st.title("📊 Data Analyst Agent")

# Sidebar for API keys
with st.sidebar:
    st.header("API Keys")
    openai_key = st.text_input(
        "Enter your OpenAI API key:",
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
    )
    if openai_key:
        st.session_state.openai_key = openai_key
        st.success("API key saved!")
    else:
        st.warning("Please enter your OpenAI API key to proceed.")

# File upload widget
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None and "openai_key" in st.session_state:
    # Preprocess and save the uploaded file
    temp_path, columns, df = preprocess_and_save(uploaded_file)
    
    if temp_path and columns and df is not None:
        # Display the uploaded data as a table
        st.write("Uploaded Data:")
        st.dataframe(df)  # Use st.dataframe for an interactive table
        
        # Display the columns of the uploaded data
        st.write("Uploaded columns:", columns)
        
        # Initialize DuckDbTools
        duckdb_tools = DuckDbTools()
        
        # Load the CSV file into DuckDB as a table
        duckdb_tools.load_local_csv_to_table(
            path=temp_path,
            table="uploaded_data",
        )
        
        # Describe the columns so the agent can offer concrete clarification options
        column_summary = ", ".join(f"{col} ({dtype})" for col, dtype in df.dtypes.astype(str).items())

        # Initialize the Agent with DuckDB and Pandas tools
        data_analyst_agent = Agent(
            model=OpenAIChat(id="gpt-4o", api_key=st.session_state.openai_key),
            tools=[duckdb_tools, PandasTools()],
            system_message=(
                "You are an expert data analyst. Use the 'uploaded_data' table to answer user queries. "
                f"The table has these columns and types: {column_summary}. "
                "Generate SQL queries using DuckDB tools to solve the user's query. Provide clear and concise answers with the results. "
                "Make your final run_query call the query whose result table best answers the question (for example grouped aggregates), because that result is charted for the user.\n\n"
                "Before running any query, decide whether the question is ambiguous. It is ambiguous when it uses a vague measure "
                "('best', 'top', 'doing well', 'performance', 'growth') that could map to different columns, leaves the time period or "
                "comparison unclear when that changes the answer, or asks for something the columns cannot measure directly "
                "(for example profit when there is no cost column). If it is ambiguous, do not guess and do not run queries. "
                f"Reply with only a first line '{CLARIFY_MARKER} <one short question>' followed by 2-4 lines starting with '- ', "
                "each a concrete option answerable from the columns above. Ask about the single most important ambiguity. "
                "If the question is clear, answer it directly."
            ),
            markdown=True,
        )

        # Initialize code storage in session state
        if "generated_code" not in st.session_state:
            st.session_state.generated_code = None

        # Run the agent and store either an answer or a clarifying question
        def run_analysis(prompt, display_query):
            try:
                # Show loading spinner while processing
                with st.spinner('Processing your query...'):
                    # Get the response from the agent
                    response = data_analyst_agent.run(prompt)

                    # Extract the content from the response object
                    if hasattr(response, 'content'):
                        response_content = response.content
                    else:
                        response_content = str(response)

                    clarification = parse_clarification(response_content)
                    if clarification:
                        # Ask the user instead of letting the agent assume
                        question, options = clarification
                        st.session_state.last_result = None
                        st.session_state.pending_clarification = {
                            "file": uploaded_file.name,
                            "query": display_query,
                            "question": question,
                            "options": options,
                        }
                        return

                    result_sql, result_df = get_result_dataframe(response, duckdb_tools)

                # Keep the result in session state so chart controls survive reruns
                st.session_state.last_result = {
                    "file": uploaded_file.name,
                    "query": display_query,
                    "content": response_content,
                    "sql": result_sql,
                    "df": result_df,
                }
            except Exception as e:
                st.error(f"Error generating response from the agent: {e}")
                st.error("Please try rephrasing your query or check if the data format is correct.")

        # Main query input widget
        user_query = st.text_area("Ask a query about the data:")

        # Add info message about terminal output
        st.info("💡 Check your terminal for a clearer output of the agent's response")

        if st.button("Submit Query"):
            if user_query.strip() == "":
                st.warning("Please enter a query.")
            else:
                st.session_state.pending_clarification = None
                run_analysis(user_query, user_query)

        pending = st.session_state.get("pending_clarification")
        if pending and pending["file"] == uploaded_file.name:
            # Placeholder so the form can be removed once it is answered
            clarification_box = st.empty()
            with clarification_box.container():
                st.info(f"🤔 **Your question needs a bit more detail.** {pending['question']}")
                clarification_form = st.form("clarification_form")
            with clarification_form:
                other_label = "Something else"
                choice = None
                if pending["options"]:
                    choice = st.radio("Choose what you meant:", pending["options"] + [other_label])
                details = st.text_input(
                    "Or describe it in your own words:" if pending["options"] else "Your answer:",
                )
                continue_col, skip_col = st.columns(2)
                submitted = continue_col.form_submit_button("Continue", type="primary")
                skipped = skip_col.form_submit_button("Answer anyway with assumptions")

            if submitted:
                if choice and choice != other_label:
                    answer = f"{choice}. {details}" if details.strip() else choice
                else:
                    answer = details.strip()
                if not answer:
                    st.warning("Please choose an option or describe what you meant.")
                else:
                    st.session_state.pending_clarification = None
                    clarification_box.empty()
                    run_analysis(
                        f"Original question: {pending['query']}\n"
                        f"You asked: {pending['question']}\n"
                        f"User's answer: {answer}\n\n"
                        "The question is now clarified. Do not ask another clarifying question; answer it, "
                        "briefly stating any remaining assumptions.",
                        f"{pending['query']} ({answer})",
                    )
            elif skipped:
                st.session_state.pending_clarification = None
                clarification_box.empty()
                run_analysis(
                    f"{pending['query']}\n\n"
                    "The user chose not to clarify. Do not ask a clarifying question; answer using the most "
                    "reasonable interpretation and state the assumptions you made at the start of your answer.",
                    pending["query"],
                )

        last_result = st.session_state.get("last_result")
        if last_result and last_result["file"] == uploaded_file.name:
            # Display the response in Streamlit
            st.markdown(f"**Question:** {last_result['query']}")
            st.markdown(last_result["content"])

            if last_result["df"] is not None:
                st.subheader("📈 Chart")
                render_result_chart(last_result["df"])
                with st.expander("Query and result data"):
                    st.code(last_result["sql"], language="sql")
                    st.dataframe(last_result["df"], use_container_width=True)