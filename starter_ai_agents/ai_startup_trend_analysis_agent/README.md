## 📈 Agente de Análisis de Tendencias de Startups de IA
El Agente de Análisis de Tendencias de Startups de IA es una herramienta para emprendedores en ciernes que genera información procesable identificando tendencias incipientes, posibles brechas de mercado y oportunidades de crecimiento en sectores específicos. Los emprendedores pueden utilizar esta información basada en datos para validar ideas, detectar oportunidades de mercado y tomar decisiones informadas sobre sus empresas emergentes. Combina Newspaper4k y DuckDuckGo para escanear y analizar artículos centrados en startups y datos de mercado. Usando Claude 3.5 Sonnet, procesa esta información para extraer patrones emergentes y permitir a los emprendedores identificar oportunidades prometedoras para startups.


### Características
- **Indicación del Usuario**: Los emprendedores pueden ingresar sectores de startups específicos o tecnologías de interés para la investigación.
- **Recopilación de Noticias**: Este agente recopila noticias recientes sobre startups, rondas de financiación y análisis de mercado utilizando DuckDuckGo.
- **Generación de Resúmenes**: Se generan resúmenes concisos de información verificada utilizando Newspaper4k.
- **Análisis de Tendencias**: El sistema identifica patrones emergentes en la financiación de startups, la adopción de tecnología y las oportunidades de mercado en las historias analizadas.
- **Interfaz de Usuario Streamlit**: La aplicación cuenta con una interfaz fácil de usar construida con Streamlit para una fácil interacción.

### Cómo Empezar
1. **Clona el repositorio**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git 
   cd awesome-llm-apps/ai_agent_tutorials/ai_startup_trend_analysis_agent
   ```

2. **Crea y activa un entorno virtual**:
   ```bash
   # Para macOS/Linux
   python -m venv venv
   source venv/bin/activate

   # Para Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instala los paquetes requeridos**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecuta la aplicación**:
   ```bash
   streamlit run startup_trends_agent.py
   ```
### Nota Importante
- El sistema utiliza específicamente la API de Claude para el procesamiento avanzado del lenguaje. Puedes obtener tu clave API de Anthropic en el [sitio web de Anthropic](https://www.anthropic.com/api).


