## 🦙💬 Clon de ChatGPT usando Llama-3
Este proyecto demuestra cómo construir un clon de ChatGPT utilizando el modelo Llama-3 ejecutándose localmente en tu computadora. La aplicación está construida con Python y Streamlit, proporcionando una interfaz fácil de usar para interactuar con el modelo de lenguaje. ¡Lo mejor de todo es que es 100% gratis y no requiere conexión a internet!

### Características
- Se ejecuta localmente en tu computadora sin necesidad de conexión a internet y es completamente gratis.
- Utiliza el modelo Llama-3 instruct para generar respuestas
- Proporciona una interfaz similar a un chat para una interacción fluida

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_tools_frameworks/local_chatgpt_clone
```
2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```
3. Descarga e instala la [aplicación de escritorio LM Studio](https://lmstudio.ai/). Descarga el modelo Llama-3 instruct.

4. Expón el modelo Llama-3 como una API de OpenAI iniciando el servidor en LM Studio. Mira este [video tutorial](https://x.com/Saboo_Shubham_/status/1783715814790549683).

5. Ejecuta la Aplicación Streamlit
```bash
streamlit run chatgpt_clone_llama3.py
```

