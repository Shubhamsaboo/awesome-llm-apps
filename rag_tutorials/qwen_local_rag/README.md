# 🐋 Agente de Razonamiento RAG Local Qwen 3

Esta Aplicación RAG demuestra cómo construir un potente sistema de Generación Aumentada por Recuperación (RAG) utilizando modelos Qwen 3 y Gemma 3 ejecutándose localmente a través de Ollama. Combina procesamiento de documentos, búsqueda vectorial y capacidades de búsqueda web para proporcionar respuestas precisas y conscientes del contexto a las consultas de los usuarios.

## Características

- **🧠 Múltiples Opciones de LLM Locales**:

  - Qwen3 (1.7b, 8b) - Últimos modelos de lenguaje de Alibaba
  - Gemma3 (1b, 4b) - Modelos de lenguaje eficientes de Google con capacidades multimodales
  - DeepSeek (1.5b) - Opción de modelo alternativa
- **📚 Sistema RAG Completo**:

  - Carga y procesa documentos PDF
  - Extrae contenido de URL web
  - Fragmentación y embedding inteligentes
  - Búsqueda de similitud con umbral ajustable
- **🌐 Integración de Búsqueda Web**:

  - Respaldo a búsqueda web cuando el conocimiento del documento es insuficiente
  - Filtrado de dominio configurable
  - Atribución de fuentes en las respuestas
- **🔄 Modos de Operación Flexibles**:

  - Alterna entre RAG e interacción directa con LLM
  - Fuerza la búsqueda web cuando sea necesario
  - Ajusta los umbrales de similitud para la recuperación de documentos
- **💾 Integración de Base de Datos Vectorial**:

  - Base de datos vectorial Qdrant para búsqueda eficiente por similitud
  - Almacenamiento persistente de embeddings de documentos

## Cómo Empezar

### Requisitos Previos

- [Ollama](https://ollama.ai/) instalado localmente
- Python 3.8+
- Cuenta Qdrant (nivel gratuito disponible) para almacenamiento de vectores
- Clave API de Exa (opcional, para capacidad de búsqueda web)

### Instalación

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd rag_tutorials/qwen_local_rag
```

2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```

3. Descarga los modelos requeridos usando Ollama:

```bash
ollama pull qwen3:1.7b # O cualquier otro modelo que quieras usar
ollama pull snowflake-arctic-embed # O cualquier otro modelo que quieras usar
```
4. Ejecuta Qdrant localmente a través de docker
```bash
docker pull qdrant/qdrant

docker run -p 6333:6333 -p 6334:6334 \
    -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
    qdrant/qdrant
```


4. Obtén tus claves API:

   - Clave API de Exa (opcional, para búsqueda web)
   
5. Ejecuta la aplicación:

```bash
streamlit run qwen_local_rag_agent.py
```

## Cómo Funciona

1. **Procesamiento de Documentos**:

   - Los archivos PDF se procesan usando PyPDFLoader
   - El contenido web se extrae usando WebBaseLoader
   - Los documentos se dividen en fragmentos con RecursiveCharacterTextSplitter
2. **Base de Datos Vectorial**:

   - Los fragmentos de documentos se incrustan usando los modelos de embedding de Ollama
   - Los embeddings se almacenan en la base de datos vectorial Qdrant
   - La búsqueda por similitud recupera documentos relevantes basados en la consulta
3. **Procesamiento de Consultas**:

   - Las consultas de los usuarios se analizan para determinar la mejor fuente de información
   - El sistema verifica la relevancia del documento usando el umbral de similitud
   - Recurre a la búsqueda web si no se encuentran documentos relevantes
4. **Generación de Respuestas**:

   - El LLM local (Qwen/Gemma) genera respuestas basadas en el contexto recuperado
   - Las fuentes se citan y se muestran al usuario
   - Los resultados de la búsqueda web se indican claramente cuando se utilizan

## Opciones de Configuración

- **Selección de Modelo**: Elige entre diferentes modelos Qwen, Gemma y DeepSeek
- **Modo RAG**: Alterna entre RAG habilitado e interacción directa con LLM
- **Ajuste de Búsqueda**: Ajusta el umbral de similitud para la recuperación de documentos
- **Búsqueda Web**: Habilita/deshabilita el respaldo de búsqueda web y configura el filtrado de dominios

## Casos de Uso

- **Preguntas y Respuestas sobre Documentos**: Haz preguntas sobre tus documentos cargados
- **Asistente de Investigación**: Combina el conocimiento de los documentos con la búsqueda web
- **Privacidad Local**: Procesa documentos sensibles sin enviar datos a API externas
- **Operación sin Conexión**: Ejecuta capacidades avanzadas de IA con acceso limitado o nulo a internet

## Requisitos

Consulta `requirements.txt` para la lista completa de dependencias.
