# Equipo de Agentes de Diseño de Juegos de IA 🎮

El Equipo de Agentes de Diseño de Juegos de IA es un sistema colaborativo de diseño de juegos impulsado por el framework de Agentes de IA de [AG2](https://github.com/ag2ai/ag2?tab=readme-ov-file) (anteriormente AutoGen). Esta aplicación genera conceptos de juego completos mediante la coordinación de múltiples agentes de IA especializados, cada uno centrado en diferentes aspectos del diseño del juego basados en las entradas del usuario, como el tipo de juego, el público objetivo, el estilo artístico y los requisitos técnicos. Esto se basa en la nueva función de enjambre de AG2 ejecutada a través del método `initiate_chat()`.

## Características

- **Equipo Especializado de Agentes de Diseño de Juegos**
    - 🎭 **Agente de Historia**: Se especializa en el diseño narrativo y la construcción de mundos, incluido el desarrollo de personajes, los arcos argumentales, la escritura de diálogos y la creación de lore.
    - 🎮 **Agente de Jugabilidad**: Se centra en la mecánica del juego y el diseño de sistemas, incluida la progresión del jugador, los sistemas de combate, la gestión de recursos y el equilibrio.
    - 🎨 **Agente Visual**: Maneja la dirección de arte y el diseño de audio, cubriendo UI/UX, estilo de arte de personajes/entornos, efectos de sonido y composición musical.
    - ⚙️ **Agente Tecnológico**: Proporciona arquitectura técnica y orientación de implementación, incluida la selección del motor, estrategias de optimización, requisitos de red y hoja de ruta de desarrollo.
    - 🎯 **Agente de Tareas**: Coordina entre todos los agentes especializados y garantiza la integración cohesiva de los diferentes aspectos del juego.

- **Resultados Completos de Diseño de Juegos**:
  - Elementos detallados de narrativa y construcción de mundos
  - Mecánicas y sistemas centrales de juego
  - Dirección visual y de audio
  - Especificaciones y requisitos técnicos
  - Cronograma de desarrollo y consideraciones presupuestarias
  - Diseño de juego coherente del equipo.

- **Parámetros de Entrada Personalizables**:
  - Tipo de juego y público objetivo
  - Estilo artístico y preferencias visuales
  - Requisitos de la plataforma
  - Restricciones de desarrollo (tiempo, presupuesto)
  - Mecánicas centrales y características de juego

- **Resultados Interactivos**:
   - Muestra rápida de ideas de diseño de juegos de cada agente
   - Los resultados detallados se presentan en secciones expandibles para facilitar la navegación y referencia

## Cómo Ejecutar

Sigue estos pasos para configurar y ejecutar la aplicación:

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_game_design_agent_team
   ```

2. **Instala las Dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura la Clave API de OpenAI**:
   - Obtén una clave API de OpenAI desde la [plataforma de OpenAI](https://platform.openai.com)
   - Ingresarás esta clave en la barra lateral de la aplicación al ejecutarla

4. **Ejecuta la Aplicación Streamlit**:
   ```bash
   streamlit run ai_game_design_agent_team/game_design_agent_team.py
   ```

## Uso

1. Ingresa tu clave API de OpenAI en la barra lateral
2. Completa los detalles del juego:
   - Ambiente y entorno de fondo
   - Tipo de juego y público objetivo
   - Preferencias de estilo visual
   - Requisitos técnicos
   - Restricciones de desarrollo
3. Haz clic en "Generar Concepto de Juego" para recibir documentación de diseño completa de todos los agentes
4. Revisa los resultados en las secciones expandibles para cada aspecto del diseño del juego
