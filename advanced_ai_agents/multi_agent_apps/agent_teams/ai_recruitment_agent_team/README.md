# 💼 Equipo de Agentes de Reclutamiento de IA

Una aplicación de Streamlit que simula un equipo de reclutamiento de servicio completo utilizando múltiples agentes de IA para automatizar y optimizar el proceso de contratación. Cada agente representa un rol de especialista en reclutamiento diferente, desde el análisis de currículums y la evaluación de candidatos hasta la programación de entrevistas y la comunicación, trabajando juntos para proporcionar soluciones de contratación integrales. El sistema combina la experiencia de reclutadores técnicos, coordinadores de recursos humanos y especialistas en programación en un flujo de trabajo automatizado y cohesivo.

## Características

#### Agentes de IA Especializados

- Agente Reclutador Técnico: Analiza currículums y evalúa habilidades técnicas
- Agente de Comunicación: Maneja la correspondencia profesional por correo electrónico
- Agente Coordinador de Programación: Gestiona la programación y coordinación de entrevistas
- Cada agente tiene experiencia específica y colabora para un reclutamiento integral


#### Proceso de Reclutamiento de Extremo a Extremo
- Selección y análisis automatizado de currículums
- Evaluación técnica específica del rol
- Comunicación profesional con el candidato
- Programación automatizada de entrevistas
- Sistema de retroalimentación integrado

## Cosas Importantes que Hacer Antes de Ejecutar la Aplicación

- Crear/Usar una nueva cuenta de Gmail para el reclutador
- Habilitar la verificación en 2 pasos y generar una contraseña de aplicación para la cuenta de Gmail
- La contraseña de aplicación es un código de 16 dígitos (usar sin espacios) que debe generarse aquí - [Contraseña de Aplicación de Google](https://support.google.com/accounts/answer/185833?hl=es) Por favor, sigue los pasos para generar la contraseña - tendrá el formato - 'afec wejf awoj fwrv' (elimina los espacios e ingrésala en la aplicación de Streamlit)
- Crear/Usar una cuenta de Zoom e ir al Zoom App Marketplace para obtener las credenciales de la API:
[Zoom Marketplace](https://marketplace.zoom.us)
- Ir al Panel de Desarrolladores y crear una nueva aplicación - Seleccionar OAuth de Servidor a Servidor y obtener las credenciales. Verás 3 credenciales: ID de Cliente, Secreto de Cliente e ID de Cuenta
- Después de eso, necesitas agregar algunos ámbitos a la aplicación, para que el enlace de Zoom del candidato se envíe y se cree a través del correo.
- Los Ámbitos son meeting:write:invite_links:admin, meeting:write:meeting:admin, meeting:write:meeting:master, meeting:write:invite_links:master, meeting:write:open_app:admin, user:read:email:admin, user:read:list_users:admin, billing:read:user_entitlement:admin, dashboard:read:list_meeting_participants:admin [los últimos 3 son opcionales]

## Cómo Ejecutar

1. **Configurar el Entorno**
   ```bash
   # Clona el repositorio
    git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
    cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_recruitment_agent_team
    
   # Instala las dependencias
   pip install -r requirements.txt
   ```

2. **Configurar Claves API**
   - Clave API de OpenAI para acceso a GPT-4o
   - Credenciales de la API de Zoom (ID de Cuenta, ID de Cliente, Secreto de Cliente)
   - Contraseña de Aplicación de Correo Electrónico del Correo del Reclutador

3. **Ejecutar la Aplicación**
   ```bash
   streamlit run ai_recruitment_agent_team.py
   ```

## Componentes del Sistema

- **Agente Analizador de Currículums**
  - Algoritmo de coincidencia de habilidades
  - Verificación de experiencia
  - Evaluación técnica
  - Toma de decisiones de selección

- **Agente de Comunicación por Correo Electrónico**
  - Redacción profesional de correos electrónicos
  - Notificaciones automatizadas
  - Comunicación de retroalimentación
  - Gestión de seguimiento

- **Agente Programador de Entrevistas**
  - Coordinación de reuniones de Zoom
  - Gestión de calendarios
  - Manejo de zonas horarias
  - Sistema de recordatorios

- **Experiencia del Candidato**
  - Interfaz de carga simple
  - Retroalimentación en tiempo real
  - Comunicación clara
  - Proceso optimizado

## Stack Tecnológico

- **Framework**: Phidata
- **Modelo**: OpenAI GPT-4o
- **Integración**: API de Zoom, Herramienta EmailTools de Phidata
- **Procesamiento de PDF**: PyPDF2
- **Gestión del Tiempo**: pytz
- **Gestión de Estado**: Streamlit Session State


## Descargo de Responsabilidad

Esta herramienta está diseñada para ayudar en el proceso de reclutamiento, pero no debe reemplazar completamente el juicio humano en las decisiones de contratación. Todas las decisiones automatizadas deben ser revisadas por reclutadores humanos para su aprobación final.

## Mejoras Futuras

- Integración con sistemas ATS
- Puntuación avanzada de candidatos
- Capacidades de entrevista en video
- Integración de evaluación de habilidades
- Soporte multilingüe
