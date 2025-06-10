## 📚 Agente de Investigación de IA con Memoria
Esta aplicación de Streamlit implementa un asistente de investigación impulsado por IA que ayuda a los usuarios a buscar artículos académicos en arXiv mientras mantiene una memoria de los intereses del usuario y las interacciones pasadas. Utiliza el modelo GPT-4o-mini de OpenAI para procesar los resultados de búsqueda, MultiOn para la navegación web y Mem0 con Qdrant para mantener el contexto del usuario.

### Características

- Interfaz de búsqueda para consultar artículos de arXiv
- Procesamiento impulsado por IA de los resultados de búsqueda para mejorar la legibilidad
- Memoria persistente de los intereses del usuario y búsquedas pasadas
- Utiliza el modelo GPT-4o-mini de OpenAI para un procesamiento inteligente
- Implementa el almacenamiento y recuperación de memoria utilizando Mem0 y Qdrant

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/llm_apps_with_memory_tutorials/ai_arxiv_agent_memory
```

2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```

3. Asegúrate de que Qdrant esté en ejecución:
La aplicación espera que Qdrant esté en ejecución en localhost:6333. Ajusta la configuración en el código si tu configuración es diferente.

```bash
docker pull qdrant/qdrant

docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

4. Ejecuta la Aplicación Streamlit
```bash
streamlit run ai_arxiv_agent_memory.py
```
