# 🎧 Agente de Tour de Audio Autoguiado con IA

Un sistema de agente de voz conversacional que genera tours de audio autoguiados inmersivos basados en la **ubicación**, **áreas de interés** y **duración del tour** del usuario. Construido sobre una arquitectura multiagente utilizando el SDK de Agentes de OpenAI, recuperación de información en tiempo real y TTS expresivo para una salida de voz natural.

---

## 🚀 Características

### 🎙️ Arquitectura Multiagente

- **Agente Orquestador**
  Coordina el flujo general del tour, gestiona las transiciones y ensambla el contenido de todos los agentes expertos.

- **Agente de Historia**
  Entrega narrativas históricas perspicaces con una voz autorizada.

- **Agente de Arquitectura**
  Destaca detalles arquitectónicos, estilos y elementos de diseño utilizando un tono descriptivo y técnico.

- **Agente de Cultura**
  Explora costumbres locales, tradiciones y patrimonio artístico con una voz entusiasta.

- **Agente Culinario**
  Describe platos icónicos y cultura gastronómica en un tono apasionado y atractivo.

---

### 📍 Generación de Contenido Consciente de la Ubicación

- Generación dinámica de contenido basada en la **ubicación** ingresada por el usuario
- **Integración de búsqueda web** en tiempo real para obtener detalles relevantes y actualizados
- Entrega de contenido personalizado filtrado por las **categorías de interés** del usuario

---

### ⏱️ Duración del Tour Personalizable

- Duración del tour seleccionable: **15, 30 o 60 minutos**
- Las asignaciones de tiempo se adaptan a los pesos de interés del usuario y la relevancia de la ubicación
- Asegura narrativas bien espaciadas y proporcionadas en todas las secciones

---

### 🔊 Salida de Voz Expresiva

- Audio de alta calidad generado usando **Gpt-4o Mini Audio**

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd ai_agent_tutorials/ai_audio_tour_agent
```
2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```
3. Obtén tu Clave API de OpenAI

- Regístrate para obtener una [cuenta de OpenAI](https://platform.openai.com/) (o el proveedor de LLM de tu elección) y obtén tu clave API.

4. Ejecuta la Aplicación Streamlit
```bash
streamlit run ai_audio_tour_agent.py
```

