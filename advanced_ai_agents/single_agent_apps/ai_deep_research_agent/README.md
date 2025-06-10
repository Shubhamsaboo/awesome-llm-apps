# Agente de Investigación Profunda con OpenAI Agents SDK y Firecrawl

Un potente asistente de investigación que aprovecha el SDK de Agentes de OpenAI y las capacidades de investigación profunda de Firecrawl para realizar investigaciones web exhaustivas sobre cualquier tema y cualquier pregunta.

## Características

- **Investigación Web Profunda**: Busca automáticamente en la web, extrae contenido y sintetiza los hallazgos.
- **Análisis Mejorado**: Utiliza el SDK de Agentes de OpenAI para desarrollar los hallazgos de la investigación con contexto e información adicionales.
- **Interfaz de Usuario Interactiva**: Interfaz de Streamlit limpia para una fácil interacción.
- **Informes Descargables**: Exporta los hallazgos de la investigación como archivos markdown.

## Cómo Funciona

1. **Fase de Entrada**: El usuario proporciona un tema de investigación y credenciales de API.
2. **Fase de Investigación**: La herramienta utiliza Firecrawl para buscar en la web y extraer información relevante.
3. **Fase de Análisis**: Se genera un informe de investigación inicial basado en los hallazgos.
4. **Fase de Mejora**: Un segundo agente desarrolla el informe inicial, agregando profundidad y contexto.
5. **Fase de Salida**: El informe mejorado se presenta al usuario y está disponible para descargar.

## Requisitos

- Python 3.8+
- Clave API de OpenAI
- Clave API de Firecrawl
- Paquetes de Python requeridos (ver `requirements.txt`)

## Instalación

1. Clona este repositorio:
   ```bash
   git clone  https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_deep_research_agent
   ```

2. Instala los paquetes requeridos:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Ejecuta la aplicación Streamlit:
   ```bash
   streamlit run deep_research_openai.py
   ```

2. Ingresa tus claves API en la barra lateral:
   - Clave API de OpenAI
   - Clave API de Firecrawl

3. Ingresa tu tema de investigación en el campo de entrada principal.

4. Haz clic en "Iniciar Investigación" y espera a que se complete el proceso.

5. Visualiza y descarga tu informe de investigación mejorado.

## Temas de Investigación de Ejemplo

- "Últimos desarrollos en computación cuántica"
- "Impacto del cambio climático en los ecosistemas marinos"
- "Avances en el almacenamiento de energía renovable"
- "Consideraciones éticas en la inteligencia artificial"
- "Tendencias emergentes en tecnologías de trabajo remoto"

## Detalles Técnicos

La aplicación utiliza dos agentes especializados:

1. **Agente de Investigación**: Utiliza el punto final de investigación profunda de Firecrawl para recopilar información completa de múltiples fuentes web.

2. **Agente de Elaboración**: Mejora la investigación inicial agregando explicaciones detalladas, ejemplos, estudios de caso e implicaciones prácticas.

La herramienta de investigación profunda de Firecrawl realiza múltiples iteraciones de búsquedas web, extracción de contenido y análisis para proporcionar una cobertura exhaustiva del tema.

