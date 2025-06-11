from agno.agent import Agent
from agno.models.google import Gemini
from agno.media import Image as AgnoImage
from agno.tools.duckduckgo import DuckDuckGoTools
import streamlit as st
from typing import List, Optional
from agno.agent import Agent
from agno.models.google import Gemini
from agno.media import Image as AgnoImage
from agno.tools.duckduckgo import DuckDuckGoTools
import streamlit as st
from typing import List, Optional
import logging
from pathlib import Path
import tempfile
import os

# Configure logging for errors only
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def initialize_agents(api_key: str) -> tuple[Agent, Agent, Agent, Agent]:
    try:
        model = Gemini(id="gemini-2.0-flash-exp", api_key=api_key)
        
        therapist_agent = Agent(
            model=model,
            name="Agente Terapeuta",
            instructions=[
                "Eres un terapeuta empático que:",
                "1. Escucha con empatía y valida los sentimientos",
                "2. Usa humor gentil para aligerar el ambiente",
                "3. Comparte experiencias de ruptura con las que se pueda identificar",
                "4. Ofrece palabras de consuelo y aliento",
                "5. Analiza tanto las entradas de texto como de imagen para el contexto emocional",
                "Sé solidario y comprensivo en tus respuestas"
            ],
            markdown=True
        )

        closure_agent = Agent(
            model=model,
            name="Agente de Cierre",
            instructions=[
                "Eres un especialista en cierre que:",
                "1. Crea mensajes emocionales para sentimientos no enviados",
                "2. Ayuda a expresar emociones crudas y honestas",
                "3. Formatea los mensajes claramente con encabezados",
                "4. Asegura que el tono sea sincero y auténtico",
                "Concéntrate en la liberación emocional y el cierre"
            ],
            markdown=True
        )

        routine_planner_agent = Agent(
            model=model,
            name="Agente Planificador de Rutinas",
            instructions=[
                "Eres un planificador de rutinas de recuperación que:",
                "1. Diseña desafíos de recuperación de 7 días",
                "2. Incluye actividades divertidas y tareas de autocuidado",
                "3. Sugiere estrategias de desintoxicación de redes sociales",
                "4. Crea listas de reproducción empoderadoras",
                "Concéntrate en pasos prácticos de recuperación"
            ],
            markdown=True
        )

        brutal_honesty_agent = Agent(
            model=model,
            name="Agente de Honestidad Brutal",
            tools=[DuckDuckGoTools()],
            instructions=[
                "Eres un especialista en retroalimentación directa que:",
                "1. Da retroalimentación cruda y objetiva sobre las rupturas",
                "2. Explica claramente los fracasos en las relaciones",
                "3. Usa un lenguaje directo y factual",
                "4. Proporciona razones para seguir adelante",
                "Concéntrate en perspectivas honestas sin endulzar la realidad"
            ],
            markdown=True
        )
        
        return therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent
    except Exception as e:
        st.error(f"Error al inicializar los agentes: {str(e)}")
        return None, None, None, None

# Set page config and UI elements
st.set_page_config(
    page_title="💔 Escuadrón de Recuperación de Rupturas",
    page_icon="💔",
    layout="wide"
)



# Sidebar for API key input
with st.sidebar:
    st.header("🔑 Configuración de API")

    if "api_key_input" not in st.session_state:
        st.session_state.api_key_input = ""
        
    api_key = st.text_input(
        "Ingresa tu Clave API de Gemini",
        value=st.session_state.api_key_input,
        type="password",
        help="Obtén tu clave API de Google AI Studio",
        key="api_key_widget"  
    )

    if api_key != st.session_state.api_key_input:
        st.session_state.api_key_input = api_key
    
    if api_key:
        st.success("¡Clave API proporcionada! ✅")
    else:
        st.warning("Por favor, ingresa tu clave API para continuar")
        st.markdown("""
        Para obtener tu clave API:
        1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Habilita la API de Lenguaje Generativo en tu [Google Cloud Console](https://console.developers.google.com/apis/api/generativelanguage.googleapis.com)
        """)

# Main content
st.title("💔 Escuadrón de Recuperación de Rupturas")
st.markdown("""
    ### ¡Tu equipo de recuperación de rupturas impulsado por IA está aquí para ayudarte!
    Comparte tus sentimientos y capturas de pantalla de chat, y te ayudaremos a superar este momento difícil.
""")

# Input section
col1, col2 = st.columns(2)

with col1:
    st.subheader("Comparte Tus Sentimientos")
    user_input = st.text_area(
        "¿Cómo te sientes? ¿Qué pasó?",
        height=150,
        placeholder="Cuéntanos tu historia..."
    )
    
