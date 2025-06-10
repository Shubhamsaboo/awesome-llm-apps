## 🦙 Agente RAG Local con Llama 3.2
Esta aplicación implementa un sistema de Generación Aumentada por Recuperación (RAG) utilizando Llama 3.2 a través de Ollama, con Qdrant como base de datos vectorial.


### Características
- Implementación RAG completamente local
- Impulsado por Llama 3.2 a través de Ollama
- Búsqueda vectorial utilizando Qdrant
- Interfaz de playground interactiva
- Sin dependencias de API externas

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
```

2. Instala las dependencias requeridas:

```bash
cd awesome-llm-apps/rag_tutorials/local_rag_agent
pip install -r requirements.txt
```

3. Instala e inicia la base de datos vectorial [Qdrant](https://qdrant.tech/) localmente

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

4. Instala [Ollama](https://ollama.com/download) y descarga Llama 3.2 para LLM y OpenHermes como el embedder para OllamaEmbedder
```bash
ollama pull llama3.2
ollama pull openhermes
```

4. Ejecuta el Agente RAG de IA
```bash
python local_rag_agent.py
```

5. Abre tu navegador web y navega a la URL proporcionada en la salida de la consola para interactuar con el agente RAG a través de la interfaz del playground.


