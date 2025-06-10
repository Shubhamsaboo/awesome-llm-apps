# 🚀 Agente de Inteligencia de Lanzamiento de Productos de IA

Un **centro de inteligencia optimizado** para equipos de Go-To-Market (GTM) y Marketing de Producto.
Construida con **Streamlit + Agno (GPT-4o) + Firecrawl**, la aplicación convierte datos dispersos de la web pública en información concisa y procesable sobre lanzamientos.

## 3 Agentes Especializados

| Pestaña | Qué Obtienes |
|-----|--------------|
| **Agente de Análisis de Competencia** | Desglose respaldado por evidencia de los últimos lanzamientos de un rival: posicionamiento, diferenciadores, indicios de precios y mezcla de canales |
| **Agente de Sentimiento del Mercado** | Conversaciones sociales consolidadas y temas de reseñas divididos por impulsores 🚀 *positivos* / ⚠️ *negativos* |
| **Agente de Métricas de Lanzamiento** | KPIs disponibles públicamente: cifras de adopción, cobertura de prensa, señales cualitativas de "rumor" |

Ventajas adicionales:

* 🔑 **Entrada de claves en la barra lateral** – ingresa las claves de OpenAI y Firecrawl de forma segura (type="password")
* 🧠 **Núcleo multiagente especializado** – tres agentes expertos colaboran para obtener información más rica
  * 🔍 Analista de Lanzamiento de Producto (estratega GTM)
  * 💬 Especialista en Sentimiento del Mercado (gurú de la percepción del consumidor)
  * 📈 Especialista en Métricas de Lanzamiento (analista de rendimiento)
* ⚡ **Acciones rápidas** – presiona **J/K/L** para activar los tres análisis sin tocar la interfaz de usuario
* 📑 **Informes Markdown autoformateados** – resumen con viñetas primero, luego análisis profundo expandido
* 🛠️ **Sección de fuentes** – cada informe termina con las URL que se rastrearon o buscaron

## 🛠️ Stack Tecnológico

| Capa | Detalles |
|-------|---------|
| Datos | API de búsqueda + rastreo asíncrono de **Firecrawl** |
| Agentes | **Agno** (GPT-4o) con FirecrawlTools |
| UI | **Streamlit** diseño amplio, flujo de trabajo con pestañas |
| LLM | **OpenAI GPT-4o** |

## 🚀 Inicio Rápido

1. **Clona** el repositorio

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent
```

2. **Instala** las dependencias

```bash
pip install -r requirements.txt
```

3. **Proporciona las claves API** (elige una opción)

   • **Variables de entorno** – crea un archivo `.env`:
   ```ini
   OPENAI_API_KEY=sk-************************
   FIRECRAWL_API_KEY=fc-************************
   ```
   • **Barra lateral en la aplicación** – pega las claves en las entradas de texto seguras

4. **Ejecuta la aplicación**

```bash
streamlit run product_launch_intelligence_agent.py
```

5. **Navega** a <http://localhost:8501> – deberías ver tres pestañas de análisis.

## 🕹️ Uso de la Aplicación

1. Ingresa las **claves API** en la barra lateral (o asegúrate de que estén en tu entorno).
2. Escribe una **empresa / producto / hashtag** en el cuadro de entrada principal.
3. Elige una pestaña y presiona el botón **Analizar** correspondiente – aparecerá un indicador giratorio mientras el agente trabaja.
4. Revisa el análisis de dos partes:
   * Lista con viñetas de los hallazgos clave
   * Informe expandido y ricamente formateado (tablas, destacados, recomendaciones)
