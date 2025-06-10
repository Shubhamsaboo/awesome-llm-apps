# Agente Investigador de OpenAI
Una aplicación de investigación multiagente construida con el SDK de Agentes de OpenAI y Streamlit. Esta aplicación permite a los usuarios realizar investigaciones exhaustivas sobre cualquier tema aprovechando múltiples agentes de IA especializados.

### Características

- Arquitectura Multiagente:
    - Agente de Triaje: Planifica el enfoque de la investigación y coordina el flujo de trabajo
    - Agente de Investigación: Busca en la web y recopila información relevante
    - Agente Editor: Compila los hechos recopilados en un informe completo

- Recopilación Automática de Hechos: Captura hechos importantes de la investigación con atribución de fuente
- Generación de Informes Estructurados: Crea informes bien organizados con títulos, esquemas y citas de fuentes
- Interfaz de Usuario Interactiva: Construida con Streamlit para facilitar la entrada de temas de investigación y la visualización de resultados
- Rastreo y Monitoreo: Rastreo integrado para todo el flujo de trabajo de investigación

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/ai_agent_tutorials/openai_researcher_agent
```

2. Instala las dependencias requeridas:

```bash
cd awesome-llm-apps/ai_agent_tutorials/openai_researcher_agent
pip install -r requirements.txt
```

3. Obtén tu Clave API de OpenAI

- - Regístrate para obtener una [cuenta de OpenAI](https://platform.openai.com/) y obtén tu clave API.
- Establece tu variable de entorno OPENAI_API_KEY.
```bash
export OPENAI_API_KEY='your-api-key-here'
```

4. Ejecuta el equipo de Agentes de IA
```bash
streamlit run openai_researcher_agent.py
```

Luego abre tu navegador y navega a la URL que se muestra en la terminal (generalmente http://localhost:8501).

### Proceso de Investigación:
- Ingresa un tema de investigación en la barra lateral o selecciona uno de los ejemplos proporcionados
- Haz clic en "Iniciar Investigación" para comenzar el proceso
- Visualiza el proceso de investigación en tiempo real en la pestaña "Proceso de Investigación"
- Una vez completado, cambia a la pestaña "Informe" para ver y descargar el informe generado