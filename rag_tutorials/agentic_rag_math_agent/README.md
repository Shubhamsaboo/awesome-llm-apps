# 🧠 Agente Tutor de Matemáticas – RAG Agéntico con Bucle de Retroalimentación

Este proyecto implementa una **arquitectura RAG Agéntica** para simular un profesor de matemáticas que resuelve **preguntas de matemáticas de nivel JEE** con explicaciones paso a paso. El sistema enruta inteligentemente las consultas entre una base de datos vectorial y la búsqueda web, aplica barreras de protección de entrada/salida e incorpora la retroalimentación humana para el aprendizaje continuo.

## 📌 Características

- ✅ **Barreras de Protección de Entrada** (DSPy): Acepta solo preguntas académicas de matemáticas.
- 📚 **Búsqueda en Base de Conocimientos**: Utiliza **Qdrant Vector DB** con Embeddings de OpenAI para encontrar preguntas conocidas.
- 🌐 **Respaldo Web**: Integra la **API de Tavily** cuando no se encuentra una buena coincidencia.
- ✍️ **Explicaciones GPT-4.1**: Genera soluciones matemáticas paso a paso.
- 🛡️ **Barreras de Protección de Salida**: Filtra para corrección y seguridad.
- 👍 **Retroalimentación Humana en el Bucle**: Los usuarios califican las respuestas (Sí/No), registradas para aprendizaje futuro.
- 📊 **Benchmarking**: Evaluado en el conjunto de datos **JEEBench** con límites de preguntas ajustables.
- 💻 **Interfaz de Usuario Streamlit**: Panel interactivo con múltiples pestañas.

## 🚀 Flujo de la Arquitectura
<img width="465" alt="Screenshot 2025-05-04 at 3 45 58 PM" src="https://github.com/user-attachments/assets/c0a9e612-2ef0-413c-b779-c99fe9f48619" />


## 📚 Base de Conocimientos

- **Conjunto de Datos:** [JEEBench (HuggingFace)](https://huggingface.co/datasets/daman1209arora/jeebench)
- **BD Vectorial:** Qdrant (con Embeddings de OpenAI)
- **Almacenamiento:** Construido con `llama-index` para persistir embeddings y realizar búsquedas de similitud top-1

## 🌐 Búsqueda Web

- Utiliza la **API de Tavily** para búsqueda de respaldo cuando la BC no contiene una buena coincidencia
- El contenido obtenido se envía a **GPT-4o** para una explicación clara


## 🔐 Barreras de Protección

- **Barrera de Protección de Entrada (DSPy):** Acepta solo preguntas académicas relacionadas con matemáticas
- **Barrera de Protección de Salida (DSPy):** Bloquea contenido alucinado o fuera de tema


## 👨‍🏫 Retroalimentación Humana en el Bucle

- La interfaz de usuario de Streamlit permite a los estudiantes dar 👍 / 👎 después de ver la respuesta
- La retroalimentación se registra en un archivo JSON local para mejoras futuras

## 📊 Benchmarking

- Evaluado en **50 Preguntas de Matemáticas Aleatorias de JEEBench**
- **Precisión Actual:** 66%
- Resultados del benchmark guardados en: `benchmark/results.csv`


## 🚀 Demostración

Para ejecutar la aplicación con Streamlit:

```bash
streamlit run app/streamlit.py




