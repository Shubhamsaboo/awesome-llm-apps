## 📰 ➡️ 🎙️ Agente de Blog a Podcast
Esta es una aplicación basada en Streamlit que permite a los usuarios convertir cualquier entrada de blog en un podcast. La aplicación utiliza el modelo GPT-4 de OpenAI para la sumarización, Firecrawl para extraer el contenido del blog y la API de ElevenLabs para generar audio. Los usuarios simplemente ingresan la URL de un blog y la aplicación generará un episodio de podcast basado en el blog.

## Características

- **Extracción de Blogs**: Extrae el contenido completo de cualquier URL de blog pública utilizando la API de Firecrawl.

- **Generación de Resúmenes**: Crea un resumen atractivo y conciso del blog (dentro de 2000 caracteres) utilizando OpenAI GPT-4.

- **Generación de Podcasts**: Convierte el resumen en un podcast de audio utilizando la API de voz de ElevenLabs.

- **Integración de Claves API**: Requiere claves API de OpenAI, Firecrawl y ElevenLabs para funcionar, ingresadas de forma segura a través de la barra lateral.

## Configuración

### Requisitos

1. **Claves API**:
    - **Clave API de OpenAI**: Regístrate en OpenAI para obtener tu clave API.

    - **Clave API de ElevenLabs**: Obtén tu clave API de ElevenLabs en ElevenLabs.

    - **Clave API de Firecrawl**: Obtén tu clave API de Firecrawl en Firecrawl.

2. **Python 3.8+**: Asegúrate de tener instalado Python 3.8 o superior.

### Instalación
1. Clona este repositorio:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps
   cd ai_agent_tutorials/ai_blog_to_podcast_agent
   ```

2. Instala los paquetes de Python requeridos:
   ```bash
   pip install -r requirements.txt
   ```
### Ejecutando la Aplicación

1. Inicia la aplicación Streamlit:
   ```bash
   streamlit run blog_to_podcast_agent.py
   ```

2. En la interfaz de la aplicación:
    - Ingresa tus claves API de OpenAI, ElevenLabs y Firecrawl en la barra lateral.

    - Ingresa la URL del blog que deseas convertir.

    - Haz clic en "🎙️ Generar Podcast".

    - Escucha el podcast generado o descárgalo.