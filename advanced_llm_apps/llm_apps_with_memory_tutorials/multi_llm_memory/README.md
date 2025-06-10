## 🧠 Aplicación Multi-LLM con Memoria Compartida
Esta aplicación Streamlit demuestra un sistema multi-LLM con una capa de memoria compartida, permitiendo a los usuarios interactuar con diferentes modelos de lenguaje mientras se mantiene el historial de conversaciones y el contexto a través de las sesiones.

### Características

- Soporte para múltiples LLMs:
    - GPT-4o de OpenAI
    - Claude 3.5 Sonnet de Anthropic

- Memoria persistente utilizando el almacén de vectores Qdrant
- Historial de conversaciones específico del usuario
- Recuperación de memoria para respuestas contextuales
- Interfaz fácil de usar con selección de LLM

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/llm_apps_with_memory_tutorials/multi_llm_memory
```

2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```

3. Asegúrate de que Qdrant esté en ejecución:
La aplicación espera que Qdrant esté en ejecución en localhost:6333. Ajusta la configuración en el código si tu configuración es diferente.

```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

4. Ejecuta la Aplicación Streamlit
```bash
streamlit run multi_llm_memory.py
```