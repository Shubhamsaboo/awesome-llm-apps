# Agencia de Servicios de IA 👨‍💼

Una aplicación de IA que simula una agencia digital de servicio completo utilizando múltiples agentes de IA para analizar y planificar proyectos de software. Cada agente representa un rol diferente en el ciclo de vida del proyecto, desde la planificación estratégica hasta la implementación técnica.

## Demostración:

https://github.com/user-attachments/assets/a0befa3a-f4c3-400d-9790-4b9e37254405

## Características

### Cinco agentes de IA especializados

- **Agente CEO**: Líder estratégico y tomador de decisiones final
  - Analiza ideas de startups utilizando una evaluación estructurada
  - Toma decisiones estratégicas en los dominios de producto, técnico, marketing y financiero
  - Utiliza las herramientas AnalyzeStartupTool y MakeStrategicDecision

- **Agente CTO**: Experto en arquitectura técnica y viabilidad
  - Evalúa los requisitos técnicos y la viabilidad
  - Proporciona decisiones de arquitectura
  - Utiliza las herramientas QueryTechnicalRequirements y EvaluateTechnicalFeasibility

- **Agente Product Manager**: Especialista en estrategia de producto
  - Define la estrategia y la hoja de ruta del producto
  - Coordina entre los equipos técnicos y de marketing
  - Se centra en el ajuste producto-mercado

- **Agente Desarrollador**: Experto en implementación técnica
  - Proporciona orientación detallada sobre la implementación técnica
  - Sugiere el stack tecnológico óptimo y soluciones en la nube
  - Estima los costos y plazos de desarrollo

- **Agente de Éxito del Cliente**: Líder de estrategia de marketing
  - Desarrolla estrategias de lanzamiento al mercado
  - Planifica enfoques de adquisición de clientes
  - Coordina con el equipo de producto

### Herramientas Personalizadas

La agencia utiliza herramientas especializadas construidas con OpenAI Schema para un análisis estructurado:
- **Herramientas de Análisis**: AnalyzeProjectRequirements para la evaluación de mercado y el análisis de la idea de startup
- **Herramientas Técnicas**: CreateTechnicalSpecification para la evaluación técnica

### 🔄 Comunicación Asíncrona

La agencia opera en modo asíncrono, permitiendo:
- Procesamiento paralelo de análisis de diferentes agentes
- Colaboración eficiente multiagente
- Comunicación en tiempo real entre agentes
- Operaciones no bloqueantes para un mejor rendimiento

### 🔗 Flujos de Comunicación de Agentes
- CEO ↔️ Todos los Agentes (Supervisión Estratégica)
- CTO ↔️ Desarrollador (Implementación Técnica)
- Product Manager ↔️ Gerente de Marketing (Estrategia de Lanzamiento al Mercado)
- Product Manager ↔️ Desarrollador (Implementación de Funciones)
- (¡y más!)

## Cómo Ejecutar

Sigue los pasos a continuación para configurar y ejecutar la aplicación:
Antes que nada, obtén tu Clave API de OpenAI aquí: https://platform.openai.com/api-keys

1. **Clona el Repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency
   ```

2. **Instala las dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Ejecuta la aplicación Streamlit**:
    ```bash
    streamlit run ai_services_agency/agency.py
    ```

4. **Ingresa tu Clave API de OpenAI** en la barra lateral cuando se te solicite ¡y comienza a analizar tu idea de startup!
