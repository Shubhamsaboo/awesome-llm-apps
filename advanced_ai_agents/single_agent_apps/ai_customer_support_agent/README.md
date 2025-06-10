## 🛒 Agente de Soporte al Cliente de IA con Memoria
Esta aplicación de Streamlit implementa un agente de soporte al cliente impulsado por IA para datos sintéticos generados con GPT-4o. El agente utiliza el modelo GPT-4o de OpenAI y mantiene una memoria de interacciones pasadas utilizando la biblioteca Mem0 con Qdrant como almacén de vectores.

### Características

- Interfaz de chat para interactuar con el agente de soporte al cliente de IA
- Memoria persistente de interacciones y perfiles de clientes
- Generación de datos sintéticos para pruebas y demostración
- Utiliza el modelo GPT-4o de OpenAI para respuestas inteligentes

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_customer_support_agent
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
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```

4. Ejecuta la Aplicación Streamlit
```bash
streamlit run customer_support_agent.py
```
