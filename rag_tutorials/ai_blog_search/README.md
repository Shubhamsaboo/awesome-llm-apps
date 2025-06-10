# RAG Agéntico con LangGraph: Búsqueda de Blogs de IA

## Descripción General
AI Blog Search es una aplicación RAG Agéntica diseñada para mejorar la recuperación de información de publicaciones de blogs relacionadas con la IA. Este sistema aprovecha LangChain, LangGraph y el modelo Gemini de Google para obtener, procesar y analizar contenido de blogs, proporcionando a los usuarios respuestas precisas y contextualmente relevantes.

## Flujo de Trabajo de LangGraph
![LangGraph-Workflow](https://github.com/user-attachments/assets/07d8a6b5-f1ef-4b7e-b47a-4f14a192bd8a)

## Demostración
https://github.com/user-attachments/assets/cee07380-d3dc-45f4-ad26-7d944ba9c32b

## Características
- **Recuperación de Documentos:** Utiliza Qdrant como base de datos vectorial para almacenar y recuperar contenido de blogs basado en embeddings.
- **Procesamiento Agéntico de Consultas:** Utiliza un agente impulsado por IA para determinar si una consulta debe ser reescrita, respondida o requiere más recuperación.
- **Evaluación de Relevancia:** Implementa un sistema automatizado de calificación de relevancia utilizando el modelo Gemini de Google.
- **Refinamiento de Consultas:** Mejora las consultas mal estructuradas para obtener mejores resultados de recuperación.
- **Interfaz de Usuario Streamlit:** Proporciona una interfaz fácil de usar para ingresar URL de blogs, consultas y recuperar respuestas perspicaces.
- **Flujo de Trabajo Basado en Grafos:** Implementa un grafo de estado estructurado utilizando LangGraph para una toma de decisiones eficiente.

## Tecnologías Utilizadas
- **Lenguaje de Programación**: [Python 3.10+](https://www.python.org/downloads/release/python-31011/)
- **Framework**: [LangChain](https://www.langchain.com/) y [LangGraph](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
- **Base de Datos**: [Qdrant](https://qdrant.tech/)
- **Modelos**:
  - Embeddings: [Google Gemini API (embedding-001)](https://ai.google.dev/gemini-api/docs/embeddings)
  - Chat: [Google Gemini API (gemini-2.0-flash)](https://ai.google.dev/gemini-api/docs/models/gemini#gemini-2.0-flash)
- **Cargador de Blogs**: [Langchain WebBaseLoader](https://python.langchain.com/docs/integrations/document_loaders/web_base/)
- **Divisor de Documentos**: [RecursiveCharacterTextSplitter](https://python.langchain.com/v0.1/docs/modules/data_connection/document_transformers/recursive_text_splitter/)
- **Interfaz de Usuario (UI)**: [Streamlit](https://docs.streamlit.io/)

## Requisitos
1. **Instalar Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ejecutar la Aplicación**:
   ```bash
   streamlit run app.py
   ```

3. **Usar la Aplicación**:
   - Pega tu Clave API de Google en la barra lateral.
   - Pega el enlace del blog.
   - Ingresa tu consulta sobre la publicación del blog.

## :mailbox: Conéctate Conmigo
<img align="right" src="https://media.giphy.com/media/2HtWpp60NQ9CU/giphy.gif" alt="handshake gif" width="150">

<p align="left">
  <a href="https://linkedin.com/in/codewithcharan" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/linked-in-alt.svg" alt="codewithcharan" height="30" width="40" style="margin-right: 10px" /></a>
  <a href="https://instagram.com/joyboy._.ig" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/instagram.svg" alt="__mr.__.unique" height="30" width="40" /></a>
  <a href="https://twitter.com/Joyboy_x_" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/twitter.svg" alt="codewithcharan" height="30" width="40" style="margin-right: 10px" /></a>
</p>

<img src="https://readme-typing-svg.herokuapp.com/?font=Righteous&size=35&center=true&vCenter=true&width=500&height=70&duration=4000&lines=Thanks+for+visiting!+👋;+Message+me+on+Linkedin!;+I'm+always+down+to+collab+:)"/>