# PharmaQuery

## Descripción General
PharmaQuery es un Sistema Avanzado de Recuperación de Información Farmacéutica diseñado para ayudar a los usuarios a obtener información significativa de artículos de investigación y documentos en el dominio farmacéutico.

## Demostración
https://github.com/user-attachments/assets/c12ee305-86fe-4f71-9219-57c7f438f291

## Características
- **Consultas en Lenguaje Natural**: Realiza preguntas complejas sobre la industria farmacéutica y obtén respuestas concisas y precisas.
- **Base de Datos Personalizada**: Sube tus propios documentos de investigación para mejorar la base de conocimientos del sistema de recuperación.
- **Búsqueda por Similitud**: Recupera los documentos más relevantes para tu consulta utilizando embeddings de IA.
- **Interfaz Streamlit**: Interfaz fácil de usar para consultas y carga de documentos.

## Tecnologías Utilizadas
- **Lenguaje de Programación**: [Python 3.10+](https://www.python.org/downloads/release/python-31011/)
- **Framework**: [LangChain](https://www.langchain.com/)
- **Base de Datos**: [ChromaDB](https://www.trychroma.com/)
- **Modelos**:
  - Embeddings: [Google Gemini API (embedding-001)](https://ai.google.dev/gemini-api/docs/embeddings)
  - Chat: [Google Gemini API (gemini-1.5-pro)](https://ai.google.dev/gemini-api/docs/models/gemini#gemini-1.5-pro)
- **Procesamiento de PDF**: [PyPDFLoader](https://python.langchain.com/docs/integrations/document_loaders/pypdfloader/)
- **Divisor de Documentos**: [SentenceTransformersTokenTextSplitter](https://python.langchain.com/api_reference/text_splitters/sentence_transformers/langchain_text_splitters.sentence_transformers.SentenceTransformersTokenTextSplitter.html)

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
   - Ingresa tu consulta en la interfaz principal.
   - Opcionalmente, sube artículos de investigación en la barra lateral para mejorar la base de datos.

## :mailbox: Conéctate Conmigo
<img align="right" src="https://media.giphy.com/media/2HtWpp60NQ9CU/giphy.gif" alt="handshake gif" width="150">

<p align="left">
  <a href="https://linkedin.com/in/codewithcharan" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/linked-in-alt.svg" alt="codewithcharan" height="30" width="40" style="margin-right: 10px" /></a>
  <a href="https://instagram.com/joyboy._.ig" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/instagram.svg" alt="__mr.__.unique" height="30" width="40" /></a>
  <a href="https://twitter.com/Joyboy_x_" target="blank"><img align="center" src="https://raw.githubusercontent.com/rahuldkjain/github-profile-readme-generator/master/src/images/icons/Social/twitter.svg" alt="codewithcharan" height="30" width="40" style="margin-right: 10px" /></a>
</p>