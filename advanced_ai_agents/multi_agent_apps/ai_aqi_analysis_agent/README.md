# 🌍 Agente de Análisis de AQI

El Agente de Análisis de AQI es una potente herramienta de monitorización de la calidad del aire y recomendación de salud impulsada por Firecrawl y el framework de Agentes de IA de Agno. Esta aplicación ayuda a los usuarios a tomar decisiones informadas sobre actividades al aire libre analizando datos de calidad del aire en tiempo real y proporcionando recomendaciones de salud personalizadas.

## Características

- **Sistema Multiagente**
    - **Analizador de AQI**: Obtiene y procesa datos de calidad del aire en tiempo real
    - **Agente de Recomendación de Salud**: Genera consejos de salud personalizados

- **Métricas de Calidad del Aire**:
  - Índice General de Calidad del Aire (AQI)
  - Material Particulado (PM2.5 y PM10)
  - Niveles de Monóxido de Carbono (CO)
  - Temperatura
  - Humedad
  - Velocidad del Viento

- **Análisis Exhaustivo**:
  - Visualización de datos en tiempo real
  - Evaluación del impacto en la salud
  - Recomendaciones de seguridad para actividades
  - Sugerencias de mejores horarios para actividades al aire libre
  - Correlaciones con las condiciones climáticas

- **Características Interactivas**:
  - Análisis basado en la ubicación
  - Consideraciones sobre condiciones médicas
  - Recomendaciones específicas para actividades
  - Informes descargables
  - Consultas de ejemplo para pruebas rápidas

## Cómo Ejecutar

Sigue estos pasos para configurar y ejecutar la aplicación:

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_aqi_analysis_agent
   ```

2. **Instala las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configura tus claves API**:
    - Obtén una clave API de OpenAI desde: https://platform.openai.com/api-keys
    - Obtén una clave API de Firecrawl desde: [Sitio web de Firecrawl](https://www.firecrawl.dev/app/api-keys)

4. **Ejecuta la aplicación Gradio**:
    ```bash
    python ai_aqi_analysis_agent.py
    ```

5. **Accede a la Interfaz Web**:
    - La terminal mostrará dos URLs:
      - URL Local: `http://127.0.0.1:7860` (para acceso local)
      - URL Pública: `https://xxx-xxx-xxx.gradio.live` (para acceso público temporal)
    - Haz clic en cualquiera de las URL para abrir la interfaz web en tu navegador

## Uso

1. Ingresa tus claves API en la sección de Configuración de API
2. Ingresa los detalles de la ubicación:
   - Nombre de la ciudad
   - Estado (opcional para Territorios de la Unión/ciudades de EE. UU.)
   - País
3. Proporciona información personal:
   - Condiciones médicas (opcional)
   - Actividad al aire libre planificada
4. Haz clic en "Analizar y Obtener Recomendaciones" para recibir:
   - Datos actuales de calidad del aire
   - Análisis del impacto en la salud
   - Recomendaciones de seguridad para actividades
5. Prueba las consultas de ejemplo para pruebas rápidas

## Nota

Los datos de calidad del aire se obtienen utilizando las capacidades de web scraping de Firecrawl. Debido al almacenamiento en caché y la limitación de velocidad, es posible que los datos no siempre coincidan con los valores en tiempo real del sitio web. Para obtener los datos en tiempo real más precisos, considera consultar directamente el sitio web de origen.
