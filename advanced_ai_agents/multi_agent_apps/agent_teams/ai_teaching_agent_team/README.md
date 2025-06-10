# 👨‍🏫 Equipo de Agentes de Enseñanza de IA

Una aplicación de Streamlit que reúne a un equipo de agentes de enseñanza de IA especializados que colaboran como un cuerpo docente profesional. Cada agente actúa como un educador especializado: un diseñador de currículos, un experto en rutas de aprendizaje, un bibliotecario de recursos y un instructor de práctica, trabajando juntos para crear una experiencia educativa completa a través de Google Docs.

## 🪄 Conoce a tu Equipo de Agentes de Enseñanza de IA

#### 🧠 Agente Profesor
- Crea una base de conocimientos fundamental en Google Docs
- Organiza el contenido con encabezados y secciones adecuados
- Incluye explicaciones detalladas y ejemplos
- Resultado: Documento completo de base de conocimientos con tabla de contenido

#### 🗺️ Agente Asesor Académico
- Diseña la ruta de aprendizaje en un documento estructurado de Google Doc
- Crea marcadores de hitos progresivos
- Incluye estimaciones de tiempo y requisitos previos
- Resultado: Documento de hoja de ruta visual con rutas de progresión claras

#### 📚 Agente Bibliotecario de Investigación
- Compila recursos en un documento organizado de Google Doc
- Incluye enlaces a artículos académicos y tutoriales
- Agrega descripciones y niveles de dificultad
- Resultado: Lista de recursos categorizada con calificaciones de calidad

#### ✍️ Agente Asistente de Enseñanza
- Desarrolla ejercicios en un documento interactivo de Google Doc
- Crea secciones de práctica estructuradas
- Incluye guías de soluciones
- Resultado: Cuaderno de trabajo de práctica completo con respuestas


## Cómo Ejecutar

1. Clona el repositorio
  ```bash
   # Clona el repositorio
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd ai_agent_tutorials/ai_personal_learning_agent

   # Instala las dependencias
   pip install -r requirements.txt
   ```

## Configuración - PASO IMPORTANTE

1. Obtén tu Clave API de OpenAI
- Crea una cuenta en [OpenAI Platform](https://platform.openai.com/)
- Navega a la sección de Claves API
- Crea una nueva clave API

2. Obtén tu Clave API de Composio
- Crea una cuenta en [Composio Platform](https://composio.ai/)
- **IMPORTANTE** - Para que puedas usar la aplicación, necesitas crear una nueva ID de conexión con Google Docs y Composio. Sigue los dos pasos a continuación para hacerlo:
  - `composio add googledocs` (EN LA TERMINAL)
  - Crea una nueva conexión
  - Selecciona OAUTH2
  - Selecciona Cuenta de Google y Listo.
  - En el sitio web de la cuenta de Composio, ve a aplicaciones, selecciona la herramienta Google Docs y [haz clic en crear integración](https://app.composio.dev/app/googledocs) (botón violeta) y haz clic en el botón "Try connecting default’s googldocs" y listo.

3. Regístrate y obtén la [Clave API de SerpAPI](https://serpapi.com/)

## ¿Cómo Usar?

1. Inicia la aplicación Streamlit
```bash
streamlit run teaching_agent_team.py
```

2. Usa la aplicación
- Ingresa tu clave API de OpenAI en la barra lateral (si no está configurada en el entorno)
- Ingresa tu clave API de Composio en la barra lateral
- Escribe un tema sobre el que quieras aprender (p. ej., "Programación en Python", "Aprendizaje Automático")
- Haz clic en "Generar Plan de Aprendizaje"
- Espera a que los agentes generen tu plan de aprendizaje personalizado
- Visualiza los resultados y la salida de la terminal en la interfaz
