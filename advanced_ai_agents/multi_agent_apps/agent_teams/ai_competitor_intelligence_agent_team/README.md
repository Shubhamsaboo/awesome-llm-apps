# 🧲 Equipo de Agentes de Inteligencia Competitiva de IA

El Equipo de Agentes de Inteligencia Competitiva de IA es una potente herramienta de análisis de la competencia impulsada por Firecrawl y el framework de Agentes de IA de Agno. Esta aplicación ayuda a las empresas a analizar a sus competidores extrayendo datos estructurados de los sitios web de la competencia y generando información procesable mediante IA.

## Características

- **Sistema Multiagente**
    - **Agente Firecrawl**: Se especializa en rastrear y resumir los sitios web de la competencia
    - **Agente de Análisis**: Genera informes detallados de análisis competitivo
    - **Agente de Comparación**: Crea comparaciones estructuradas entre competidores

- **Descubrimiento de Competidores**:
  - Encuentra empresas similares utilizando la coincidencia de URL con Exa AI
  - Descubre competidores basándose en descripciones de negocios
  - Extrae automáticamente URL de competidores relevantes

- **Análisis Exhaustivo**:
  - Proporciona informes de análisis estructurados con:
    - Brechas y oportunidades de mercado
    - Debilidades de la competencia
    - Características recomendadas
    - Estrategias de precios
    - Oportunidades de crecimiento
    - Recomendaciones procesables

- **Análisis Interactivo**: Los usuarios pueden ingresar la URL o la descripción de su empresa para el análisis

## Requisitos

La aplicación requiere las siguientes bibliotecas de Python:

- `agno`
- `exa-py`
- `streamlit`
- `pandas`
- `firecrawl-py`

También necesitarás claves API para:
- OpenAI
- Firecrawl
- Exa

## Cómo Ejecutar

Sigue estos pasos para configurar y ejecutar la aplicación:

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_competitor_intelligence_agent_team
   ```

2. **Instala las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configura tus claves API**:
    - Obtén una clave API de OpenAI desde: https://platform.openai.com/api-keys
    - Obtén una clave API de Firecrawl desde: [Sitio web de Firecrawl](https://www.firecrawl.dev/app/api-keys)
    - Obtén una clave API de Exa desde: [Sitio web de Exa](https://dashboard.exa.ai/api-keys)

4. **Ejecuta la aplicación Streamlit**:
    ```bash
    streamlit run ai_competitor_analyser.py
    ```

## Uso

1. Ingresa tus claves API en la barra lateral
2. Ingresa ya sea:
   - La URL del sitio web de tu empresa
   - Una descripción de tu empresa
3. Haz clic en "Analizar Competidores" para generar:
   - Tabla de comparación de competidores
   - Informe de análisis detallado
   - Recomendaciones estratégicas
