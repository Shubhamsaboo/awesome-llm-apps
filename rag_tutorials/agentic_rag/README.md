## 🗃️ Agente RAG de IA con Acceso Web
Este script demuestra cómo construir un agente de Generación Aumentada por Recuperación (RAG) con acceso web utilizando GPT-4o en solo 15 líneas de código Python. El agente utiliza una base de conocimientos en PDF y tiene la capacidad de buscar en la web utilizando DuckDuckGo.

### Características

- Crea un agente RAG utilizando GPT-4o
- Incorpora una base de conocimientos basada en PDF
- Utiliza LanceDB como base de datos vectorial para una búsqueda eficiente por similitud
- Incluye capacidad de búsqueda web a través de DuckDuckGo
- Proporciona una interfaz de playground para una fácil interacción

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/agentic_rag
```

2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```

3. Obtén tu Clave API de OpenAI

- Regístrate para obtener una [cuenta de OpenAI](https://platform.openai.com/) (o el proveedor de LLM de tu elección) y obtén tu clave API.
- Establece tu clave API de OpenAI como una variable de entorno:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

4. Ejecuta el Agente RAG de IA
```bash
python3 rag_agent.py
```
5. Abre tu navegador web y navega a la URL proporcionada en la salida de la consola para interactuar con el agente RAG a través de la interfaz del playground.

### ¿Cómo Funciona?

1. **Creación de la Base de Conocimientos:** El script crea una base de conocimientos a partir de un archivo PDF alojado en línea.
2. **Configuración de la Base de Datos Vectorial:** Se utiliza LanceDB como base de datos vectorial para una búsqueda eficiente por similitud dentro de la base de conocimientos.
3. **Configuración del Agente:** Se crea un agente de IA utilizando GPT-4o como modelo subyacente, con la base de conocimientos en PDF y la herramienta de búsqueda DuckDuckGo.
4. **Configuración del Playground:** Se configura una interfaz de playground para una fácil interacción con el agente RAG.

