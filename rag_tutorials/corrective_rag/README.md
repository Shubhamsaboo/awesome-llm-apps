# 🔄 Agente RAG Correctivo
Un sofisticado sistema de Generación Aumentada por Recuperación (RAG) que implementa un flujo de trabajo correctivo de múltiples etapas utilizando LangGraph. Este sistema combina la recuperación de documentos, la calificación de relevancia, la transformación de consultas y la búsqueda web para proporcionar respuestas completas y precisas.

## Características

- **Recuperación Inteligente de Documentos**: Utiliza el almacén de vectores Qdrant para una recuperación eficiente de documentos.
- **Calificación de Relevancia de Documentos**: Emplea Claude 3.5 sonnet para evaluar la relevancia de los documentos.
- **Transformación de Consultas**: Mejora los resultados de búsqueda optimizando las consultas cuando es necesario.
- **Respaldo de Búsqueda Web**: Utiliza la API de Tavily para la búsqueda web cuando los documentos locales no son suficientes.
- **Enfoque Multimodelo**: Combina embeddings de OpenAI y Claude 3.5 sonnet para diferentes tareas.
- **Interfaz de Usuario Interactiva**: Construida con Streamlit para facilitar la carga de documentos y la realización de consultas.

## ¿Cómo Ejecutar?

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd rag_tutorials/corrective_rag
   ```

2. **Instala las Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura las Claves API**:
   Necesitarás obtener las siguientes claves API:
   - [Clave API de OpenAI](https://platform.openai.com/api-keys) (para embeddings)
   - [Clave API de Anthropic](https://console.anthropic.com/settings/keys) (para Claude 3.5 sonnet como LLM)
   - [Clave API de Tavily](https://app.tavily.com/home) (para búsqueda web)
   - Configuración de Qdrant Cloud
      1. Visita [Qdrant Cloud](https://cloud.qdrant.io/)
      2. Crea una cuenta o inicia sesión
      3. Crea un nuevo clúster
      4. Obtén tus credenciales:
         - Clave API de Qdrant: Se encuentra en la sección de Claves API
         - URL de Qdrant: La URL de tu clúster (formato: `https://xxx-xxx.aws.cloud.qdrant.io`)

4. **Ejecuta la Aplicación**:
   ```bash
   streamlit run corrective_rag.py
   ```

5. **Usa la Aplicación**:
   - Carga documentos o proporciona URL
   - Ingresa tus preguntas en el cuadro de consulta
   - Visualiza el proceso RAG Correctivo paso a paso
   - Obtén respuestas completas

## Stack Tecnológico

- **LangChain**: Para orquestación RAG y cadenas
- **LangGraph**: Para gestión de flujos de trabajo
- **Qdrant**: Base de datos vectorial para almacenamiento de documentos
- **Claude 3.5 sonnet**: Modelo de lenguaje principal para análisis y generación
- **OpenAI**: Para embeddings de documentos
- **Tavily**: Para capacidades de búsqueda web
- **Streamlit**: Para la interfaz de usuario
