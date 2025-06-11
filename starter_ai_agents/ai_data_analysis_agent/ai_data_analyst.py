import json
import tempfile
import csv
import streamlit as st
import pandas as pd
from agno.models.openai import OpenAIChat
from phi.agent.duckdb import DuckDbAgent
from agno.tools.pandas import PandasTools
import re

# Function to preprocess and save the uploaded file
def preprocess_and_save(file):
    try:
        # Read the uploaded file into a DataFrame
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8', na_values=['NA', 'N/A', 'missing'])
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file, na_values=['NA', 'N/A', 'missing'])
        else:
            st.error("Formato de archivo no compatible. Por favor, sube un archivo CSV o Excel.")
            return None, None, None
        
        # Ensure string columns are properly quoted
        for col in df.select_dtypes(include=['object']):
            df[col] = df[col].astype(str).replace({r'"': '""'}, regex=True)
        
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
        st.error(f"Error al procesar el archivo: {e}")
        return None, None, None

# Streamlit app
st.title("📊 Agente Analista de Datos")

# Sidebar for API keys
with st.sidebar:
    st.header("Claves API")
    openai_key = st.text_input("Ingresa tu clave API de OpenAI:", type="password")
    if openai_key:
        st.session_state.openai_key = openai_key
        st.success("¡Clave API guardada!")
    else:
        st.warning("Por favor, ingresa tu clave API de OpenAI para continuar.")

# File upload widget
uploaded_file = st.file_uploader("Sube un archivo CSV o Excel", type=["csv", "xlsx"])

if uploaded_file is not None and "openai_key" in st.session_state:
    # Preprocess and save the uploaded file
    temp_path, columns, df = preprocess_and_save(uploaded_file)
    
    if temp_path and columns and df is not None:
        # Display the uploaded data as a table
        st.write("Datos Cargados:")
        st.dataframe(df)  # Use st.dataframe for an interactive table
        
        # Display the columns of the uploaded data
        st.write("Columnas cargadas:", columns)
        
        # Configure the semantic model with the temporary file path
        semantic_model = {
            "tables": [
                {
                    "name": "uploaded_data",
                    "description": "Contiene el conjunto de datos cargado.",
                    "path": temp_path,
                }
            ]
        }
        
        # Initialize the DuckDbAgent for SQL query generation
        duckdb_agent = DuckDbAgent(
            model=OpenAIChat(model="gpt-4", api_key=st.session_state.openai_key),
            semantic_model=json.dumps(semantic_model),
            tools=[PandasTools()],
            markdown=True,
            add_history_to_messages=False,  # Disable chat history
            followups=False,  # Disable follow-up queries
            read_tool_call_history=False,  # Disable reading tool call history
            system_prompt="Eres un analista de datos experto. Genera consultas SQL para resolver la consulta del usuario. Devuelve solo la consulta SQL, encerrada en ```sql ``` y da la respuesta final.",
        )
        
        # Initialize code storage in session state
        if "generated_code" not in st.session_state:
            st.session_state.generated_code = None
        
        # Main query input widget
        user_query = st.text_area("Haz una consulta sobre los datos:")
        
        # Add info message about terminal output
        st.info("💡 Revisa tu terminal para una salida más clara de la respuesta del agente")
        
        if st.button("Enviar Consulta"):
            if user_query.strip() == "":
                st.warning("Por favor, ingresa una consulta.")
            else:
                try:
                    # Show loading spinner while processing
                    with st.spinner('Procesando tu consulta...'):
                        # Get the response from DuckDbAgent
               
                        response1 = duckdb_agent.run(user_query)

                        # Extract the content from the RunResponse object
                        if hasattr(response1, 'content'):
                            response_content = response1.content
                        else:
                            response_content = str(response1)
                        response = duckdb_agent.print_response(
                        user_query,
                        stream=True,
                        )

                    # Display the response in Streamlit
                    st.markdown(response_content)
                
                    
                except Exception as e:
                    st.error(f"Error al generar la respuesta del DuckDbAgent: {e}")
                    st.error("Por favor, intenta reformular tu consulta o verifica si el formato de los datos es correcto.")