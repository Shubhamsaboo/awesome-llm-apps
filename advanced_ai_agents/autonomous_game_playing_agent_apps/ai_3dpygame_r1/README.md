# 🎮 Visualizador 3D de PyGame con IA y DeepSeek R1
Este proyecto demuestra las capacidades de codificación de R1 con un generador y visualizador de código PyGame para uso en navegador. El sistema utiliza DeepSeek para el razonamiento, OpenAI para la extracción de código y agentes de automatización de navegador para visualizar el código en Trinket.io.

### Características

- Genera código PyGame a partir de descripciones en lenguaje natural
- Utiliza DeepSeek Reasoner para la lógica y explicación del código
- Extrae código limpio utilizando OpenAI GPT-4o
- Automatiza la visualización de código en Trinket.io utilizando agentes de navegador
- Proporciona una interfaz de Streamlit optimizada
- Sistema multiagente para manejar diferentes tareas (navegación, codificación, ejecución, visualización)

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/ai_agent_tutorials/ai_3dpygame_r1
```

2. Instala las dependencias requeridas:
```bash
pip install -r requirements.txt
```

3. Obtén tus Claves API
- Regístrate en [DeepSeek](https://platform.deepseek.com/) y obtén tu clave API
- Regístrate en [OpenAI](https://platform.openai.com/) y obtén tu clave API

4. Ejecuta el Visualizador de PyGame con IA
```bash
streamlit run ai_3dpygame_r1.py
```

5. El uso del navegador abre automáticamente tu navegador web y navega a la URL proporcionada en la salida de la consola para interactuar con el generador de PyGame.

### ¿Cómo Funciona?

1. **Procesamiento de Consultas:** El usuario ingresa una descripción en lenguaje natural de la visualización de PyGame deseada.
2. **Generación de Código:**
   - DeepSeek Reasoner analiza la consulta y proporciona un razonamiento detallado con código
   - El agente de OpenAI extrae código limpio y ejecutable del razonamiento
3. **Visualización:**
   - Los agentes del navegador automatizan el proceso de ejecución de código en Trinket.io
   - Múltiples agentes especializados manejan diferentes tareas:
     - Navegación a Trinket.io
     - Entrada de código
     - Ejecución
     - Visualización de la visualización
4. **Interfaz de Usuario:** Streamlit proporciona una interfaz intuitiva para ingresar consultas, ver código y gestionar el proceso de visualización.
