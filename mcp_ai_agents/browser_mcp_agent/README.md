# 🌐 Agente MCP para Navegador

![Area](https://github.com/user-attachments/assets/285a6a02-c1a9-4581-b32b-b244f665f648)

Una aplicación de Streamlit que te permite navegar e interactuar con sitios web utilizando comandos de lenguaje natural a través del Model Context Protocol (MCP) y [MCP-Agent](https://github.com/lastmile-ai/mcp-agent) con integración de Puppeteer.

## Características

- **Interfaz de Lenguaje Natural**: Controla un navegador con comandos simples en español
- **Navegación Completa del Navegador**: Visita sitios web y navega por las páginas
- **Elementos Interactivos**: Haz clic en botones, rellena formularios y desplázate por el contenido
- **Retroalimentación Visual**: Toma capturas de pantalla de elementos de la página web
- **Extracción de Información**: Extrae y resume contenido de páginas web
- **Tareas de Múltiples Pasos**: Completa secuencias de navegación complejas a través de la conversación

## Configuración

### Requisitos

- Python 3.8+
- Node.js y npm (para Puppeteer)
  - ¡Este es un requisito crítico! La aplicación utiliza Puppeteer para controlar un navegador sin cabeza (headless)
  - Descarga e instala desde [nodejs.org](https://nodejs.org/)
- Clave API de OpenAI o Anthropic

### Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd mcp_ai_agents/browser_mcp_agent
   ```

2. Instala los paquetes de Python requeridos:
   ```bash
   pip install -r requirements.txt
   ```

3. Verifica que Node.js y npm estén instalados:
   ```bash
   node --version
   npm --version
   ```
   Ambos comandos deberían devolver números de versión. Si no es así, instala Node.js.

4. Configura tus claves API:
   - Establece la Clave API de OpenAI como una variable de entorno:
     ```bash
     export OPENAI_API_KEY=your-openai-api-key
     ```


### Ejecutando la Aplicación

1. Inicia la aplicación Streamlit:
   ```bash
   streamlit run main.py
   ```

2. En la interfaz de la aplicación:
   - Ingresa tu comando de navegación
   - Haz clic en "Ejecutar Comando"
   - Visualiza los resultados y las capturas de pantalla

### Comandos de Ejemplo

#### Navegación Básica
- "Ir a www.lastmileai.dev"
- "Volver a la página anterior"

#### Interacción
- "Hacer clic en el botón de inicio de sesión"
- "Desplazarse hacia abajo para ver más contenido"

#### Extracción de Contenido
- "Resumir el contenido principal de esta página"
- "Extraer los elementos del menú de navegación"
- "Tomar una captura de pantalla de la sección principal"

#### Tareas de Múltiples Pasos
- "Ir al blog, encontrar el artículo más reciente y resumir sus puntos clave"

## Arquitectura

La aplicación utiliza:
- Streamlit para la interfaz de usuario
- MCP (Model Context Protocol) para conectar el LLM con herramientas
- Puppeteer para la automatización del navegador
- [MCP-Agent](https://github.com/lastmile-ai/mcp-agent/) para el Framework Agéntico
- Modelos de OpenAI para interpretar comandos y generar respuestas
