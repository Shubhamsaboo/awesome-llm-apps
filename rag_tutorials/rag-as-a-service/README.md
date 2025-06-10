## 🖇️ RAG como Servicio con Claude 3.5 Sonnet
Construye e implementa un servicio de Generación Aumentada por Recuperación (RAG) listo para producción utilizando Claude 3.5 Sonnet y Ragie.ai. Esta implementación te permite crear un sistema de consulta de documentos con una interfaz de Streamlit fácil de usar en menos de 50 líneas de código Python.

### Características
- Canalización RAG lista para producción
- Integración con Claude 3.5 Sonnet para la generación de respuestas
- Carga de documentos desde URL
- Consulta de documentos en tiempo real
- Soporte para modos de procesamiento de documentos rápido y preciso

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/rag-as-a-service
```

2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```

3. Obtén tu Clave API de Anthropic y Ragie

- Regístrate para obtener una [cuenta de Anthropic](https://console.anthropic.com/) y obtén tu clave API
- Regístrate para obtener una [cuenta de Ragie](https://www.ragie.ai/) y obtén tu clave API

4. Ejecuta la aplicación Streamlit
```bash
streamlit run rag_app.py
```