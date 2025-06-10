# 🎙️ Agente de Voz para Soporte al Cliente

Una aplicación de agente de soporte al cliente impulsada por el SDK de OpenAI que ofrece respuestas por voz a preguntas sobre tu base de conocimientos utilizando las capacidades de GPT-4o y TTS de OpenAI. El sistema rastrea sitios web de documentación con Firecrawl, procesa el contenido en una base de conocimientos consultable con Qdrant y proporciona respuestas tanto de texto como de voz a las consultas de los usuarios.

## Características

- Creación de Base de Conocimientos

  - Rastrea sitios web de documentación utilizando Firecrawl
  - Almacena e indexa contenido utilizando la base de datos vectorial Qdrant
  - Genera incrustaciones para capacidades de búsqueda semántica utilizando FastEmbed
- **Equipo de Agentes de IA**
  - **Procesador de Documentación**: Analiza el contenido de la documentación y genera respuestas claras y concisas a las consultas de los usuarios
  - **Agente TTS**: Convierte las respuestas de texto en voz con sonido natural con ritmo y énfasis apropiados
  - **Personalización de Voz**: Admite múltiples voces TTS de OpenAI:
    - alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse

- **Interfaz Interactiva**
  - Interfaz de usuario de Streamlit limpia con configuración en la barra lateral
  - Búsqueda de documentación y generación de respuestas en tiempo real
  - Reproductor de audio incorporado con capacidad de descarga
  - Indicadores de progreso para la inicialización del sistema y el procesamiento de consultas

## Cómo Ejecutar

1. **Configurar el Entorno**
   ```bash
   # Clona el repositorio
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/ai_agent_tutorials/ai_voice_agent_openaisdk
   
   # Instala las dependencias
   pip install -r requirements.txt
   ```

2. **Configurar Claves API**
   - Obtén la clave API de OpenAI desde [OpenAI Platform](https://platform.openai.com)
   - Obtén la clave API y la URL de Qdrant desde [Qdrant Cloud](https://cloud.qdrant.io)
   - Obtén la clave API de Firecrawl para el rastreo de documentación

3. **Ejecutar la Aplicación**
   ```bash
   streamlit run ai_voice_agent_docs.py
   ```

4. **Usar la Interfaz**
   - Ingresa las credenciales de API en la barra lateral
   - Ingresa la URL de la documentación sobre la que deseas aprender
   - Selecciona tu voz preferida del menú desplegable
   - Haz clic en "Inicializar Sistema" para procesar la documentación
   - Haz preguntas y recibe respuestas tanto de texto como de voz

## Características en Detalle

- **Creación de Base de Conocimientos**
  - Construye una base de conocimientos consultable a partir de tu documentación
  - Conserva la estructura y los metadatos del documento
  - Admite el rastreo de múltiples páginas (limitado a 5 páginas por configuración predeterminada)

- **Búsqueda Vectorial**
  - Utiliza FastEmbed para generar incrustaciones
  - Capacidades de búsqueda semántica para encontrar contenido relevante
  - Recuperación eficiente de documentos utilizando Qdrant

- **Generación de Voz**
  - Conversión de texto a voz de alta calidad utilizando los modelos TTS de OpenAI
  - Múltiples opciones de voz para personalización
  - Patrones de habla natural con ritmo y énfasis adecuados
