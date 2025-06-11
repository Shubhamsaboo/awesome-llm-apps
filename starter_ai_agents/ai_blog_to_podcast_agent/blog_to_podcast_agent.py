import os
from uuid import uuid4
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.eleven_labs import ElevenLabsTools
from agno.tools.firecrawl import FirecrawlTools
from agno.agent import Agent, RunResponse
from agno.utils.audio import write_audio_to_file
from agno.utils.log import logger
import streamlit as st

# Streamlit Page Setup
st.set_page_config(page_title="📰 ➡️ 🎙️ Agente de Blog a Podcast", page_icon="🎙️")
st.title("📰 ➡️ 🎙️ Agente de Blog a Podcast")

# Sidebar: API Keys
st.sidebar.header("🔑 Claves API")

openai_api_key = st.sidebar.text_input("Clave API de OpenAI", type="password")
elevenlabs_api_key = st.sidebar.text_input("Clave API de ElevenLabs", type="password")
firecrawl_api_key = st.sidebar.text_input("Clave API de Firecrawl", type="password")

# Check if all keys are provided
keys_provided = all([openai_api_key, elevenlabs_api_key, firecrawl_api_key])

# Input: Blog URL
url = st.text_input("Ingresa la URL del Blog:", "")

# Button: Generate Podcast
generate_button = st.button("🎙️ Generar Podcast", disabled=not keys_provided)

if not keys_provided:
    st.warning("Por favor, ingresa todas las claves API requeridas para habilitar la generación de podcasts.")

if generate_button:
    if url.strip() == "":
        st.warning("Por favor, ingresa primero la URL de un blog.")
    else:
        # Set API keys as environment variables for Agno and Tools
        os.environ["OPENAI_API_KEY"] = openai_api_key
        os.environ["ELEVENLABS_API_KEY"] = elevenlabs_api_key
        os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key

        with st.spinner("Procesando... Extrayendo blog, resumiendo y generando podcast 🎶"):
            try:
                blog_to_podcast_agent = Agent(
                    name="Agente de Blog a Podcast",
                    agent_id="blog_to_podcast_agent",
                    model=OpenAIChat(id="gpt-4o"),
                    tools=[
                        ElevenLabsTools(
                            voice_id="JBFqnCBsd6RMkjVDRZzb",
                            model_id="eleven_multilingual_v2",
                            target_directory="audio_generations",
                        ),
                        FirecrawlTools(),
                    ],
                    description="Eres un agente de IA que puede generar audio utilizando la API de ElevenLabs.",
                    instructions=[
                        "Cuando el usuario proporcione una URL de blog:",
                        "1. Usa FirecrawlTools para extraer el contenido del blog",
                        "2. Crea un resumen conciso del contenido del blog que NO TENGA MÁS de 2000 caracteres",
                        "3. El resumen debe capturar los puntos principales mientras es atractivo y conversacional",
                        "4. Usa ElevenLabsTools para convertir el resumen en audio",
                        "Asegúrate de que el resumen esté dentro del límite de 2000 caracteres para evitar los límites de la API de ElevenLabs",
                    ],
                    markdown=True,
                    debug_mode=True,
                )

                podcast: RunResponse = blog_to_podcast_agent.run(
                    f"Convertir el contenido del blog a un podcast: {url}"
                )

                save_dir = "audio_generations"
                os.makedirs(save_dir, exist_ok=True)

                if podcast.audio and len(podcast.audio) > 0:
                    filename = f"{save_dir}/podcast_{uuid4()}.wav"
                    write_audio_to_file(
                        audio=podcast.audio[0].base64_audio,
                        filename=filename
                    )

                    st.success("¡Podcast generado exitosamente! 🎧")
                    audio_bytes = open(filename, "rb").read()
                    st.audio(audio_bytes, format="audio/wav")

                    st.download_button(
                        label="Descargar Podcast",
                        data=audio_bytes,
                        file_name="generated_podcast.wav",
                        mime="audio/wav"
                    )
                else:
                    st.error("No se generó audio. Por favor, inténtalo de nuevo.")

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
                logger.error(f"Error en la aplicación Streamlit: {e}")
