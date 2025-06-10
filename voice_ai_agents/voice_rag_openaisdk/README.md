## 🎙️ RAG por Voz con SDK de OpenAI

Este script demuestra cómo construir un sistema de Generación Aumentada por Recuperación (RAG) habilitado para voz utilizando el SDK de OpenAI y Streamlit. La aplicación permite a los usuarios cargar documentos PDF, hacer preguntas y recibir respuestas tanto de texto como de voz utilizando las capacidades de conversión de texto a voz de OpenAI.

### Características

- Crea un sistema RAG habilitado para voz utilizando el SDK de OpenAI
- Admite el procesamiento y la fragmentación de documentos PDF
- Utiliza Qdrant como base de datos vectorial para una búsqueda eficiente por similitud
- Implementa la conversión de texto a voz en tiempo real con múltiples opciones de voz
- Proporciona una interfaz de Streamlit fácil de usar
- Permite descargar las respuestas de audio generadas
- Admite la carga y el seguimiento de múltiples documentos

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/voice_rag_openaisdk
```

2. Instala las dependencias requeridas:
```bash
pip install -r requirements.txt
```

3. Configura tus claves API:
- Obtén tu [clave API de OpenAI](https://platform.openai.com/)
- Configura una cuenta en [Qdrant Cloud](https://cloud.qdrant.io/) y obtén tu clave API y URL
- Crea un archivo `.env` con tus credenciales:
```bash
OPENAI_API_KEY='your-openai-api-key'
QDRANT_URL='your-qdrant-url'
QDRANT_API_KEY='your-qdrant-api-key'
```

4. Ejecuta la aplicación RAG por Voz:
```bash
streamlit run rag_voice.py
```

5. Abre tu navegador web y navega a la URL proporcionada en la salida de la consola para interactuar con el sistema RAG por Voz.

### ¿Cómo Funciona?

1. **Procesamiento de Documentos:**
   - Sube documentos PDF a través de la interfaz de Streamlit
   - Los documentos se dividen en fragmentos utilizando RecursiveCharacterTextSplitter de LangChain
   - Cada fragmento se incrusta utilizando FastEmbed y se almacena en Qdrant

2. **Procesamiento de Consultas:**
   - Las preguntas de los usuarios se convierten en incrustaciones
   - Se recuperan documentos similares de Qdrant
   - Un agente de procesamiento genera una respuesta clara y amigable para la voz
   - Un agente TTS optimiza la respuesta para la síntesis de voz

3. **Generación de Voz:**
   - Las respuestas de texto se convierten en voz utilizando TTS de OpenAI
   - Los usuarios pueden elegir entre múltiples opciones de voz
   - El audio se puede reproducir directamente o descargar como MP3

4. **Características:**
   - Transmisión de audio en tiempo real
   - Múltiples opciones de personalidad de voz
   - Seguimiento de la fuente del documento
   - Capacidad de descarga para respuestas de audio
   - Seguimiento del progreso para el procesamiento de documentos