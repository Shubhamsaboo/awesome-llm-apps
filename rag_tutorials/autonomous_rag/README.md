# 🤖 AutoRAG: RAG Autónomo con GPT-4o y Base de Datos Vectorial
Esta aplicación de Streamlit implementa un sistema de Generación Aumentada por Recuperación (RAG) Autónomo utilizando el modelo GPT-4o de OpenAI y la base de datos PgVector. Permite a los usuarios cargar documentos PDF, agregarlos a una base de conocimientos y consultar al asistente de IA con contexto tanto de la base de conocimientos como de búsquedas web.

### Características
- Interfaz de chat para interactuar con el asistente de IA
- Carga y procesamiento de documentos PDF
- Integración de base de conocimientos utilizando PostgreSQL y Pgvector
- Capacidad de búsqueda web utilizando DuckDuckGo
- Almacenamiento persistente de datos y conversaciones del asistente

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/rag_tutorials/autonomous_rag
```

2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```

3. Asegúrate de que la Base de Datos PgVector esté en ejecución:
La aplicación espera que PgVector esté en ejecución en [localhost:5532](http://localhost:5532/). Ajusta la configuración en el código si tu configuración es diferente.

```bash
docker run -d \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgvolume:/var/lib/postgresql/data \
  -p 5532:5432 \
  --name pgvector \
  phidata/pgvector:16
```

4. Ejecuta la Aplicación Streamlit
```bash
streamlit run autorag.py
```
