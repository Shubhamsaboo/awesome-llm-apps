# 📠 Agente RAG con Enrutamiento de Base de Datos

Una aplicación de Streamlit que demuestra una implementación avanzada de Agente RAG con enrutamiento inteligente de consultas. El sistema combina múltiples bases de datos especializadas con mecanismos de respaldo inteligentes para garantizar respuestas confiables y precisas a las consultas de los usuarios.

## Características

- **Carga de Documentos**: Los usuarios pueden cargar múltiples documentos PDF relacionados con una empresa en particular. Estos documentos se procesan y almacenan en una de las tres bases de datos: Información del Producto, Soporte al Cliente y Preguntas Frecuentes, o Información Financiera.
  
- **Consultas en Lenguaje Natural**: Los usuarios pueden hacer preguntas en lenguaje natural. El sistema enruta automáticamente la consulta a la base de datos más relevante utilizando un agente phidata como enrutador.

- **Orquestación RAG**: Utiliza Langchain para orquestar el proceso de generación aumentada por recuperación, asegurando que se recupere y presente al usuario la información más relevante.

- **Mecanismo de Respaldo**: Si no se encuentran documentos relevantes en las bases de datos, se utiliza un agente LangGraph con una herramienta de búsqueda DuckDuckGo para realizar investigaciones web y proporcionar una respuesta.

## ¿Cómo Ejecutar?

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd rag_tutorials/rag_database_routing
   ```

2. **Instala las Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecuta la Aplicación**:
   ```bash
   streamlit run rag_database_routing.py
   ```

4. **Obtén la Clave API de OpenAI**: Obtén una clave API de OpenAI y configúrala en la aplicación. Esto es necesario para inicializar los modelos de lenguaje utilizados en la aplicación.

5. **Configura Qdrant Cloud**
- Visita [Qdrant Cloud](https://cloud.qdrant.io/)
- Crea una cuenta o inicia sesión
- Crea un nuevo clúster
- Obtén tus credenciales:
   - Clave API de Qdrant: Se encuentra en la sección de Claves API
   - URL de Qdrant: La URL de tu clúster (formato: https://xxx-xxx.aws.cloud.qdrant.io)

5. **Sube Documentos**: Utiliza la sección de carga de documentos para agregar documentos PDF a la base de datos deseada.

6. **Haz Preguntas**: Ingresa tus preguntas en la sección de consultas. La aplicación enrutará tu pregunta a la base de datos apropiada y proporcionará una respuesta.

## Tecnologías Utilizadas

- **Langchain**: Para la orquestación RAG, asegurando una recuperación y generación eficiente de información.
- **Agente Phidata**: Utilizado como agente enrutador para determinar la base de datos más relevante para una consulta dada.
- **Agente LangGraph**: Actúa como un mecanismo de respaldo, utilizando DuckDuckGo para la investigación web cuando sea necesario.
- **Streamlit**: Proporciona una interfaz fácil de usar para la carga de documentos y la realización de consultas.
- **Qdrant**: Utilizado para gestionar las bases de datos, almacenando y recuperando eficientemente los embeddings de los documentos.

## ¿Cómo Funciona?

**1. Enrutamiento de Consultas**
El sistema utiliza un enfoque de enrutamiento de tres etapas:
- Búsqueda de similitud vectorial en todas las bases de datos
- Enrutamiento basado en LLM para consultas ambiguas
- Respaldo de búsqueda web para temas desconocidos

**2. Procesamiento de Documentos**
- Extracción automática de texto de PDF
- Fragmentación inteligente de texto con superposición
- Generación de embeddings vectoriales
- Almacenamiento eficiente en base de datos

**3. Generación de Respuestas**
- Recuperación consciente del contexto
- Combinación inteligente de documentos
- Respuestas basadas en la confianza
- Integración de investigación web