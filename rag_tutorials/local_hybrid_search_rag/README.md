# 🖥️ Aplicación RAG Local con Búsqueda Híbrida

Una potente aplicación de preguntas y respuestas sobre documentos que aprovecha la Búsqueda Híbrida (RAG) y LLMs locales para obtener respuestas completas. Construida con RAGLite para un procesamiento y recuperación robustos de documentos, y Streamlit para una interfaz de chat intuitiva, este sistema combina el conocimiento específico de los documentos con las capacidades de los LLM locales para ofrecer respuestas precisas y contextuales.

## Demostración:


https://github.com/user-attachments/assets/375da089-1ab9-4bf4-b6f3-733f44e47403


## Inicio Rápido

Para pruebas inmediatas, utiliza estas configuraciones de modelos probadas:
```bash
# Modelo LLM
bartowski/Llama-3.2-3B-Instruct-GGUF/Llama-3.2-3B-Instruct-Q4_K_M.gguf@4096

# Modelo Embedder
lm-kit/bge-m3-gguf/bge-m3-Q4_K_M.gguf@1024
```
Estos modelos ofrecen un buen equilibrio entre rendimiento y uso de recursos, y se ha verificado que funcionan bien juntos incluso en un MacBook Air M2 con 8GB de RAM.

## Características

- **Integración de LLM Local**:
  - Utiliza modelos llama-cpp-python para inferencia local
  - Admite varios formatos de cuantización (se recomienda Q4_K_M)
  - Tamaños de ventana de contexto configurables

- **Procesamiento de Documentos**:
  - Carga y procesamiento de documentos PDF
  - Fragmentación y embedding automático de texto
  - Búsqueda híbrida que combina coincidencia semántica y de palabras clave
  - Reclasificación para una mejor selección de contexto

- **Integración Multimodelo**:
  - LLM local para generación de texto (p. ej., Llama-3.2-3B-Instruct)
  - Embeddings locales utilizando modelos BGE
  - FlashRank para reclasificación local

## Requisitos Previos

1. **Instala el Modelo spaCy**:
   ```bash
   pip install https://github.com/explosion/spacy-models/releases/download/xx_sent_ud_sm-3.7.0/xx_sent_ud_sm-3.7.0-py3-none-any.whl
   ```

2. **Instala llama-cpp-python Acelerado** (Opcional pero recomendado):
   ```bash
   # Configura variables de instalación
   LLAMA_CPP_PYTHON_VERSION=0.3.2
   PYTHON_VERSION=310 # 3.10, 3.11, 3.12
   ACCELERATOR=metal  # Para Mac
   # ACCELERATOR=cu121  # Para GPU NVIDIA
   PLATFORM=macosx_11_0_arm64  # Para Mac
   # PLATFORM=linux_x86_64  # Para Linux
   # PLATFORM=win_amd64  # Para Windows

   # Instala la versión acelerada
   pip install "https://github.com/abetlen/llama-cpp-python/releases/download/v$LLAMA_CPP_PYTHON_VERSION-$ACCELERATOR/llama_cpp_python-$LLAMA_CPP_PYTHON_VERSION-cp$PYTHON_VERSION-cp$PYTHON_VERSION-$PLATFORM.whl"
   ```

3. **Instala las Dependencias**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/rag_tutorials/local_hybrid_search_rag
   pip install -r requirements.txt
   ```

## Configuración del Modelo

RAGLite extiende LiteLLM con soporte para modelos llama.cpp usando llama-cpp-python. Para seleccionar un modelo llama.cpp (p. ej., de la colección de bartowski), usa un identificador de modelo con el formato "llama-cpp-python/<hugging_face_repo_id>/<filename>@<n_ctx>", donde n_ctx es un parámetro opcional que especifica el tamaño del contexto del modelo.

1. **Formato de Ruta del Modelo LLM**:
   ```
   llama-cpp-python/<repo>/<model>/<filename>@<context_length>
   ```
   Ejemplo:
   ```
   bartowski/Llama-3.2-3B-Instruct-GGUF/Llama-3.2-3B-Instruct-Q4_K_M.gguf@4096
   ```

2. **Formato de Ruta del Modelo Embedder**:
   ```
   llama-cpp-python/<repo>/<model>/<filename>@<dimension>
   ```
   Ejemplo:
   ```
   lm-kit/bge-m3-gguf/bge-m3-Q4_K_M.gguf@1024
   ```

## Configuración de la Base de Datos

La aplicación admite múltiples backends de base de datos:

- **PostgreSQL** (Recomendado):
  - Crea una base de datos PostgreSQL sin servidor gratuita en [Neon](https://neon.tech) en pocos clics
  - Obtén aprovisionamiento instantáneo y capacidad de escalado a cero
  - Formato de la cadena de conexión: `postgresql://user:pass@ep-xyz.region.aws.neon.tech/dbname`


## Cómo Ejecutar

1. **Inicia la Aplicación**:
   ```bash
   streamlit run local_main.py
   ```

2. **Configura la Aplicación**:
   - Ingresa la ruta del modelo LLM
   - Ingresa la ruta del modelo embedder
   - Establece la URL de la base de datos
   - Haz clic en "Guardar Configuración"

3. **Sube Documentos**:
   - Sube archivos PDF a través de la interfaz
   - Espera a que se complete el procesamiento

4. **Comienza a Chatear**:
   - Haz preguntas sobre tus documentos
   - Obtén respuestas utilizando el LLM local
   - Respaldo a conocimiento general cuando sea necesario

## Notas

- Se recomienda un tamaño de ventana de contexto de 4096 para la mayoría de los casos de uso
- La cuantización Q4_K_M ofrece un buen equilibrio entre velocidad y calidad
- El embedder BGE-M3 con 1024 dimensiones es óptimo
- Los modelos locales requieren suficientes recursos de RAM y CPU/GPU
- Aceleración Metal disponible para Mac, CUDA para GPU NVIDIA

## Contribuciones

¡Las contribuciones son bienvenidas! Por favor, siéntete libre de enviar un Pull Request.
