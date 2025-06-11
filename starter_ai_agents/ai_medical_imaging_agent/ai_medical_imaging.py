import os
from PIL import Image as PILImage
from agno.agent import Agent
from agno.models.google import Gemini
import streamlit as st
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.media import Image as AgnoImage

if "GOOGLE_API_KEY" not in st.session_state:
    st.session_state.GOOGLE_API_KEY = None

with st.sidebar:
    st.title("ℹ️ Configuración")
    
    if not st.session_state.GOOGLE_API_KEY:
        api_key = st.text_input(
            "Ingresa tu Clave API de Google:",
            type="password"
        )
        st.caption(
            "Obtén tu clave API de [Google AI Studio]"
            "(https://aistudio.google.com/apikey) 🔑"
        )
        if api_key:
            st.session_state.GOOGLE_API_KEY = api_key
            st.success("¡Clave API guardada!")
            st.rerun()
    else:
        st.success("La Clave API está configurada")
        if st.button("🔄 Restablecer Clave API"):
            st.session_state.GOOGLE_API_KEY = None
            st.rerun()
    
    st.info(
        "Esta herramienta proporciona análisis de datos de imágenes médicas impulsado por IA utilizando "
        "visión por computadora avanzada y experiencia radiológica."
    )
    st.warning(
        "⚠AVISO LEGAL: Esta herramienta es solo para fines educativos e informativos. "
        "Todos los análisis deben ser revisados por profesionales de la salud calificados. "
        "No tomes decisiones médicas basándote únicamente en este análisis."
    )

medical_agent = Agent(
    model=Gemini(
        id="gemini-2.0-flash",
        api_key=st.session_state.GOOGLE_API_KEY
    ),
    tools=[DuckDuckGoTools()],
    markdown=True
) if st.session_state.GOOGLE_API_KEY else None

if not medical_agent:
    st.warning("Por favor, configura tu clave API en la barra lateral para continuar")

# Medical Analysis Query
query = """
Eres un experto en imágenes médicas altamente cualificado con amplios conocimientos en radiología y diagnóstico por imagen. Analiza la imagen médica del paciente y estructura tu respuesta de la siguiente manera:

### 1. Tipo de Imagen y Región
- Especifica la modalidad de imagen (Rayos X/IRM/TC/Ultrasonido/etc.)
- Identifica la región anatómica y el posicionamiento del paciente
- Comenta sobre la calidad de la imagen y la adecuación técnica

### 2. Hallazgos Clave
- Enumera las observaciones primarias sistemáticamente
- Observa cualquier anormalidad en las imágenes del paciente con descripciones precisas
- Incluye mediciones y densidades cuando sea relevante
- Describe la ubicación, tamaño, forma y características
- Califica la gravedad: Normal/Leve/Moderada/Severa

### 3. Evaluación Diagnóstica
- Proporciona el diagnóstico primario con nivel de confianza
- Enumera los diagnósticos diferenciales en orden de probabilidad
- Respalda cada diagnóstico con evidencia observada de las imágenes del paciente
- Observa cualquier hallazgo crítico o urgente

### 4. Explicación Amigable para el Paciente
- Explica los hallazgos en un lenguaje simple y claro que el paciente pueda entender
- Evita la jerga médica o proporciona definiciones claras
- Incluye analogías visuales si es útil
- Aborda las preocupaciones comunes de los pacientes relacionadas con estos hallazgos

### 5. Contexto de Investigación
IMPORTANTE: Utiliza la herramienta de búsqueda DuckDuckGo para:
- Encontrar literatura médica reciente sobre casos similares
- Buscar protocolos de tratamiento estándar
- Proporcionar una lista de enlaces médicos relevantes de ellos también
- Investigar cualquier avance tecnológico relevante
- Incluye 2-3 referencias clave para respaldar tu análisis

Formatea tu respuesta usando encabezados markdown claros y viñetas. Sé conciso pero exhaustivo.
"""

st.title("🏥 Agente de Diagnóstico de Imágenes Médicas")
st.write("Sube una imagen médica para un análisis profesional")

# Create containers for better organization
upload_container = st.container()
image_container = st.container()
analysis_container = st.container()

with upload_container:
    uploaded_file = st.file_uploader(
        "Subir Imagen Médica",
        type=["jpg", "jpeg", "png", "dicom"],
        help="Formatos soportados: JPG, JPEG, PNG, DICOM"
    )

if uploaded_file is not None:
    with image_container:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            image = PILImage.open(uploaded_file)
            width, height = image.size
            aspect_ratio = width / height
            new_width = 500
            new_height = int(new_width / aspect_ratio)
            resized_image = image.resize((new_width, new_height))
            
            st.image(
                resized_image,
                caption="Imagen Médica Subida",
                use_container_width=True
            )
            
            analyze_button = st.button(
                "🔍 Analizar Imagen",
                type="primary",
                use_container_width=True
            )
    
    with analysis_container:
        if analyze_button:
            with st.spinner("🔄 Analizando imagen... Por favor espera."):
                try:
                    temp_path = "temp_resized_image.png"
                    resized_image.save(temp_path)
                    
                    # Create AgnoImage object
                    agno_image = AgnoImage(filepath=temp_path)  # Adjust if constructor differs
                    
                    # Run analysis
                    response = medical_agent.run(query, images=[agno_image])
                    st.markdown("### 📋 Resultados del Análisis")
                    st.markdown("---")
                    st.markdown(response.content)
                    st.markdown("---")
                    st.caption(
                        "Nota: Este análisis es generado por IA y debe ser revisado por "
                        "un profesional de la salud calificado."
                    )
                except Exception as e:
                    st.error(f"Error en el análisis: {e}")
else:
    st.info("👆 Por favor, sube una imagen médica para comenzar el análisis")
