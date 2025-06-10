## 💻 Agente de IA para Web Scraping
Esta aplicación de Streamlit te permite extraer datos de un sitio web utilizando la API de OpenAI y la biblioteca scrapegraphai. Simplemente proporciona tu clave API de OpenAI, ingresa la URL del sitio web que deseas extraer y especifica qué deseas que el agente de IA extraiga del sitio web.

### Características
- Extrae datos de cualquier sitio web proporcionando la URL
- Utiliza los LLM de OpenAI (GPT-3.5-turbo o GPT-4) para una extracción inteligente
- Personaliza la tarea de extracción especificando qué deseas que el agente de IA extraiga

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_tools_frameworks/web_scrapping_ai_agent
```
2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```
3. Obtén tu Clave API de OpenAI

- Regístrate para obtener una [cuenta de OpenAI](https://platform.openai.com/) (o el proveedor de LLM de tu elección) y obtén tu clave API.

4. Ejecuta la Aplicación Streamlit
```bash
streamlit run ai_scrapper.py
```

### ¿Cómo Funciona?

- La aplicación te solicita que ingreses tu clave API de OpenAI, que se utiliza para autenticar y acceder a los modelos de lenguaje de OpenAI.
- Puedes seleccionar el modelo de lenguaje deseado (GPT-3.5-turbo o GPT-4) para la tarea de extracción.
- Ingresa la URL del sitio web que deseas extraer en el campo de entrada de texto proporcionado.
- Especifica qué deseas que el agente de IA extraiga del sitio web ingresando una indicación de usuario.
- La aplicación crea un objeto SmartScraperGraph utilizando la URL proporcionada, la indicación del usuario y la configuración de OpenAI.
- El objeto SmartScraperGraph extrae datos del sitio web y la información solicitada utilizando el modelo de lenguaje especificado.
- Los resultados extraídos se muestran en la aplicación para que los veas