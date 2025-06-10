
# 💔 Equipo de Agentes para la Recuperación de Rupturas

Esta es una aplicación impulsada por IA diseñada para ayudar a los usuarios a recuperarse emocionalmente de las rupturas proporcionando apoyo, orientación y mensajes de desahogo emocional de un equipo de agentes de IA especializados. La aplicación está construida usando **Streamlit** y **Agno**, aprovechando **Gemini 2.0 Flash (Google Vision Model)   **.

## 🚀 Características

- 🧠 **Equipo Multi-Agente:**
    - **Agente Terapeuta:** Ofrece apoyo empático y estrategias de afrontamiento.
    - **Agente de Cierre:** Escribe mensajes emocionales que los usuarios no deberían enviar para la catarsis.
    - **Agente Planificador de Rutinas:** Sugiere rutinas diarias para la recuperación emocional.
    - **Agente de Honestidad Brutal:** Proporciona retroalimentación directa y sin rodeos sobre la ruptura.
- 📷 **Análisis de Capturas de Pantalla de Chat:**
    - Sube capturas de pantalla para el análisis del chat.
- 🔑 **Gestión de Claves API:**
    - Almacena y gestiona tus claves API de Gemini de forma segura a través de la barra lateral de Streamlit.
- ⚡ **Ejecución Paralela:**
    - Los agentes procesan las entradas en modo de coordinación para obtener resultados completos.
- ✅ **Interfaz Fácil de Usar:**
    - Interfaz de usuario simple e intuitiva con fácil interacción y visualización de las respuestas de los agentes.

---

## 🛠️ Tecnologías Utilizadas

- **Frontend:** Streamlit (Python)
- **Modelos de IA:** Gemini 2.0 Flash (Google Vision Model)
- **Procesamiento de Imágenes:** PIL (para mostrar capturas de pantalla)
- **Extracción de Texto:** Modelo Gemini Vision de Google para analizar capturas de pantalla de chat
- **Variables de Entorno:** Claves API gestionadas con `st.session_state` en Streamlit

---

## 📦 Instalación

1. **Clona el Repositorio:**
   ```bash
   git clone <repository_url>
   cd breakup-recovery-agent-team
   ```

2. **Crea un Entorno Virtual (Opcional pero Recomendado):**
   ```bash
   conda create --name <env_name> python=<version>
   conda activate <env_name>
   ```

3. **Instala las Dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecuta la Aplicación Streamlit:**
   ```bash
   streamlit run app.py
   ```

---

## 🔑 Variables de Entorno

Asegúrate de proporcionar tu **clave API de Gemini** en la barra lateral de Streamlit:

- GEMINI_API_KEY=your_google_gemini_api_key

---

## 🛠️ Uso

1. **Ingresa Tus Sentimientos:**
    - Describe cómo te sientes en el área de texto.
2. **Sube una Captura de Pantalla (Opcional):**
    - Sube una captura de pantalla del chat (PNG, JPG, JPEG) para su análisis.
3. **Ejecuta los Agentes:**
    - Haz clic en **"Obtener Apoyo para la Recuperación"** para ejecutar el equipo multi-agente.
4. **Visualiza los Resultados:**
    - Se muestran las respuestas individuales de los agentes.
    - El Líder del Equipo proporciona un resumen final.

---

## 🧑‍💻 Resumen de los Agentes

- **Agente Terapeuta**
    - Proporciona apoyo empático y estrategias de afrontamiento.
    - Utiliza herramientas **Gemini 2.0 Flash (Google Vision Model)** y DuckDuckGo para obtener información.
  
- **Agente de Cierre**
    - Genera mensajes emocionales no enviados para la liberación emocional.
    - Asegura mensajes sinceros y auténticos.

- **Agente Planificador de Rutinas**
    - Crea una rutina diaria de recuperación con actividades equilibradas.
    - Incluye autorreflexión, interacción social y distracciones saludables.

- **Agente de Honestidad Brutal**
    - Ofrece retroalimentación directa y objetiva sobre la ruptura.
    - Utiliza un lenguaje factual sin endulzar la realidad.

---


## 📄 Licencia

Este proyecto está licenciado bajo la **Licencia MIT**.

---
