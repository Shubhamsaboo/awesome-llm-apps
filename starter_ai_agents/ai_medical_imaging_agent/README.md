# 🩻 Agente de Diagnóstico de Imágenes Médicas

Un Agente de Diagnóstico de Imágenes Médicas construido sobre agno e impulsado por Gemini 2.0 Flash que proporciona análisis asistido por IA de imágenes médicas de diversos escaneos. El agente actúa como un experto en diagnóstico de imágenes médicas para analizar varios tipos de imágenes y videos médicos, proporcionando información y explicaciones diagnósticas detalladas.

## Características

- **Análisis Integral de Imágenes**
  - Identificación del Tipo de Imagen (rayos X, resonancia magnética, tomografía computarizada, ultrasonido)
  - Detección de la Región Anatómica
  - Hallazgos y Observaciones Clave
  - Detección de Posibles Anormalidades
  - Evaluación de la Calidad de la Imagen
  - Investigación y Referencia

## Cómo Ejecutar

1. **Configurar el Entorno**
   ```bash
   # Clona el repositorio
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_medical_imaging_agent

   # Instala las dependencias
   pip install -r requirements.txt
   ```

2. **Configurar Claves API**
   - Obtén la clave API de Google desde [Google AI Studio](https://aistudio.google.com)

3. **Ejecutar la Aplicación**
   ```bash
   streamlit run ai_medical_imaging.py
   ```

## Componentes del Análisis

- **Tipo y Región de la Imagen**
  - Identifica la modalidad de imagen
  - Especifica la región anatómica

- **Hallazgos Clave**
  - Listado sistemático de observaciones
  - Descripciones detalladas de la apariencia
  - Resaltado de anormalidades

- **Evaluación Diagnóstica**
  - Clasificación de posibles diagnósticos
  - Diagnósticos diferenciales
  - Evaluación de la gravedad

- **Explicaciones Amigables para el Paciente**
  - Terminología simplificada
  - Explicaciones detalladas de los primeros principios
  - Puntos de referencia visuales

## Notas

- Utiliza Gemini 2.0 Flash para el análisis
- Requiere conexión a internet estable
- Costos de uso de API gratuitos: ¡1,500 solicitudes gratuitas por día por Google!
- Solo para fines educativos y de desarrollo
- No reemplaza el diagnóstico médico profesional

## Descargo de Responsabilidad

Esta herramienta es solo para fines educativos e informativos. Todos los análisis deben ser revisados por profesionales de la salud calificados. No tomes decisiones médicas basándote únicamente en este análisis.