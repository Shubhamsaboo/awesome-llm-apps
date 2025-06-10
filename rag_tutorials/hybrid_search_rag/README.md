# 👀 Aplicación RAG con Búsqueda Híbrida

Una potente aplicación de preguntas y respuestas sobre documentos que aprovecha la Búsqueda Híbrida (RAG) y las capacidades avanzadas de lenguaje de Claude para proporcionar respuestas completas. Construido con RAGLite para un procesamiento y recuperación robustos de documentos, y Streamlit para una interfaz de chat intuitiva, este sistema combina a la perfección el conocimiento específico de los documentos con la inteligencia general de Claude para ofrecer respuestas precisas y contextuales.

## Características

- **Preguntas y Respuestas con Búsqueda Híbrida**
    - Respuestas basadas en RAG para consultas específicas de documentos
    - Respaldo a Claude para preguntas de conocimiento general

- **Procesamiento de Documentos**:
  - Carga y procesamiento de documentos PDF
  - Fragmentación y embedding automático de texto
  - Búsqueda híbrida que combina coincidencia semántica y de palabras clave
  - Reclasificación para una mejor selección de contexto

- **Integración Multimodelo**:
  - Claude para generación de texto - probado con Claude 3 Opus
  - OpenAI para embeddings - probado con text-embedding-3-large
  - Cohere para reclasificación - probado con Cohere 3.5 reranker

## Requisitos Previos

Necesitarás las siguientes claves API y configuración de base de datos:

1. **Base de Datos**: Crea una base de datos PostgreSQL gratuita en [Neon](https://neon.tech):
   - Regístrate/Inicia sesión en Neon
   - Crea un nuevo proyecto
   - Copia la cadena de conexión (se parece a: `postgresql://user:pass@ep-xyz.region.aws.neon.tech/dbname`)

2. **Claves API**:
   - [Clave API de OpenAI](https://platform.openai.com/api-keys) para embeddings
   - [Clave API de Anthropic](https://console.anthropic.com/settings/keys) para Claude
   - [Clave API de Cohere](https://dashboard.cohere.com/api-keys) para reclasificación

## ¿Cómo Empezar?

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/rag_tutorials/hybrid_search_rag
   ```

2. **Instala las Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Instala el Modelo spaCy**:
   ```bash
   pip install https://github.com/explosion/spacy-models/releases/download/xx_sent_ud_sm-3.7.0/xx_sent_ud_sm-3.7.0-py3-none-any.whl
   ```

4. **Ejecuta la Aplicación**:
   ```bash
   streamlit run main.py
   ```

## Uso

1. Inicia la aplicación
2. Ingresa tus claves API en la barra lateral:
   - Clave API de OpenAI
   - Clave API de Anthropic
   - Clave API de Cohere
   - URL de la base de datos (opcional, por defecto SQLite)
3. Haz clic en "Guardar Configuración"
4. Sube documentos PDF
5. ¡Comienza a hacer preguntas!
   - Las preguntas específicas de documentos utilizarán RAG
   - Las preguntas generales utilizarán Claude directamente

## Opciones de Base de Datos

La aplicación admite múltiples backends de base de datos:

- **PostgreSQL** (Recomendado):
  - Crea una base de datos PostgreSQL sin servidor gratuita en [Neon](https://neon.tech)
  - Obtén aprovisionamiento instantáneo y capacidad de escalado a cero
  - Formato de la cadena de conexión: `postgresql://user:pass@ep-xyz.region.aws.neon.tech/dbname`

- **MySQL**:
  ```
  mysql://user:pass@host:port/db
  ```
- **SQLite** (Desarrollo local):
  ```
  sqlite:///path/to/db.sqlite
  ```

## Contribuciones

¡Las contribuciones son bienvenidas! Por favor, siéntete libre de enviar un Pull Request.
