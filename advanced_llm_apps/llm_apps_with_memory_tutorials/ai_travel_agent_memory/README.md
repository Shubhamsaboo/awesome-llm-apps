## 🧳 Agente de Viajes de IA con Memoria
Esta aplicación de Streamlit implementa un asistente de viajes impulsado por IA que recuerda las preferencias del usuario y las interacciones pasadas. Utiliza GPT-4o de OpenAI para generar respuestas y Mem0 con Qdrant para mantener el historial de conversaciones.

### Características
- Interfaz basada en chat para interactuar con un asistente de viajes de IA
- Memoria persistente de las preferencias del usuario y conversaciones pasadas
- Utiliza el modelo GPT-4o de OpenAI para respuestas inteligentes
- Implementa el almacenamiento y recuperación de memoria utilizando Mem0 y Qdrant
- Historial de conversaciones específico del usuario y visualización de la memoria

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/llm_apps_with_memory_tutorials/ai_travel_agent_memory
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
streamlit run travel_agent_memory.py
```
