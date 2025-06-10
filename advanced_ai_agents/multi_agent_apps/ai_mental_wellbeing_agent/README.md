# Equipo de Agentes de Bienestar Mental de IA 🧠

El Equipo de Agentes de Bienestar Mental de IA es un sistema de evaluación y orientación de salud mental de apoyo impulsado por el framework de Agentes de IA de [AG2](https://github.com/ag2ai/ag2?tab=readme-ov-file) (anteriormente AutoGen). Esta aplicación proporciona apoyo personalizado de salud mental a través de la coordinación de agentes de IA especializados, cada uno centrado en diferentes aspectos del cuidado de la salud mental basados en las entradas del usuario, como el estado emocional, los niveles de estrés, los patrones de sueño y los síntomas actuales. Esto se basa en la nueva función de enjambre de AG2 ejecutada a través del método `initiate_swarm_chat()`.

## Características

- **Equipo Especializado de Apoyo al Bienestar Mental**
    - 🧠 **Agente de Evaluación**: Analiza el estado emocional y las necesidades psicológicas con precisión clínica y empatía
    - 🎯 **Agente de Acción**: Crea planes de acción inmediatos y conecta a los usuarios con los recursos apropiados
    - 🔄 **Agente de Seguimiento**: Diseña estrategias de apoyo a largo plazo y planes de prevención

- **Apoyo Integral al Bienestar Mental**:
  - Evaluación psicológica detallada
  - Estrategias de afrontamiento inmediatas
  - Recomendaciones de recursos
  - Planificación de apoyo a largo plazo
  - Estrategias de prevención de crisis
  - Sistemas de seguimiento del progreso

- **Parámetros de Entrada Personalizables**:
  - Estado emocional actual
  - Patrones de sueño
  - Niveles de estrés
  - Información del sistema de apoyo
  - Cambios recientes en la vida
  - Síntomas actuales

- **Resultados Interactivos**:
   - Resúmenes de evaluación en tiempo real
   - Recomendaciones detalladas en secciones expandibles
   - Pasos de acción y recursos claros
   - Estrategias de apoyo a largo plazo

## Cómo Ejecutar

Sigue estos pasos para configurar y ejecutar la aplicación:

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent
   ```

2. **Instala las Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Crea un Archivo de Entorno**:
   Crea un archivo `.env` en el directorio del proyecto:
   ```bash
   echo "AUTOGEN_USE_DOCKER=0" > .env
   ```
   Esto deshabilita el requisito de Docker para la ejecución de código en AutoGen.

4. **Configura la Clave API de OpenAI**:
   - Obtén una clave API de OpenAI desde la [plataforma de OpenAI](https://platform.openai.com)
   - Ingresarás esta clave en la barra lateral de la aplicación al ejecutarla

5. **Ejecuta la Aplicación Streamlit**:
   ```bash
   streamlit run ai_mental_wellbeing_agent.py
   ```


## ⚠️ Aviso Importante

Esta aplicación es una herramienta de apoyo y no reemplaza la atención profesional de salud mental. Si estás experimentando pensamientos de autolesión o una crisis grave:

- Llama a la Línea Nacional de Crisis: 988
- Llama a los Servicios de Emergencia: 911
- Busca ayuda profesional inmediata

