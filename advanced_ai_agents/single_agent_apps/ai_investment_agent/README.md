## 📈 Agente de Inversión de IA
Esta aplicación de Streamlit es un agente de inversión impulsado por IA construido con el framework Agno AI Agent que compara el rendimiento de dos acciones y genera informes detallados. Mediante el uso de GPT-4o con datos de Yahoo Finance, esta aplicación proporciona información valiosa para ayudarte a tomar decisiones de inversión informadas.

### Características
- Compara el rendimiento de dos acciones
- Recupera información completa de la empresa
- Obtén las últimas noticias de la empresa y recomendaciones de analistas
- Obtén las últimas noticias de la empresa y recomendaciones de analistas

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/single_agent_apps/ai_investment_agent
```
2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```
3. Obtén tu Clave API de OpenAI

- Regístrate para obtener una [cuenta de OpenAI](https://platform.openai.com/) (o el proveedor de LLM de tu elección) y obtén tu clave API.

4. Ejecuta la Aplicación Streamlit
```bash
streamlit run investment_agent.py
```

### ¿Cómo Funciona?

- Al ejecutar la aplicación, se te pedirá que ingreses tu clave API de OpenAI. Esta clave se utiliza para autenticar y acceder al modelo de lenguaje de OpenAI.
- Una vez que proporciones una clave API válida, se creará una instancia de la clase Assistant. Este asistente utiliza el modelo de lenguaje GPT-4o de OpenAI y YFinanceTools para acceder a los datos bursátiles.
- Ingresa los símbolos bursátiles de las dos empresas que deseas comparar en los campos de entrada de texto proporcionados.
- El asistente realizará los siguientes pasos:
    - Recuperar precios de acciones en tiempo real y datos históricos utilizando YFinanceTools
    - Obtener las últimas noticias de la empresa y recomendaciones de analistas
    - Recopilar información completa de la empresa
    - Generar un informe de comparación detallado utilizando el modelo de lenguaje GPT-4
- El informe generado se mostrará en la aplicación, proporcionándote información y análisis valiosos para guiar tus decisiones de inversión.