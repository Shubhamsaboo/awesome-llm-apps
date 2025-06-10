## 💻 Llama-3.1 Local con RAG
Aplicación Streamlit que te permite chatear con cualquier página web utilizando Llama-3.1 local y Generación Aumentada por Recuperación (RAG). Esta aplicación se ejecuta completamente en tu computadora, lo que la hace 100% gratuita y sin necesidad de conexión a internet.


### Características
- Ingresa la URL de una página web
- Haz preguntas sobre el contenido de la página web
- Obtén respuestas precisas utilizando RAG y el modelo Llama-3.1 ejecutándose localmente en tu computadora

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/llama3.1_local_rag
```
2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```
3. Ejecuta la Aplicación Streamlit
```bash
streamlit run llama3.1_local_rag.py
```

### ¿Cómo Funciona?

- La aplicación carga los datos de la página web utilizando WebBaseLoader y los divide en fragmentos utilizando RecursiveCharacterTextSplitter.
- Crea embeddings de Ollama y un almacén de vectores utilizando Chroma.
- La aplicación configura una cadena RAG (Generación Aumentada por Recuperación), que recupera documentos relevantes basados en la pregunta del usuario.
- Se llama al modelo Llama-3.1 para generar una respuesta utilizando el contexto recuperado.
- La aplicación muestra la respuesta a la pregunta del usuario.

