## 🧠 Aplicación LLM con Memoria
Esta aplicación de Streamlit es un chatbot impulsado por IA que utiliza el modelo GPT-4o de OpenAI con una función de memoria persistente. Permite a los usuarios tener conversaciones con la IA mientras se mantiene el contexto a través de múltiples interacciones.

### Características

- Utiliza el modelo GPT-4o de OpenAI para generar respuestas
- Implementa memoria persistente utilizando Mem0 y el almacén de vectores Qdrant
- Permite a los usuarios ver su historial de conversaciones
- Proporciona una interfaz fácil de usar con Streamlit


### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory
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
streamlit run llm_app_memory.py
```
