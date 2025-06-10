## 📡 Aplicación de Chat RouteLLM

> Nota: Este proyecto está inspirado en la biblioteca de código abierto [RouteLLM library](https://github.com/lm-sys/RouteLLM/tree/main), que proporciona un enrutamiento inteligente entre diferentes modelos de lenguaje.

Esta aplicación Streamlit demuestra el uso de RouteLLM, un sistema que enruta inteligentemente las consultas entre diferentes modelos de lenguaje según la complejidad de la tarea. Proporciona una interfaz de chat donde los usuarios pueden interactuar con modelos de IA, y la aplicación selecciona automáticamente el modelo más apropiado para cada consulta.

### Características
- Interfaz de chat para interactuar con modelos de IA
- Selección automática de modelos mediante RouteLLM
- Utiliza los modelos GPT-4 y Meta-Llama 3.1
- Muestra el historial de chat con información del modelo

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_tools_frameworks/llm_router_app
```
2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```
3. Configura tus claves API:

```bash
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"
os.environ['TOGETHERAI_API_KEY'] = "your_togetherai_api_key"
```
Nota: En un entorno de producción, se recomienda utilizar variables de entorno o un sistema seguro de gestión de configuración en lugar de codificar las claves API directamente.

4. Ejecuta la Aplicación Streamlit
```bash
streamlit run llm_router.py
```

### ¿Cómo Funciona?

1. Inicialización de RouteLLM: La aplicación inicializa el controlador RouteLLM con dos modelos:
    - Modelo fuerte: GPT-4 (mini)
    -  Modelo débil: Meta-Llama 3.1 70B Instruct Turbo

2. Interfaz de Chat: Los usuarios pueden ingresar mensajes a través de una interfaz de chat.

3. Selección de Modelo: RouteLLM selecciona automáticamente el modelo apropiado según la complejidad de la consulta del usuario.

4. Generación de Respuesta: El modelo seleccionado genera una respuesta a la entrada del usuario.

5. Visualización: La aplicación muestra la respuesta junto con información sobre qué modelo se utilizó.

6. Historial: El historial de chat se mantiene y se muestra, incluyendo información del modelo para cada respuesta.