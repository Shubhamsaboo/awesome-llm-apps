# 🎮 Agente X vs Agente O: Juego de Tres en Raya

Un juego interactivo de Tres en Raya donde dos agentes de IA impulsados por diferentes modelos de lenguaje compiten entre sí, construido sobre Agno Agent Framework y Streamlit como interfaz de usuario.

Este ejemplo muestra cómo construir un juego interactivo de Tres en Raya donde los agentes de IA compiten entre sí. La aplicación muestra cómo:
- Coordinar múltiples agentes de IA en un juego por turnos
- Usar diferentes modelos de lenguaje para diferentes jugadores
- Crear una interfaz web interactiva con Streamlit
- Manejar el estado del juego y la validación de movimientos
- Mostrar el progreso del juego en tiempo real y el historial de movimientos

## Características
- Soporte para múltiples modelos de IA (GPT-4, Claude, Gemini, etc.)
- Visualización del juego en tiempo real
- Seguimiento del historial de movimientos con estados del tablero
- Selección interactiva de jugadores
- Gestión del estado del juego
- Validación y coordinación de movimientos

## ¿Cómo Ejecutar?

1. **Configurar el Entorno**
   ```bash
   # Clona el repositorio
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_tic_tac_toe_agent

   # Instala las dependencias
   pip install -r requirements.txt
   ```

### 2. Instalar dependencias

```shell
pip install -r requirements.txt
```

### 3. Exportar Claves API

El juego admite múltiples modelos de IA. Exporta las claves API para los modelos que deseas utilizar:

```shell
# Requerido para modelos OpenAI
export OPENAI_API_KEY=***

# Opcional - para modelos adicionales
export ANTHROPIC_API_KEY=***  # Para modelos Claude
export GOOGLE_API_KEY=***     # Para modelos Gemini
export GROQ_API_KEY=***       # Para modelos Groq
```

### 4. Ejecutar el Juego

```shell
streamlit run app.py
```

- Abre [localhost:8501](http://localhost:8501) para ver la interfaz del juego

## Cómo Funciona

El juego consta de tres agentes:

1. **Agente Maestro (Árbitro)**
   - Coordina el juego
   - Valida los movimientos
   - Mantiene el estado del juego
   - Determina el resultado del juego

2. **Dos Agentes Jugadores**
   - Realizan movimientos estratégicos
   - Analizan el estado del tablero
   - Siguen las reglas del juego
   - Responden a los movimientos del oponente

## Modelos Disponibles

El juego admite varios modelos de IA:
- GPT-4o (OpenAI)
- GPT-o3-mini (OpenAI)
- Gemini (Google)
- Llama 3 (Groq)
- Claude (Anthropic)

## Características del Juego

1. **Tablero Interactivo**
   - Actualizaciones en tiempo real
   - Seguimiento visual de movimientos
   - Visualización clara del estado del juego

2. **Historial de Movimientos**
   - Seguimiento detallado de movimientos
   - Visualización del estado del tablero
   - Cronología de acciones del jugador

3. **Controles del Juego**
   - Iniciar/Pausar juego
   - Reiniciar tablero
   - Seleccionar modelos de IA
   - Ver historial del juego

4. **Análisis de Rendimiento**
   - Tiempos de movimiento
   - Seguimiento de estrategias
   - Estadísticas del juego
