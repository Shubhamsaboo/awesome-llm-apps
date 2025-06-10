# Vision RAG con Cohere Embed-4 🖼️

Un potente sistema de Generación Aumentada por Recuperación (RAG) visual que utiliza el modelo Embed-4 de última generación de Cohere para la incrustación multimodal y el eficiente modelo Gemini 2.5 Flash de Google para responder preguntas sobre imágenes y páginas PDF.

## Características

- **Búsqueda Multimodal**: Aprovecha Cohere Embed-4 para encontrar la imagen (o imagen de página PDF) semánticamente más relevante para una pregunta de texto dada.
- **Respuesta Visual a Preguntas**: Emplea Google Gemini 2.5 Flash para analizar el contenido de la imagen/página recuperada y generar respuestas precisas y conscientes del contexto.
- **Fuentes de Contenido Flexibles**:
    - Utiliza gráficos financieros e infografías de muestra precargados.
    - Sube tus propias imágenes personalizadas (PNG, JPG, JPEG).
    - **Sube documentos PDF**: Extrae automáticamente las páginas como imágenes para su análisis.
- **No se Requiere OCR**: Procesa directamente imágenes complejas y elementos visuales dentro de las páginas PDF sin necesidad de pasos separados de extracción de texto.
- **Interfaz de Usuario Interactiva**: Construida con Streamlit para una fácil interacción, incluyendo carga de contenido, entrada de preguntas y visualización de resultados.
- **Gestión de Sesiones**: Recuerda el contenido cargado/subido (imágenes y páginas PDF procesadas) dentro de una sesión.

## Requisitos

- Python 3.8+
- Clave API de Cohere
- Clave API de Google Gemini

## Cómo Ejecutar

Sigue estos pasos para configurar y ejecutar la aplicación:

1.  **Clona y Navega al Directorio** :
    ```bash
    git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
    cd awesome-llm-apps/rag_tutorials/vision_rag_agent
    ```

2.  **Instala las Dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Asegúrate de tener instalado el último `PyMuPDF` junto con otros requisitos)*

3.  **Configura tus claves API**:
    - Obtén una clave API de Cohere desde: [https://dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys)
    - Obtén una clave API de Google desde: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

4.  **Ejecuta la aplicación Streamlit**:
    ```bash
    streamlit run vision_rag.py
    ```

5.  **Accede a la Interfaz Web**:
    - Streamlit proporcionará una URL local (generalmente `http://localhost:8501`) en tu terminal.
    - Abre esta URL في tu navegador web.

## Cómo Funciona

La aplicación sigue un proceso RAG de dos etapas:

1.  **Recuperación**:
    - Cuando cargas imágenes de muestra o subes tus propias imágenes/PDF:
        - Las imágenes regulares se convierten a cadenas base64.
        - **Los PDF se procesan página por página**: Cada página se renderiza como una imagen, se guarda temporalmente y se convierte a una cadena base64.
    - El modelo `embed-v4.0` de Cohere (con `input_type="search_document"`) se utiliza para generar una incrustación vectorial densa para cada imagen o imagen de página PDF.
    - Cuando haces una pregunta, la consulta de texto se incrusta utilizando el mismo modelo `embed-v4.0` (con `input_type="search_query"`).
    - Se calcula la similitud del coseno entre la incrustación de la pregunta y todas las incrustaciones de imágenes.
    - La imagen con la puntuación de similitud más alta (que podría ser una imagen regular o una imagen de página PDF específica) se recupera como el contexto más relevante.

2.  **Generación**:
    - La pregunta de texto original y la imagen/imagen de página recuperada se pasan como entrada al modelo `gemini-2.5-flash-preview-04-17` de Google.
    - Gemini analiza el contenido de la imagen en el contexto de la pregunta y genera una respuesta textual.

## Uso

1.  Ingresa tus claves API de Cohere y Google en la barra lateral.
2.  Carga contenido:
    - Haz clic en **"Cargar Imágenes de Muestra"** para descargar y procesar los ejemplos incorporados.
    - *O/Y* Utiliza la sección **"Subir Tus Imágenes o PDF"** para subir tus propios archivos de imagen o PDF.
3.  Una vez que el contenido esté cargado y procesado (incrustaciones generadas), la sección **"Hacer una Pregunta"** se habilitará.
4.  Opcionalmente, expande **"Ver Imágenes Cargadas"** para ver miniaturas de todas las imágenes y páginas PDF procesadas actualmente en la sesión.
5.  Escribe tu pregunta sobre el contenido cargado en el campo de entrada de texto.
6.  Haz clic en **"Ejecutar Vision RAG"**.
7.  Visualiza los resultados:
    - La **Imagen/Página Recuperada** considerada más relevante para tu pregunta (el pie de foto indica el PDF de origen y el número de página si aplica).
    - La **Respuesta Generada** por Gemini basada en la imagen y la pregunta.

## Casos de Uso

- Analizar gráficos financieros y extraer cifras o tendencias clave.
- Responder preguntas específicas sobre diagramas, diagramas de flujo o infografías dentro de imágenes o PDF.
- Extraer información de tablas o texto dentro de capturas de pantalla o páginas PDF sin OCR explícito.
- Construir y consultar bases de conocimiento visuales (a partir de imágenes y PDF) utilizando lenguaje natural.
- Comprender el contenido de varios documentos visuales complejos, incluidos informes de varias páginas.

## Nota

- El procesamiento de imágenes y PDF (renderizado de página + incrustación) puede llevar tiempo, especialmente para muchos elementos o archivos grandes. Las imágenes de muestra se almacenan en caché después de la primera carga; el procesamiento de PDF actualmente ocurre en cada carga dentro de una sesión.
- Asegúrate de que tus claves API tengan los permisos y cuotas necesarios para los modelos Cohere y Gemini utilizados.
- La calidad de la respuesta depende tanto de la relevancia de la imagen recuperada como de la capacidad del modelo Gemini para interpretar la imagen en función de la pregunta.
