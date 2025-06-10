# 🔍 Agente de Investigación Profunda de Dominios de IA

Un agente de investigación de IA avanzado construido utilizando el framework Agno Agent, el modelo Qwen de Together AI y herramientas de Composio. Este agente ayuda a los usuarios a realizar investigaciones exhaustivas sobre cualquier tema generando preguntas de investigación, encontrando respuestas a través de múltiples motores de búsqueda y compilando informes profesionales con integración de Google Docs.

## Características

- 🧠 **Generación Inteligente de Preguntas**:

  - Genera automáticamente 5 preguntas de investigación específicas sobre tu tema
  - Adapta las preguntas a tu dominio especificado
  - Se enfoca en crear preguntas de sí/no para resultados de investigación claros
- 🔎 **Investigación Multifacética**:

  - Utiliza Tavily Search para resultados web completos
  - Aprovecha Perplexity AI para un análisis más profundo
  - Combina múltiples fuentes para una investigación exhaustiva
- 📊 **Generación de Informes Profesionales**:

  - Compila los hallazgos de la investigación en un informe estilo McKinsey
  - Estructura el contenido con resumen ejecutivo, análisis y conclusión
  - Crea un Google Doc con el informe completo
- 🖥️ **Interfaz Fácil de Usar**:

  - Interfaz de usuario de Streamlit limpia con flujo de trabajo intuitivo
  - Seguimiento del progreso en tiempo real
  - Secciones expandibles para ver resultados detallados

## Cómo Ejecutar

1. **Configurar el Entorno**

   ```bash
   # Clona el repositorio
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_domain_deep_research_agent

   # Instala las dependencias
   pip install -r requirements.txt

   composio add googledocs
   composio add perplexityai
   ```
2. **Configurar Claves API**

   - Obtén la clave API de Together AI desde [Together AI](https://together.ai)
   - Obtén la clave API de Composio desde [Composio](https://composio.ai)
   - Agrégalas a un archivo `.env` o ingrésalas en la barra lateral de la aplicación
3. **Ejecutar la Aplicación**

   ```bash
   streamlit run ai_domain_deep_research_agent.py
   ```

## Uso

1. Lanza la aplicación utilizando el comando anterior
2. Ingresa tus claves API de Together AI y Composio en la barra lateral
3. Ingresa tu tema de investigación y dominio en la interfaz principal
4. Haz clic en "Generar Preguntas de Investigación" para crear preguntas específicas
5. Revisa las preguntas y haz clic en "Iniciar Investigación" para comenzar el proceso de investigación
6. Una vez completada la investigación, haz clic en "Compilar Informe Final" para generar un informe profesional
7. Visualiza el informe en la aplicación y accede a él en Google Docs

## Detalles Técnicos

- **Framework Agno**: Utilizado para crear y orquestar agentes de IA
- **Together AI**: Proporciona el modelo Qwen 3 235B para procesamiento avanzado del lenguaje
- **Herramientas Composio**: Integra motores de búsqueda y funcionalidad de Google Docs
- **Streamlit**: Impulsa la interfaz de usuario con elementos interactivos

## Casos de Uso de Ejemplo

- **Investigación Académica**: Reúne rápidamente información sobre temas académicos en diversas disciplinas
- **Análisis de Mercado**: Investiga tendencias de mercado, competidores y desarrollos de la industria
- **Investigación de Políticas**: Analiza implicaciones de políticas y contexto histórico
- **Evaluación de Tecnología**: Investiga tecnologías emergentes y su impacto potencial

## Dependencias

- agno
- composio_agno
- streamlit
- python-dotenv

## Licencia

Este proyecto es parte de la colección awesome-llm-apps y está disponible bajo la Licencia MIT.
