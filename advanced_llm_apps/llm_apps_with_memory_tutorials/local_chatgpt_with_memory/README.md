## 🧠 ChatGPT Local usando Llama 3.1 con Memoria Personal
Esta aplicación Streamlit implementa una experiencia similar a ChatGPT completamente local utilizando Llama 3.1, con almacenamiento de memoria personalizado para cada usuario. Todos los componentes, incluido el modelo de lenguaje, los embeddings y el almacén de vectores, se ejecutan localmente sin necesidad de claves API externas.

### Características
- Implementación completamente local sin dependencias de API externas
- Impulsado por Llama 3.1 a través de Ollama
- Espacio de memoria personal para cada usuario
- Generación local de embeddings utilizando Nomic Embed
- Almacenamiento de vectores con Qdrant

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory
```

2. Instala las dependencias requeridas:

```bash
cd awesome-llm-apps/rag_tutorials/local_rag_agent
pip install -r requirements.txt
```

3. Instala e inicia la base de datos vectorial [Qdrant](https://qdrant.tech/documentation/guides/installation/) localmente

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

4. Instala [Ollama](https://ollama.com/download) y descarga Llama 3.1
```bash
ollama pull llama3.1
```

5. Ejecuta la Aplicación Streamlit
```bash
streamlit run local_chatgpt_memory.py
```