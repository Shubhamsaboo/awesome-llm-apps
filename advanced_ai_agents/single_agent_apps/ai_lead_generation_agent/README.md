## 🎯 Agente de Generación de Leads de IA - Impulsado por el Endpoint de Extracción de Firecrawl

El Agente de Generación de Leads de IA automatiza el proceso de encontrar y calificar leads potenciales de Quora. Utiliza la búsqueda de Firecrawl y el nuevo endpoint de Extracción para identificar perfiles de usuario relevantes, extraer información valiosa y organizarla en un formato estructurado en Google Sheets. Este agente ayuda a los equipos de ventas y marketing a construir eficientemente listas de leads específicos mientras ahorra horas de investigación manual.

### Características
- **Búsqueda Específica**: Utiliza el endpoint de búsqueda de Firecrawl para encontrar URL de Quora relevantes basadas en tus criterios de búsqueda
- **Extracción Inteligente**: Aprovecha el nuevo endpoint de Extracción de Firecrawl para obtener información de usuario de los perfiles de Quora
- **Procesamiento Automatizado**: Formatea la información de usuario extraída en un formato limpio y estructurado
- **Integración con Google Sheets**: Crea y rellena automáticamente Google Sheets con información de leads
- **Criterios Personalizables**: Te permite definir parámetros de búsqueda específicos para encontrar tus leads ideales para tu nicho

### Cómo Empezar
1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_lead_generation_agent
   ```
3. **Instala los paquetes requeridos**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Cosa importante que hacer en composio**:
    - en la terminal, ejecuta este comando: `composio add googlesheets`
    - En tu panel de control de composio, crea una nueva integración de Google Sheets y asegúrate de que esté activa en la pestaña de integraciones/conexiones activas

5. **Configura tus claves API**:
   - Obtén tu clave API de Firecrawl desde [el sitio web de Firecrawl](https://www.firecrawl.dev/app/api-keys)
   - Obtén tu clave API de Composio desde [el sitio web de Composio](https://composio.ai)
   - Obtén tu clave API de OpenAI desde [el sitio web de OpenAI](https://platform.openai.com/api-keys)

6. **Ejecuta la aplicación**:
   ```bash
   streamlit run ai_lead_generation_agent.py
   ```

