## 💬 Chatea con Repositorio de GitHub

Aplicación LLM con RAG para chatear con un Repositorio de GitHub en solo 30 líneas de código Python. La aplicación utiliza Generación Aumentada por Recuperación (RAG) para proporcionar respuestas precisas a preguntas basadas en el contenido del repositorio de GitHub especificado.

### Características

- Proporciona el nombre del Repositorio de GitHub como entrada
- Haz preguntas sobre el contenido del repositorio de GitHub
- Obtén respuestas precisas utilizando la API de OpenAI y Embedchain

### ¿Cómo Empezar?

1. Clona el repositorio de GitHub

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd advanced_llm_apps/chat_with_X_tutorials/chat_with_github
```
2. Instala las dependencias requeridas:

```bash
pip install -r requirements.txt
```
3. Obtén tu Clave API de OpenAI

- Regístrate para obtener una [cuenta de OpenAI](https://platform.openai.com/) (o el proveedor de LLM de tu elección) y obtén tu clave API.

4. Obtén tu Token de Acceso de GitHub

- Crea un [token de acceso personal](https://docs.github.com/en/enterprise-server@3.6/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token) con los permisos necesarios para acceder al repositorio de GitHub deseado.

4. Ejecuta la Aplicación Streamlit
```bash
streamlit run chat_github.py
```

### ¿Cómo Funciona?

- La aplicación solicita al usuario que ingrese su clave API de OpenAI, que se utiliza para autenticar las solicitudes a la API de OpenAI.

- Inicializa una instancia de la clase Embedchain App y un GithubLoader con el Token de Acceso de GitHub proporcionado.

- Se solicita al usuario que ingrese la URL de un repositorio de GitHub, que luego se agrega a la base de conocimientos de la aplicación Embedchain utilizando GithubLoader.

- El usuario puede hacer preguntas sobre el repositorio de GitHub utilizando la entrada de texto.

- Cuando se hace una pregunta, la aplicación utiliza el método de chat de la aplicación Embedchain para generar una respuesta basada en el contenido del repositorio de GitHub.

- La aplicación muestra la respuesta generada al usuario.
