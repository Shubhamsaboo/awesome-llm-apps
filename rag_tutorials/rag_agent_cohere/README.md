# Agente RAG con Cohere ⌘R

Un sistema RAG Agéntico construido con el nuevo modelo Command-r7b-12-2024 de Cohere, Qdrant para almacenamiento de vectores, Langchain para RAG y LangGraph para orquestación. Esta aplicación permite a los usuarios cargar documentos, hacer preguntas sobre ellos y obtener respuestas impulsadas por IA con respaldo a la búsqueda web cuando sea necesario.

## Características

- **Procesamiento de Documentos**
  - Carga y procesamiento de documentos PDF
  - Fragmentación y embedding automático de texto
  - Almacenamiento de vectores en la nube Qdrant

- **Consultas Inteligentes**
  - Recuperación de documentos basada en RAG
  - Búsqueda de similitud con filtrado de umbral
  - Respaldo automático a búsqueda web cuando no se encuentran documentos relevantes
  - Atribución de fuentes para las respuestas

- **Capacidades Avanzadas**
  - Integración de búsqueda web DuckDuckGo
  - Agente LangGraph para investigación web
  - Generación de respuestas conscientes del contexto
  - Resumen de respuestas largas

- **Características Específicas del Modelo**
  - Modelo Command-r7b-12-2024 para Chat y RAG
  - Modelo cohere embed-english-v3.0 para embeddings
  - Función create_react_agent de langgraph
  - Herramienta DuckDuckGoSearchRun para búsqueda web

## Requisitos Previos

### 1. Clave API de Cohere
1. Ve a [Cohere Platform](https://dashboard.cohere.ai/api-keys)
2. Regístrate o inicia sesión en tu cuenta
3. Navega a la sección de Claves API
4. Crea una nueva clave API

### 2. Configuración de Qdrant Cloud
1. Visita [Qdrant Cloud](https://cloud.qdrant.io/)
2. Crea una cuenta o inicia sesión
3. Crea un nuevo clúster
4. Obtén tus credenciales:
   - Clave API de Qdrant: Se encuentra en la sección de Claves API
   - URL de Qdrant: La URL de tu clúster (formato: `https://xxx-xxx.aws.cloud.qdrant.io`)


## Cómo Ejecutar

1. Clona el repositorio:
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd rag_tutorials/rag_agent_cohere
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

```bash
streamlit run rag_agent_cohere.py
```


