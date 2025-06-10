# Agente Planificador de Salud y Fitness con IA 🏋️‍♂️

El **Planificador de Salud y Fitness con IA** es un Agente personalizado de salud y fitness impulsado por el framework Agno AI Agent. Esta aplicación genera planes dietéticos y de fitness personalizados basados en las entradas del usuario, como edad, peso, altura, nivel de actividad, preferencias dietéticas y objetivos de fitness.

## Características

- **Agente de Salud y Agente de Fitness**
    - La aplicación tiene dos agentes phidata que son especialistas en dar consejos de dieta y consejos de fitness/entrenamiento respectivamente.

- **Planes Dietéticos Personalizados**:
  - Genera planes de comidas detallados (desayuno, almuerzo, cena y meriendas).
  - Incluye consideraciones importantes como hidratación, electrolitos e ingesta de fibra.
  - Admite diversas preferencias dietéticas como Keto, Vegetariana, Baja en Carbohidratos, etc.

- **Planes de Fitness Personalizados**:
  - Proporciona rutinas de ejercicio personalizadas basadas en los objetivos de fitness.
  - Cubre calentamientos, entrenamientos principales y enfriamientos.
  - Incluye consejos de fitness procesables y consejos de seguimiento del progreso.

- **Preguntas y Respuestas Interactivas**: Permite a los usuarios hacer preguntas de seguimiento sobre sus planes.


## Requisitos

La aplicación requiere las siguientes bibliotecas de Python:

- `agno`
- `google-generativeai`
- `streamlit`

Asegúrate de que estas dependencias estén instaladas a través del archivo `requirements.txt` de acuerdo con sus versiones mencionadas.

## Cómo Ejecutar

Sigue los pasos a continuación para configurar y ejecutar la aplicación:
Antes que nada, obtén una Clave API de Gemini gratuita proporcionada por Google AI aquí: https://aistudio.google.com/apikey

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_health_fitness_agent
   ```

2. **Instala las dependencias**
    ```bash
    pip install -r requirements.txt
    ```
3. **Ejecuta la aplicación Streamlit**
    ```bash
    streamlit run health_agent.py
    ```


