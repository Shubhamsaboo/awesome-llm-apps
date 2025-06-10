# 👨‍⚖️ Equipo de Agentes Legales de IA

Una aplicación de Streamlit que simula un equipo legal de servicio completo utilizando múltiples agentes de IA para analizar documentos legales y proporcionar información legal completa. Cada agente representa un rol de especialista legal diferente, desde la investigación y el análisis de contratos hasta la planificación estratégica, trabajando juntos para proporcionar un análisis y recomendaciones legales exhaustivos.

## Características

- **Equipo Especializado de Agentes Legales de IA**
  - **Investigador Legal**: Equipado con la herramienta de búsqueda DuckDuckGo para encontrar y citar casos legales y precedentes relevantes. Proporciona resúmenes de investigación detallados con fuentes y referencias a secciones específicas de los documentos cargados.
  
  - **Analista de Contratos**: Se especializa en la revisión exhaustiva de contratos, identificando términos clave, obligaciones y posibles problemas. Hace referencia a cláusulas específicas de los documentos para un análisis detallado.
  
  - **Estratega Legal**: Se centra en el desarrollo de estrategias legales integrales, proporcionando recomendaciones procesables mientras considera tanto los riesgos como las oportunidades.
  
  - **Líder de Equipo**: Coordina el análisis entre los miembros del equipo, asegura respuestas completas, recomendaciones debidamente fundamentadas y referencias a partes específicas del documento. Actúa como coordinador del Equipo de Agentes para los tres agentes.

- **Tipos de Análisis de Documentos**
  - Revisión de Contratos - Realizado por el Analista de Contratos
  - Investigación Legal - Realizado por el Investigador Legal
  - Evaluación de Riesgos - Realizado por el Estratega Legal, Analista de Contratos
  - Verificación de Cumplimiento - Realizado por el Estratega Legal, Investigador Legal, Analista de Contratos
  - Consultas Personalizadas - Realizado por el Equipo de Agentes - Investigador Legal, Estratega Legal, Analista de Contratos

## Cómo Ejecutar

1. **Configurar el Entorno**
   ```bash
   # Clona el repositorio
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team
   
   # Instala las dependencias
   pip install -r requirements.txt
   ```

2. **Configurar Claves API**
   - Obtén la clave API de OpenAI desde [OpenAI Platform](https://platform.openai.com)
   - Obtén la clave API y la URL de Qdrant desde [Qdrant Cloud](https://cloud.qdrant.io)

3. **Ejecutar la Aplicación**
   ```bash
   streamlit run legal_agent_team.py
   ```
4. **Usar la Interfaz**
   - Ingresa las credenciales de la API
   - Sube un documento legal (PDF)
   - Selecciona el tipo de análisis
   - Agrega consultas personalizadas si es necesario
   - Visualiza los resultados del análisis

## Notas

- Solo admite documentos PDF
- Utiliza GPT-4o para el análisis
- Utiliza text-embedding-3-small para las incrustaciones
- Requiere conexión a internet estable
- Se aplican costos de uso de API
