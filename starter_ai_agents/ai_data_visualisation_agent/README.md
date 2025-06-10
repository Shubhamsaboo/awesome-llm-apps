# 📊 Agente de Visualización de Datos de IA
Una aplicación de Streamlit que actúa como tu experto personal en visualización de datos, impulsada por LLMs. Simplemente carga tu conjunto de datos y haz preguntas en lenguaje natural: el agente de IA analizará tus datos, generará las visualizaciones adecuadas y proporcionará información a través de una combinación de gráficos, estadísticas y explicaciones.

## Características
#### Análisis de Datos en Lenguaje Natural
- Haz preguntas sobre tus datos en español sencillo
- Obtén visualizaciones instantáneas y análisis estadísticos
- Recibe explicaciones de los hallazgos y perspectivas
- Interrogatorio interactivo de seguimiento

#### Selección Inteligente de Visualización
- Elección automática de los tipos de gráficos apropiados
- Generación dinámica de visualizaciones
- Soporte para visualización estadística
- Formato y estilo de gráficos personalizados

#### Soporte de IA Multi-Modelo
- Meta-Llama 3.1 405B para análisis complejos
- DeepSeek V3 para perspectivas detalladas
- Qwen 2.5 7B para análisis rápidos
- Meta-Llama 3.3 70B para consultas avanzadas

## Cómo Ejecutar

Sigue los pasos a continuación para configurar y ejecutar la aplicación:
- Antes que nada, obtén una clave API gratuita de Together AI aquí: https://api.together.ai/signin
- Obtén una clave API gratuita de E2B aquí: https://e2b.dev/ ; https://e2b.dev/docs/legacy/getting-started/api-key

1. **Clona el Repositorio**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_data_visualisation_agent
   ```
2. **Instala las dependencias**
    ```bash
    pip install -r requirements.txt
    ```
3. **Ejecuta la aplicación Streamlit**
    ```bash
    streamlit run ai_data_visualisation_agent.py
    ```