with col2:
    st.subheader("Sube Capturas de Pantalla del Chat")
    uploaded_files = st.file_uploader(
        "Sube capturas de pantalla de tus chats (opcional)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="screenshots"
    )
    
    if uploaded_files:
        for file in uploaded_files:
            st.image(file, caption=file.name, use_container_width=True)

# Process button and API key check
if st.button("Obtener Plan de Recuperación 💝", type="primary"):
    if not st.session_state.api_key_input:
        st.warning("¡Por favor, ingresa primero tu clave API en la barra lateral!")
    else:
        therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent = initialize_agents(st.session_state.api_key_input)
        
        if all([therapist_agent, closure_agent, routine_planner_agent, brutal_honesty_agent]):
            if user_input or uploaded_files:
                try:
                    st.header("Tu Plan de Recuperación Personalizado")
                    
                    def process_images(files):
                        processed_images = []
                        for file in files:
                            try:
                                temp_dir = tempfile.gettempdir()
                                temp_path = os.path.join(temp_dir, f"temp_{file.name}")
                                
                                with open(temp_path, "wb") as f:
                                    f.write(file.getvalue())
                                
                                agno_image = AgnoImage(filepath=Path(temp_path))
                                processed_images.append(agno_image)
                                
                            except Exception as e:
                                logger.error(f"Error al procesar la imagen {file.name}: {str(e)}")
                                continue
                        return processed_images
                    
                    all_images = process_images(uploaded_files) if uploaded_files else []
                    
                    # Therapist Analysis
                    with st.spinner("🤗 Obteniendo apoyo empático..."):
                        therapist_prompt = f"""
                        Analiza el estado emocional y proporciona apoyo empático basado en:
                        Mensaje del usuario: {user_input}
                        
                        Por favor, proporciona una respuesta compasiva con:
                        1. Validación de los sentimientos
                        2. Palabras gentiles de consuelo
                        3. Experiencias con las que se pueda identificar
                        4. Palabras de aliento
                        """
                        
                        response = therapist_agent.run(
                            message=therapist_prompt,
                            images=all_images
                        )
                        
                        st.subheader("🤗 Apoyo Emocional")
                        st.markdown(response.content)
                    
                    # Closure Messages
                    with st.spinner("✍️ Creando mensajes de cierre..."):
                        closure_prompt = f"""
                        Ayuda a crear un cierre emocional basado en:
                        Sentimientos del usuario: {user_input}
                        
                        Por favor, proporciona:
                        1. Plantilla para mensajes no enviados
                        2. Ejercicios de liberación emocional
                        3. Rituales de cierre
                        4. Estrategias para seguir adelante
                        """
                        
                        response = closure_agent.run(
                            message=closure_prompt,
                            images=all_images
                        )
                        
                        st.subheader("✍️ Encontrando el Cierre")
                        st.markdown(response.content)
                    
                    # Recovery Plan
                    with st.spinner("📅 Creando tu plan de recuperación..."):
                        routine_prompt = f"""
                        Diseña un plan de recuperación de 7 días basado en:
                        Estado actual: {user_input}
                        
                        Incluye:
                        1. Actividades y desafíos diarios
                        2. Rutinas de autocuidado
                        3. Pautas para redes sociales
                        4. Sugerencias de música para levantar el ánimo
                        """
                        
                        response = routine_planner_agent.run(
                            message=routine_prompt,
                            images=all_images
                        )
                        
                        st.subheader("📅 Tu Plan de Recuperación")
                        st.markdown(response.content)
                    
                    # Honest Feedback
                    with st.spinner("💪 Obteniendo una perspectiva honesta..."):
                        honesty_prompt = f"""
                        Proporciona retroalimentación honesta y constructiva sobre:
                        Situación: {user_input}
                        
                        Incluye:
                        1. Análisis objetivo
                        2. Oportunidades de crecimiento
                        3. Perspectiva futura
                        4. Pasos procesables
                        """
                        
                        response = brutal_honesty_agent.run(
                            message=honesty_prompt,
                            images=all_images
                        )
                        
                        st.subheader("💪 Perspectiva Honesta")
                        st.markdown(response.content)
                            
                except Exception as e:
                    logger.error(f"Error durante el análisis: {str(e)}")
                    st.error("Ocurrió un error durante el análisis. Por favor, revisa los registros para más detalles.")
            else:
                st.warning("Por favor, comparte tus sentimientos o sube capturas de pantalla para obtener ayuda.")
        else:
            st.error("Falló la inicialización de los agentes. Por favor, verifica tu clave API.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Hecho con ❤️ por el Escuadrón de Recuperación de Rupturas</p>
        <p>Comparte tu viaje de recuperación con #EscuadronRecuperacionRupturas</p>
    </div>
""", unsafe_allow_html=True)