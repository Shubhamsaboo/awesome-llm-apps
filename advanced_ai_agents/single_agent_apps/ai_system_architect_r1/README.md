# 🤖 Asesor de Arquitectura de Sistemas de IA con R1

Un sistema agéntico de Agno que proporciona análisis y recomendaciones de arquitectura de software experta utilizando un enfoque de modelo dual que combina el Razonamiento de DeepSeek R1 y Claude. El sistema proporciona análisis técnicos detallados, hojas de ruta de implementación y decisiones arquitectónicas para sistemas de software complejos.

## Características

- **Arquitectura de Modelo de IA Dual**
  - **DeepSeek Reasoner**: Proporciona análisis técnico inicial y razonamiento estructurado sobre patrones de arquitectura, herramientas y estrategias de implementación.
  - **Claude-3.5**: Genera explicaciones detalladas, hojas de ruta de implementación y especificaciones técnicas basadas en el análisis de DeepSeek.

- **Componentes de Análisis Exhaustivo**
  - Selección de Patrones de Arquitectura
  - Planificación de Recursos de Infraestructura
  - Medidas de Seguridad y Cumplimiento
  - Arquitectura de Base de Datos
  - Requisitos de Rendimiento
  - Estimación de Costos
  - Evaluación de Riesgos

- **Tipos de Análisis**
  - Sistemas de Procesamiento de Eventos en Tiempo Real
  - Plataformas de Datos de Atención Médica
  - Plataformas de Negociación Financiera
  - Soluciones SaaS Multiusuario
  - Redes de Entrega de Contenido Digital
  - Sistemas de Gestión de la Cadena de Suministro

## Cómo Ejecutar

1. **Configurar el Entorno**
   ```bash
   # Clona el repositorio
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/single_agent_apps/ai_system_architect_r1
   
   # Instala las dependencias
   pip install -r requirements.txt
   ```

2. **Configurar Claves API**
   - Obtén la clave API de DeepSeek desde la plataforma DeepSeek
   - Obtén la clave API de Anthropic desde [Anthropic Platform](https://www.anthropic.com)

3. **Ejecutar la Aplicación**
   ```bash
   streamlit run ai_system_architect_r1.py
   ```

4. **Usar la Interfaz**
   - Ingresa las credenciales de API en la barra lateral
   - Estructura tu prompt con:
     - Contexto del Proyecto
     - Requisitos
     - Restricciones
     - Escala
     - Necesidades de Seguridad/Cumplimiento
   - Visualiza los resultados detallados del análisis

## Prompts de Prueba de Ejemplo:

### 1. Plataforma de Negociación Financiera
"Necesitamos construir una plataforma de negociación de alta frecuencia que procese flujos de datos de mercado, ejecute operaciones con latencia inferior al milisegundo, mantenga registros de auditoría y maneje cálculos de riesgo complejos. El sistema debe estar distribuido globalmente, manejar 100,000 transacciones por segundo y tener capacidades robustas de recuperación ante desastres."
### 2. Plataforma SaaS Multiusuario
"Diseña una plataforma SaaS multiusuario para la planificación de recursos empresariales que necesite admitir la personalización por inquilino, manejar diferentes requisitos de residencia de datos, admitir capacidades sin conexión y mantener el aislamiento del rendimiento entre inquilinos. El sistema debe escalar a 10,000 usuarios concurrentes y admitir integraciones personalizadas."

## Notas

- Requiere claves API de DeepSeek y Anthropic
- Proporciona análisis en tiempo real con explicaciones detalladas
- Admite interacción basada en chat
- Incluye un razonamiento claro para todas las decisiones arquitectónicas
- Se aplican costos de uso de API


