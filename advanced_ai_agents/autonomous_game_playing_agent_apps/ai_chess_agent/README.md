# ♜ Agente Blanco vs Agente Negro: Partida de Ajedrez

Un sistema avanzado de juego de Ajedrez donde dos agentes de IA juegan ajedrez entre sí usando Autogen en una aplicación de Streamlit. Está construido con una robusta validación de movimientos y gestión del estado del juego.

## Características

### Arquitectura Multi-Agente
- Jugador Blanco: Tomador de decisiones estratégicas impulsado por OpenAI
- Jugador Negro: Oponente táctico impulsado por OpenAI
- Proxy del Tablero: Agente de validación para la legalidad de los movimientos y el estado del juego

### Seguridad y Validación
- Sistema robusto de verificación de movimientos
- Prevención de movimientos ilegales
- Monitoreo del estado del tablero en tiempo real
- Control seguro de la progresión del juego

### Jugabilidad Estratégica
- Evaluación de posiciones impulsada por IA
- Análisis táctico profundo
- Adaptación dinámica de la estrategia
- Implementación completa del reglamento de ajedrez


### ¿Cómo Empezar?

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd ai_agent_tutorials/ai_chess_game
```
2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```
3. Obtén tu Clave API de OpenAI

- Regístrate para obtener una [cuenta de OpenAI](https://platform.openai.com/) (o el proveedor de LLM de tu elección) y obtén tu clave API.

4. Ejecuta la Aplicación Streamlit
```bash
streamlit run ai_chess_agent.py
```

