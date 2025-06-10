# 💻 Equipo de Agentes de Codificación de IA Multimodal con o3-mini y Gemini
Una aplicación de Streamlit impulsada por IA que sirve como tu asistente personal de codificación, impulsada por múltiples Agentes construidos sobre el nuevo modelo o3-mini. También puedes subir una imagen de un problema de codificación o describirlo en texto, y el agente de IA lo analizará, generará una solución óptima y la ejecutará en un entorno sandbox.

## Características
#### Entrada de Problemas Multimodal
- Sube imágenes de problemas de codificación (admite PNG, JPG, JPEG)
- Escribe problemas en lenguaje natural
- Extracción automática de problemas de imágenes
- Procesamiento interactivo de problemas

#### Generación Inteligente de Código
- Generación de soluciones óptimas con la mejor complejidad de tiempo/espacio
- Salida de código Python limpio y documentado
- Sugerencias de tipo y documentación adecuada
- Manejo de casos extremos

#### Ejecución Segura de Código
- Entorno de ejecución de código en sandbox
- Resultados de ejecución en tiempo real
- Manejo de errores y explicaciones
- Protección de tiempo de espera de ejecución de 30 segundos

#### Arquitectura Multiagente
- Agente de Visión (Gemini-2.0-flash) para procesamiento de imágenes
- Agente de Codificación (OpenAI- o3-mini) para generación de soluciones
- Agente de Ejecución (OpenAI) para ejecución de código y análisis de resultados
- Sandbox E2B para ejecución segura de código

## Cómo Ejecutar

Sigue los pasos a continuación para configurar y ejecutar la aplicación:
- Obtén una clave API de OpenAI desde: https://platform.openai.com/
- Obtén una clave API de Google (Gemini) desde: https://makersuite.google.com/app/apikey
- Obtén una clave API de E2B desde: https://e2b.dev/docs/getting-started/api-key

1. **Clona el Repositorio**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_coding_agent_team
   ```

2. **Instala las dependencias**
    ```bash
    pip install -r requirements.txt
    ```

3. **Ejecuta la aplicación Streamlit**
    ```bash
    streamlit run ai_coding_agent_o3.py
    ```

4. **Configura las Claves API**
   - Ingresa tus claves API en la barra lateral
   - Se requieren las tres claves (OpenAI, Gemini, E2B) para una funcionalidad completa

## Uso
1. Sube una imagen de un problema de codificación O escribe la descripción de tu problema
2. Haz clic en "Generar y Ejecutar Solución"
3. Visualiza la solución generada con documentación completa
4. Consulta los resultados de la ejecución y cualquier archivo generado
5. Revisa cualquier mensaje de error o tiempos de espera de ejecución
