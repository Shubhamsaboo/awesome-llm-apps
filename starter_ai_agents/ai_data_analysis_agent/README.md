# 📊 Agente de Análisis de Datos de IA

Un Agente de análisis de datos de IA construido utilizando el framework Agno Agent y el modelo gpt-4o de OpenAI. Este agente ayuda a los usuarios a analizar sus datos (archivos csv, excel) a través de consultas en lenguaje natural, impulsado por los modelos de lenguaje de OpenAI y DuckDB para un procesamiento de datos eficiente, haciendo que el análisis de datos sea accesible para los usuarios independientemente de su experiencia en SQL.

## Características

- 📤 **Soporte para Carga de Archivos**:
  - Carga archivos CSV y Excel
  - Detección automática de tipos de datos e inferencia de esquemas
  - Soporte para múltiples formatos de archivo

- 💬 **Consultas en Lenguaje Natural**:
  - Convierte preguntas en lenguaje natural en consultas SQL
  - Obtén respuestas instantáneas sobre tus datos
  - No se requieren conocimientos de SQL

- 🔍 **Análisis Avanzado**:
  - Realiza agregaciones de datos complejas
  - Filtra y ordena datos
  - Genera resúmenes estadísticos
  - Crea visualizaciones de datos

- 🎯 **Interfaz de Usuario Interactiva**:
  - Interfaz de Streamlit fácil de usar
  - Procesamiento de consultas en tiempo real
  - Presentación clara de resultados

## Cómo Ejecutar

1. **Configurar el Entorno**
   ```bash
   # Clona el repositorio
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_data_analysis_agent

   # Instala las dependencias
   pip install -r requirements.txt
   ```

2. **Configurar Claves API**
   - Obtén la clave API de OpenAI desde [OpenAI Platform](https://platform.openai.com)

3. **Ejecutar la Aplicación**
   ```bash
   streamlit run ai_data_analyst.py
   ```

## Uso

1. Lanza la aplicación utilizando el comando anterior
2. Proporciona tu clave API de OpenAI en la barra lateral de Streamlit
3. Sube tu archivo CSV o Excel a través de la interfaz de Streamlit
4. Haz preguntas sobre tus datos en lenguaje natural
5. Visualiza los resultados y las visualizaciones generadas

