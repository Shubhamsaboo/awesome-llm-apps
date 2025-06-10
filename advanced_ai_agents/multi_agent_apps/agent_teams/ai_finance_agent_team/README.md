## 💲 Equipo de Agentes de Finanzas de IA con Acceso Web
Este script demuestra cómo construir un equipo de agentes de IA que trabajan juntos como analistas financieros utilizando GPT-4o en solo 20 líneas de código Python. El sistema combina capacidades de búsqueda web con herramientas de análisis de datos financieros para proporcionar información financiera completa.

### Características
- Sistema multiagente con roles especializados:
    - Agente Web para investigación general en internet
    - Agente de Finanzas para análisis financiero detallado
    - Agente de Equipo para coordinar entre agentes
- Acceso a datos financieros en tiempo real a través de YFinance
- Capacidades de búsqueda web utilizando DuckDuckGo
- Almacenamiento persistente de interacciones de agentes utilizando SQLite

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team
```

2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```

3. Obtén tu Clave API de OpenAI

- Regístrate para obtener una [cuenta de OpenAI](https://platform.openai.com/) (o el proveedor de LLM de tu elección) y obtén tu clave API.
- Establece tu clave API de OpenAI como una variable de entorno:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

4. Ejecuta el equipo de Agentes de IA
```bash
python3 finance_agent_team.py
```

5. Abre tu navegador web y navega a la URL proporcionada en la salida de la consola para interactuar con el equipo de agentes de IA a través de la interfaz del patio de recreo.
