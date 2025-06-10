## 📰 Asistente de noticias de IA multiagente
Esta aplicación de Streamlit implementa una sofisticada canalización de procesamiento de noticias utilizando múltiples agentes de IA especializados para buscar, sintetizar y resumir artículos de noticias. Aprovecha el modelo Llama 3.2 a través de Ollama y la búsqueda DuckDuckGo para proporcionar un análisis de noticias completo.


### Características
- Arquitectura multiagente con roles especializados:
    - Buscador de Noticias: Encuentra artículos de noticias recientes
    - Sintetizador de Noticias: Analiza y combina información
    - Resumidor de Noticias: Crea resúmenes concisos y profesionales

- Búsqueda de noticias en tiempo real utilizando DuckDuckGo
- Generación de resúmenes al estilo AP/Reuters
- Interfaz de Streamlit fácil de usar


### ¿Cómo Empezar?

1. Clona el repositorio de GitHub
```bash
git clone https://github.com/your-username/ai-news-processor.git
cd awesome-llm-apps/ai_agent_tutorials/local_news_agent_openai_swarm
```

2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```

3. Descarga y ejecuta Llama 3.2 usando Ollama:

```bash
# Descarga el modelo
ollama pull llama3.2

# Verifica la instalación
ollama list

# Ejecuta el modelo (prueba opcional)
ollama run llama3.2
```

4. Crea un archivo .env con tus configuraciones:
```bash
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=fake-key 
```
5. Ejecuta la aplicación Streamlit
```bash
streamlit run news_agent.py
```