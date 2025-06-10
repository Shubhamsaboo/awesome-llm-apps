## 🌍 Agente MCP Planificador de Viajes de IA

Esta es una aplicación basada en Streamlit que ayuda a los usuarios a planificar sus itinerarios de viaje utilizando IA. La aplicación se integra con varios servidores mcp para proporcionar una experiencia integral de planificación de viajes, incluyendo pronósticos del tiempo, mapas e integración de calendario.

## Características

### Integración de Servidores MCP

Este proyecto utiliza varios servidores MCP (Model Context Protocol) para proporcionar una experiencia integral de planificación de viajes:

### 1. Servidor MCP del Clima
- **Funcionalidad**: Proporciona datos meteorológicos y pronósticos en tiempo real

### 2. Servidor MCP de Mapas
- **Funcionalidad**: Maneja servicios basados en la ubicación y navegación
- **Características**:
  - Buscar lugares y puntos de interés
  - Obtener información detallada del lugar
  - Recuperar direcciones de conducción/peatonales

### 3. Servidor MCP de Calendario
- **Funcionalidad**: Gestiona eventos de calendario y programación
- **Características**:
  - Crear y gestionar eventos de calendario
  - Manejar conversiones de zona horaria
  - Programar recordatorios y notificaciones
- **Integración**: Implementado en `calendar_mcp.py`

### 4. Servidor MCP de Reservas
- **Funcionalidad**: Servidor MCP de Airbnb utilizado


## Configuración

### Requisitos

1. **Claves API y Credenciales**:
    - **Clave API de Google Maps**: Configura una Clave API de Google Maps desde Google Cloud Console
    - **API de Google Calendar**: Habilita y configura la Clave API de Calendar
    - **Credenciales OAuth de Google**: ID de Cliente y Secreto de Cliente y Token de Actualización para autenticación
    - **Clave API de AccuWeather**: Obtén la clave API de AccuWeather en https://developer.accuweather.com/
    - **Clave API de OpenAI**: Regístrate en OpenAI para obtener tu clave API.

2. **Python 3.8+**: Asegúrate de tener instalado Python 3.8 o superior.

### Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/yourusername/ai_travel_planner_mcp_agent_team
   cd ai_travel_planner_mcp_agent_team
   ```

2. Instala los paquetes de Python requeridos:
   ```bash
   pip install -r requirements.txt
   ```

3. Configura las variables de entorno:
   Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
   ```
   GOOGLE_CLIENT_ID=
   GOOGLE_CLIENT_SECRET=
   GOOGLE_REFRESH_TOKEN=
   GOOGLE_MAPS_API_KEY=
   OPENAI_API_KEY=
   ACCUWEATHER_API_KEY=
   ```

### Ejecutando la Aplicación

1. Genera el token OAuth para Google Calendar

2. Inicia la aplicación Streamlit:
   ```bash
   streamlit run app.py
   ```

3. En la interfaz de la aplicación:
   - Usa la barra lateral para configurar tus preferencias
   - Ingresa los detalles de tu viaje

## Estructura del Proyecto

- `app.py`: Aplicación principal de Streamlit
- `calendar_mcp.py`: Funcionalidad de integración mcp de calendario
- `requirements.txt`: Dependencias del proyecto
- `.env`: Variables de entorno

## Integración MCP de Calendario

El módulo `calendar_mcp.py` proporciona una integración perfecta con Google Calendar a través del framework MCP (Model Context Protocol). Esta integración permite al planificador de viajes:

- **Crear Eventos**: Crear automáticamente eventos de calendario para actividades de viaje, vuelos y alojamientos
- **Gestión de Horarios**: Manejar conversiones de zona horaria y conflictos de programación
- **Detalles del Evento**: Incluir información completa del evento como:
  - Detalles de ubicación con enlaces de Google Maps
  - Pronósticos del tiempo para la hora del evento
  - Duración del viaje y detalles de transporte
  - Notas y recordatorios

### Configuración del Calendario

1. **Autenticación OAuth**:
   - La aplicación utiliza OAuth 2.0 para una autenticación segura con Google Calendar
   - La configuración por primera vez requiere la generación de un token de actualización
   - Los tokens de actualización se almacenan de forma segura en el archivo `.env`

2. **Creación de Eventos**:
   ```python
   # Ejemplo de creación de un evento de calendario
   event = {
       'summary': 'Vuelo a París',
       'location': 'Aeropuerto Charles de Gaulle',
       'description': 'Detalles del vuelo y pronóstico del tiempo',
       'start': {'dateTime': '2024-04-20T10:00:00', 'timeZone': 'Europe/Paris'},
       'end': {'dateTime': '2024-04-20T12:00:00', 'timeZone': 'Europe/Paris'}
   }
   ```
