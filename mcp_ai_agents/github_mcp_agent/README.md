# 🐙 Agente MCP para GitHub

Una aplicación de Streamlit que te permite explorar y analizar repositorios de GitHub utilizando consultas en lenguaje natural a través del Model Context Protocol (MCP).

## Características

- **Interfaz de Lenguaje Natural**: Haz preguntas sobre repositorios en español sencillo
- **Análisis Exhaustivo**: Explora issues, pull requests, actividad del repositorio y estadísticas de código
- **Interfaz de Usuario Interactiva**: Interfaz fácil de usar con consultas de ejemplo y entrada personalizada
- **Integración MCP**: Aprovecha el Model Context Protocol para interactuar con la API de GitHub
- **Resultados en Tiempo Real**: Obtén información inmediata sobre la actividad y salud del repositorio

## Configuración

### Requisitos

- Python 3.8+
- Node.js y npm (para el servidor MCP de GitHub)
  - ¡Este es un requisito crítico! La aplicación utiliza `npx` para ejecutar el servidor MCP de GitHub
  - Descarga e instala desde [nodejs.org](https://nodejs.org/)
- Token de Acceso Personal de GitHub con los permisos apropiados
- Clave API de OpenAI

### Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd mcp-github-agent
   ```

2. Instala los paquetes de Python requeridos:
   ```bash
   pip install -r requirements.txt
   ```

3. Verifica que Node.js y npm estén instalados:
   ```bash
   node --version
   npm --version
   npx --version
   ```
   Todos estos comandos deberían devolver números de versión. Si no es así, instala Node.js.

4. Configura tus claves API:
   - Establece la Clave API de OpenAI como una variable de entorno:
     ```bash
     export OPENAI_API_KEY=your-openai-api-key
     ```
   - El token de GitHub se ingresará directamente en la interfaz de la aplicación

5. Crea un Token de Acceso Personal de GitHub:
   - Visita https://github.com/settings/tokens
   - Crea un nuevo token con los ámbitos `repo` y `user`
   - Guarda el token en un lugar seguro

### Ejecutando la Aplicación

1. Inicia la aplicación Streamlit:
   ```bash
   streamlit run app.py
   ```

2. En la interfaz de la aplicación:
   - Ingresa tu token de GitHub en la barra lateral
   - Especifica un repositorio para analizar
   - Selecciona un tipo de consulta o escribe la tuya propia
   - Haz clic en "Ejecutar Consulta"

### Consultas de Ejemplo

#### Issues
- "Muéstrame issues por etiqueta"
- "¿Qué issues se están discutiendo activamente?"
- "Encuentra issues etiquetados como bugs"

#### Pull Requests
- "¿Qué PRs necesitan revisión?"
- "Muéstrame PRs fusionados recientemente"
- "Encuentra PRs con conflictos"

#### Repositorio
- "Mostrar métricas de salud del repositorio"
- "Mostrar patrones de actividad del repositorio"
- "Analizar tendencias de calidad del código"
