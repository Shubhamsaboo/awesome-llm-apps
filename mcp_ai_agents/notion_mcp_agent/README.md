# 📑 Agente MCP para Notion

Un Agente de Notion basado en terminal para interactuar con tus páginas de Notion usando lenguaje natural a través del servidor MCP (Model Context Protocol) de Notion.

## Características

- Interactúa con las páginas de Notion a través de una interfaz de línea de comandos
- Realiza operaciones de actualización, inserción y recuperación en tus páginas de Notion
- Crea y edita bloques, listas, tablas y otras estructuras de Notion
- Agrega comentarios a los bloques
- Busca información específica
- Recuerda el contexto de la conversación para interacciones de varios turnos
- Gestión de sesiones para conversaciones persistentes

## Requisitos Previos

- Python 3.9+
- Una cuenta de Notion con permisos de administrador
- Un token de Integración de Notion
- Una clave API de OpenAI

## Instalación

1. Clona el repositorio
2. Instala los paquetes de Python requeridos:

```bash
pip install -r requirements.txt
```

3. Instala el servidor MCP de Notion (se hará automáticamente cuando ejecutes la aplicación)

## Configurando la Integración de Notion

### Creando una Integración de Notion

1. Ve a [Integraciones de Notion](https://www.notion.so/my-integrations)
2. Haz clic en "Nueva integración"
3. Nombra tu integración (p. ej., "Asistente de Notion")
4. Selecciona las capacidades necesarias (Leer y Escribir contenido)
5. Envía y copia tu "Token de Integración Interno"

### Compartiendo tu Página de Notion con la Integración

1. Abre tu página de Notion
2. Haz clic en los tres puntos (⋮) en la esquina superior derecha de la página
3. Selecciona "Agregar conexiones" del menú desplegable
4. Busca el nombre de tu integración en el cuadro de búsqueda
5. Haz clic en tu integración para agregarla a la página
6. Confirma haciendo clic en "Confirmar" en el diálogo que aparece

Alternativamente, también puedes compartir a través del botón "Compartir":
1. Haz clic en "Compartir" en la esquina superior derecha
2. En el diálogo de compartir, busca el nombre de tu integración (precedido por "@")
3. Haz clic en tu integración para agregarla
4. Haz clic en "Invitar" para otorgarle acceso a tu página

Ambos métodos otorgarán a tu integración acceso completo a la página y su contenido.

### Encontrando el ID de tu Página de Notion

1. Abre tu página de Notion en un navegador
2. Copia la URL, que se parece a:
   `https://www.notion.so/workspace/Tu-Pagina-1f5b8a8ba283...`
3. El ID es la parte después del último guion y antes de cualquier parámetro de consulta
   Ejemplo: `1f5b8a8bad058a7e39a6`

## Configuración

Puedes configurar el agente usando variables de entorno:

- `NOTION_API_KEY`: Tu token de Integración de Notion
- `OPENAI_API_KEY`: Tu clave API de OpenAI
- `NOTION_PAGE_ID`: El ID de tu página de Notion

Alternativamente, puedes establecer estos valores directamente en el script.

## Uso

Ejecuta el agente desde la línea de comandos:

```bash
python notion_mcp_agent.py
```

Cuando inicies el agente, te pedirá que ingreses el ID de tu página de Notion. Puedes:
1. Ingresar el ID de tu página en el prompt
2. Presionar Enter sin escribir nada para usar el ID de página predeterminado (si está configurado)
3. Proporcionar el ID de la página directamente como un argumento de línea de comandos (omitiendo el prompt):

```bash
python notion_mcp_agent.py tu-id-de-pagina-aqui
```

### Flujo de Conversación

Cada vez que inicias el agente, crea un ID de usuario y un ID de sesión únicos para mantener el contexto de la conversación. Esto permite que el agente recuerde interacciones previas y continúe conversaciones coherentes incluso después de cerrar y reiniciar la aplicación.

Puedes salir de la conversación en cualquier momento escribiendo `exit`, `quit`, `bye` o `goodbye`.

## Consultas de Ejemplo

- "¿Qué hay en mi página de Notion?"
- "Agregar un nuevo párrafo que diga 'Notas de la reunión de hoy'"
- "Crear una lista con viñetas con tres elementos: Manzana, Plátano, Naranja"
- "Agregar un comentario al primer párrafo que diga '¡Esto se ve bien!'"
- "Buscar cualquier mención de reuniones"
- "Resumir nuestra conversación hasta ahora"

## Licencia

MIT