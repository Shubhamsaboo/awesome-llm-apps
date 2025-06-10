## 📨 Chatea con tu Bandeja de Entrada de Gmail

Aplicación LLM con RAG para chatear con Gmail en solo 30 líneas de código Python. La aplicación utiliza Generación Aumentada por Recuperación (RAG) para proporcionar respuestas precisas a preguntas basadas en el contenido de tu Bandeja de Entrada de Gmail.

### Características

- Conéctate a tu Bandeja de Entrada de Gmail
- Haz preguntas sobre el contenido de tus correos electrónicos
- Obtén respuestas precisas utilizando RAG y el LLM seleccionado

### Instalación

1. Clona el repositorio

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_llm_apps/chat_with_X_tutorials/chat_with_gmail
```
2. Instala las dependencias requeridas

```bash
pip install -r requirements.txt
```

3. Configura tu proyecto de Google Cloud y habilita la API de Gmail:

- Ve a la [Google Cloud Console](https://console.cloud.google.com/) y crea un nuevo proyecto.
- Navega a "APIs y servicios > Pantalla de consentimiento de OAuth" y configura la pantalla de consentimiento de OAuth.
- Publica la pantalla de consentimiento de OAuth proporcionando la información necesaria de la aplicación.
- Habilita la API de Gmail y crea credenciales de ID de cliente OAuth.
- Descarga las credenciales en formato JSON y guárdalas como `credentials.json` en tu directorio de trabajo.

4. Obtén tu Clave API de OpenAI

- Regístrate para obtener una [cuenta de OpenAI](https://platform.openai.com/) (o el proveedor de LLM de tu elección) y obtén tu clave API.

4. Ejecuta la Aplicación Streamlit

```bash
streamlit run chat_gmail.py
```


