# 🥸 Agente Generador de Memes con IA - Uso en Navegador

El Agente Generador de Memes con IA es una potente herramienta de automatización de navegadores que crea memes utilizando agentes de IA. Esta aplicación combina capacidades multi-LLM con interacciones automatizadas del navegador para generar memes basados en indicaciones de texto mediante la manipulación directa de sitios web.

## Características

- **Soporte Multi-LLM**
  - Claude 3.5 Sonnet (Anthropic)
  - GPT-4o (OpenAI)
  - Deepseek v3 (Deepseek)
  - Cambio automático de modelo con validación de clave API

- **Automatización del Navegador**:
  - Interacción directa con plantillas de memes de imgflip.com
  - Búsqueda automatizada de formatos de memes relevantes
  - Inserción dinámica de texto para leyendas superiores/inferiores
  - Extracción de enlaces de imágenes de memes generados

- **Flujo de Trabajo de Generación Inteligente**:
  - Extracción de verbos de acción de las indicaciones
  - Coincidencia de plantillas metafóricas
  - Validación de calidad en varios pasos
  - Mecanismo de reintento automático para generaciones fallidas

- **Interfaz Fácil de Usar**:
  - Barra lateral de configuración del modelo
  - Gestión de claves API
  - Vista previa directa de memes con enlaces clicables
  - Manejo receptivo de errores


Claves API requeridas:
- **Anthropic** (para Claude)
- **Deepseek** 
- **OpenAI** (para GPT-4o)

## Cómo Ejecutar

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_meme_generator_browseruse
   ```
2. **Instala las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
3. **Ejecuta la aplicación Streamlit**:
    ```bash
    streamlit run ai_meme_generator.py
    ```