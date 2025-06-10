# 🧐 RAG Agéntico con Razonamiento
Un sistema RAG sofisticado que demuestra el proceso de razonamiento paso a paso de un agente de IA utilizando Agno, Claude y OpenAI. Esta implementación permite a los usuarios cargar documentos, agregar fuentes web, hacer preguntas y observar el proceso de pensamiento del agente en tiempo real.


## Características

1. Gestión Interactiva de la Base de Conocimientos
- Carga documentos para expandir la base de conocimientos
- Agrega URL dinámicamente para contenido web
- Almacenamiento persistente en base de datos vectorial usando LanceDB


2. Proceso de Razonamiento Transparente
- Visualización en tiempo real de los pasos de pensamiento del agente
- Vista lado a lado del razonamiento y la respuesta final
- Visibilidad clara del proceso RAG


3. Capacidades RAG Avanzadas
- Búsqueda vectorial utilizando embeddings de OpenAI para coincidencia semántica
- Atribución de fuentes con citas


## Configuración del Agente

- Claude 3.5 Sonnet para procesamiento de lenguaje
- Modelo de embedding de OpenAI para búsqueda vectorial
- ReasoningTools para análisis paso a paso
- Instrucciones de agente personalizables

## Requisitos Previos

Necesitarás las siguientes claves API:

1. Clave API de Anthropic

- Regístrate en console.anthropic.com
- Navega a la sección de Claves API
- Crea una nueva clave API

2. Clave API de OpenAI

- Regístrate en platform.openai.com
- Navega a la sección de Claves API
- Genera una nueva clave API

## Cómo Ejecutar

1. **Clona el Repositorio**:
    ```bash
    git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
    cd rag_tutorials/agentic_rag_with_reasoning
    ```

2. **Instala las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Ejecuta la Aplicación:**
    ```bash
    streamlit run rag_reasoning_agent.py
    ```

4. **Configura las Claves API:**

- Ingresa tu clave API de Anthropic en el primer campo
- Ingresa tu clave API de OpenAI en el segundo campo
- Ambas claves son necesarias para que la aplicación funcione


5. **Usa la Aplicación:**

- Agrega Fuentes de Conocimiento: Usa la barra lateral para agregar URL a tu base de conocimientos
- Haz Preguntas: Ingresa consultas en el campo de entrada principal
- Visualiza el Razonamiento: Observa cómo se desarrolla el proceso de pensamiento del agente en tiempo real
- Obtén Respuestas: Recibe respuestas completas con citas de fuentes

## Cómo Funciona

La aplicación utiliza una sofisticada canalización RAG:

### Configuración de la Base de Conocimientos
- Los documentos se cargan desde URL utilizando WebBaseLoader
- El texto se divide en fragmentos y se incrusta utilizando el modelo de embedding de OpenAI
- Los vectores se almacenan en LanceDB para una recuperación eficiente
- La búsqueda vectorial permite la coincidencia semántica para información relevante

### Procesamiento del Agente
- Las consultas del usuario activan el proceso de razonamiento del agente
- ReasoningTools ayuda al agente a pensar paso a paso
- El agente busca en la base de conocimientos información relevante
- Claude 4 Sonnet genera respuestas completas con citas

### Flujo de la Interfaz de Usuario
- Ingresa claves API → Agrega fuentes de conocimiento → Haz preguntas
- El proceso de razonamiento y la generación de respuestas se muestran lado a lado
- Fuentes citadas para transparencia y verificación