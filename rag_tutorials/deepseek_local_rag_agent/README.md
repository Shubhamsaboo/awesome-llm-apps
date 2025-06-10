# 🐋 Agente de Razonamiento RAG Local Deepseek

Un potente agente de razonamiento que combina modelos locales Deepseek con capacidades RAG. Construido utilizando Deepseek (a través de Ollama), Snowflake para embeddings, Qdrant para almacenamiento de vectores y Agno para la orquestación de agentes, esta aplicación ofrece tanto chat local simple como interacciones avanzadas mejoradas con RAG con procesamiento integral de documentos y capacidades de búsqueda web.

## Características

- **Modos de Operación Dual**
  - Modo Chat Local: Interacción directa con Deepseek localmente
  - Modo RAG: Razonamiento mejorado con contexto de documentos e integración de búsqueda web - llama3.2

- **Procesamiento de Documentos** (Modo RAG)
  - Carga y procesamiento de documentos PDF
  - Extracción de contenido de páginas web
  - Fragmentación y embedding automático de texto
  - Almacenamiento de vectores en la nube Qdrant

- **Consultas Inteligentes** (Modo RAG)
  - Recuperación de documentos basada en RAG
  - Búsqueda de similitud con filtrado de umbral
  - Respaldo automático a búsqueda web
  - Atribución de fuentes para las respuestas

- **Capacidades Avanzadas**
  - Integración de búsqueda web Exa AI
  - Filtrado de dominio personalizado para búsqueda web
  - Generación de respuestas conscientes del contexto
  - Gestión del historial de chat
  - Visualización del proceso de pensamiento

- **Características Específicas del Modelo**
  - Selección flexible de modelos:
    - Deepseek r1 1.5b (más ligero, adecuado para la mayoría de las laptops)
    - Deepseek r1 7b (más capaz, requiere mejor hardware)
  - Modelo de Embedding Snowflake Arctic (SOTA) para embeddings vectoriales
  - Framework Agno Agent para orquestación
  - Interfaz interactiva basada en Streamlit

## Requisitos Previos

### 1. Configuración de Ollama
1. Instala [Ollama](https://ollama.ai)
2. Descarga los modelos Deepseek r1:
```bash
# Para el modelo más ligero
ollama pull deepseek-r1:1.5b

# Para el modelo más capaz (si tu hardware lo soporta)
ollama pull deepseek-r1:7b

ollama pull snowflake-arctic-embed
ollama pull llama3.2
```

### 2. Configuración de Qdrant Cloud (para Modo RAG)
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
cd rag_tutorials/deepseek_local_rag_agent
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta la aplicación:
```bash
streamlit run deepseek_rag_agent.py
```

