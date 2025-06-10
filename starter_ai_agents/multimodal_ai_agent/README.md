## 🧬 Agente de IA Multimodal

Una aplicación de Streamlit que combina capacidades de análisis de video y búsqueda web utilizando el modelo Gemini 2.0 de Google. Este agente puede analizar videos subidos y responder preguntas combinando la comprensión visual con la búsqueda web.

### Características

- Análisis de video utilizando Gemini 2.0 Flash
- Integración de investigación web a través de DuckDuckGo
- Soporte para múltiples formatos de video (MP4, MOV, AVI)
- Procesamiento de video en tiempo real
- Análisis visual y textual combinado

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd ai_agent_tutorials/multimodal_ai_agent
```
2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```
3. Obtén tu Clave API de Google Gemini

- Regístrate para obtener una [cuenta de Google AI Studio](https://aistudio.google.com/apikey) y obtén tu clave API.

4. Configura tu Clave API de Gemini como variable de entorno

```bash
GOOGLE_API_KEY=your_api_key_here
```

5. Ejecuta la Aplicación Streamlit
```bash
streamlit run multimodal_agent.py
```
