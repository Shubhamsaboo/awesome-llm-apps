## 🗞️ Agente Periodista de IA
Esta aplicación de Streamlit es un agente periodista impulsado por IA que genera artículos de alta calidad utilizando OpenAI GPT-4o. Automatiza el proceso de investigación, redacción y edición de artículos, permitiéndote crear contenido atractivo sobre cualquier tema con facilidad.

### Características
- Busca en la web información relevante sobre un tema determinado
- Escribe artículos bien estructurados, informativos y atractivos
- Edita y refina el contenido generado para cumplir con los altos estándares del New York Times

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_journalist_agent
```
2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```
3. Obtén tu Clave API de OpenAI

- Regístrate para obtener una [cuenta de OpenAI](https://platform.openai.com/) (o el proveedor de LLM de tu elección) y obtén tu clave API.

4. Obtén tu Clave API de SerpAPI

- Regístrate para obtener una [cuenta de SerpAPI](https://serpapi.com/) y obtén tu clave API.

5. Ejecuta la Aplicación Streamlit
```bash
streamlit run journalist_agent.py
```

### ¿Cómo Funciona?

El Agente Periodista de IA utiliza tres componentes principales:
- Buscador: Responsable de generar términos de búsqueda basados en el tema dado y buscar en la web URL relevantes utilizando SerpAPI.
- Escritor: Recupera el texto de las URL proporcionadas utilizando NewspaperToolkit y escribe un artículo de alta calidad basado en la información extraída.
- Editor: Coordina el flujo de trabajo entre el Buscador y el Escritor, y realiza la edición final y el refinamiento del artículo generado.

