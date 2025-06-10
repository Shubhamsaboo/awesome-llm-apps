## Generador de Música ModelsLab

Esta es una aplicación basada en Streamlit que permite a los usuarios generar música utilizando la API de ModelsLab y el modelo GPT-4 de OpenAI. Los usuarios pueden ingresar una indicación que describa el tipo de música que desean generar, y la aplicación generará una pista de música en formato MP3 basada en la indicación proporcionada.

## Características

- **Generar Música**: Ingresa una indicación detallada para la generación de música (género, instrumentos, estado de ánimo, etc.), y la aplicación generará una pista de música.
- **Salida MP3**: La música generada estará en formato MP3, disponible para escuchar o descargar.
- **Interfaz Fácil de Usar**: Interfaz de usuario de Streamlit simple y limpia para facilitar su uso.
- **Integración de Claves API**: Requiere claves API de OpenAI y ModelsLab para funcionar. Las claves API se ingresan en la barra lateral para la autenticación.

## Configuración

### Requisitos

1. **Claves API**:
   - **Clave API de OpenAI**: Regístrate en [OpenAI](https://platform.openai.com/api-keys) para obtener tu clave API.
   - **Clave API de ModelsLab**: Regístrate en [ModelsLab](https://modelslab.com/dashboard/api-keys) para obtener tu clave API.

2. **Python 3.8+**: Asegúrate de tener instalado Python 3.8 o superior.

### Instalación
1. Clona este repositorio:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps
   cd ai_agent_tutorials/ai_models_lab_music_generator_agent
   ```

2. Instala los paquetes de Python requeridos:
   ```bash
   pip install -r requirements.txt
   ```
### Ejecutando la Aplicación

1. Inicia la aplicación Streamlit:
   ```bash
   streamlit run models_lab_music_generator_agent.py
   ```

2. En la interfaz de la aplicación:
   - Ingresa una indicación para la generación de música
   - Haz clic en "Generar Música"
   - Reproduce la música y descárgala.