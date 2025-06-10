# 🔥 Información de Startups con IA y Agente Firecrawl FIRE-1

Una herramienta avanzada de extracción y análisis web construida utilizando el agente FIRE-1 de Firecrawl + el endpoint extract v1 y el framework Agno Agent para obtener detalles de una nueva startup ¡al instante! Esta aplicación extrae automáticamente datos estructurados de los sitios web de startups y proporciona análisis de negocios impulsados por IA, facilitando la recopilación de información sobre empresas sin investigación manual.

## Características

- 🌐 **Extracción Web Inteligente**:

  - Extrae datos estructurados de cualquier sitio web de empresa
  - Identifica automáticamente la información de la empresa, la misión y las características del producto
  - Procesa múltiples sitios web en secuencia
- 🔍 **Navegación Web Avanzada**:

  - Interactúa con botones, enlaces y elementos dinámicos
  - Maneja la paginación y los procesos de varios pasos
  - Accede a información a través de múltiples páginas
- 🧠 **Análisis de Negocios con IA**:

  - Genera resúmenes perspicaces de los datos de la empresa extraídos
  - Identifica propuestas de valor únicas y oportunidades de mercado
  - Proporciona inteligencia de negocios procesable
- 📊 **Salida de Datos Estructurados**:

  - Organiza la información en un esquema JSON consistente
  - Extrae el nombre de la empresa, descripción, misión y características del producto
  - Estandariza la salida para su posterior procesamiento
- 🎯 **Interfaz de Usuario Interactiva**:

  - Interfaz de Streamlit fácil de usar
  - Procesa múltiples URL en paralelo
  - Presentación clara de los datos extraídos y el análisis

## Cómo Ejecutar

1. **Configurar el Entorno**

   ```bash
   # Clona el repositorio

   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_startup_insight_fire1_agent
   ```

   # Instala las dependencias


   ```
   pip install -r requirements.txt

   ```
2. **Configurar Claves API**

   - Obtén la clave API de Firecrawl desde [Firecrawl](https://firecrawl.dev)
   - Obtén la clave API de OpenAI desde [OpenAI Platform](https://platform.openai.com)
3. **Ejecutar la Aplicación**

   ```bash
   streamlit run ai_startup_insight_fire1_agent.py
   ```

## Uso

1. Lanza la aplicación utilizando el comando anterior
2. Proporciona tus claves API de Firecrawl y OpenAI en la barra lateral
3. Ingresa una o más URL de sitios web de empresas en el área de texto (una por línea)
4. Haz clic en "🚀 Iniciar Análisis" para comenzar el proceso de extracción y análisis
5. Visualiza los datos estructurados y el análisis de IA para cada sitio web en la interfaz con pestañas

## Sitios Web de Ejemplo para Probar

- https://www.spurtest.com
- https://cluely.com
- https://www.harvey.ai

## Tecnologías Utilizadas

- **Firecrawl FIRE-1**: Agente avanzado de extracción web
- **Framework Agno Agent**: Para capacidades de análisis de IA
- **Modelos OpenAI GPT**: Para la generación de información de negocios
- **Streamlit**: Para la interfaz web interactiva

## Requisitos

- Python 3.8+
- Clave API de Firecrawl
- Clave API de OpenAI
- Conexión a internet para la extracción web
