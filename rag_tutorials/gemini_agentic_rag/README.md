# 🤔 RAG Agéntico con Gemini Flash Thinking

Un sistema RAG Agéntico construido con el nuevo modelo Gemini 2.0 Flash Thinking y gemini-exp-1206, Qdrant para almacenamiento de vectores y Agno (anteriormente phidata) para la orquestación de agentes. Esta aplicación cuenta con reescritura inteligente de consultas, procesamiento de documentos y capacidades de respaldo de búsqueda web para proporcionar respuestas completas impulsadas por IA.

## Características

- **Procesamiento de Documentos**
  - Carga y procesamiento de documentos PDF
  - Extracción de contenido de páginas web
  - Fragmentación y embedding automático de texto
  - Almacenamiento de vectores en la nube Qdrant

- **Consultas Inteligentes**
  - Reescritura de consultas para una mejor recuperación
  - Recuperación de documentos basada en RAG
  - Búsqueda de similitud con filtrado de umbral
  - Respaldo automático a búsqueda web
  - Atribución de fuentes para las respuestas

- **Capacidades Avanzadas**
  - Integración de búsqueda web Exa AI
  - Filtrado de dominio personalizado para búsqueda web
  - Generación de respuestas conscientes del contexto
  - Gestión del historial de chat
  - Agente de reformulación de consultas

- **Características Específicas del Modelo**
  - Gemini Thinking 2.0 Flash para chat y razonamiento
  - Modelo Gemini Embedding para embeddings vectoriales
  - Framework Agno Agent para orquestación
  - Interfaz interactiva basada en Streamlit

## Requisitos Previos

### 1. Clave API de Google
1. Ve a [Google AI Studio](https://aistudio.google.com/apikey)
2. Regístrate o inicia sesión en tu cuenta
3. Crea una nueva clave API

### 2. Configuración de Qdrant Cloud
1. Visita [Qdrant Cloud](https://cloud.qdrant.io/)
2. Crea una cuenta o inicia sesión
3. Crea un nuevo clúster
4. Obtén tus credenciales:
   - Clave API de Qdrant: Se encuentra en la sección de Claves API
   - URL de Qdrant: La URL de tu clúster (formato: `https://xxx-xxx.cloud.qdrant.io`)

### 3. Clave API de Exa AI (Opcional)
1. Visita [Exa AI](https://exa.ai)
2. Regístrate para obtener una cuenta
3. Genera una clave API para capacidades de búsqueda web

## Cómo Ejecutar

1. Clona el repositorio:
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd rag_tutorials/gemini_agentic_rag
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta la aplicación:
```bash
streamlit run agentic_rag_gemini.py
```

## Uso

1. Configura las claves API en la barra lateral:
   - Ingresa tu clave API de Google
   - Agrega las credenciales de Qdrant
   - (Opcional) Agrega la clave de Exa AI para búsqueda web

2. Sube documentos:
   - Usa el cargador de archivos para PDF
   - Ingresa URL para contenido web

3. Haz preguntas:
   - Escribe tu consulta en la interfaz de chat
   - Visualiza consultas reescritas y fuentes
   - Consulta los resultados de búsqueda web cuando sea relevante

4. Gestiona tu sesión:
   - Borra el historial de chat según sea necesario
   - Configura dominios de búsqueda web
   - Supervisa los documentos procesados
