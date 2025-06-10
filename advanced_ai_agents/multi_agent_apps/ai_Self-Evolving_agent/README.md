<!-- Add logo here -->
<div align="center">
  <a href="https://github.com/EvoAgentX/EvoAgentX">
    <img src="./assets/EAXLoGo.svg" alt="EvoAgentX" width="50%">
  </a>
</div>

<h2 align="center">
    Construyendo un Ecosistema Autoevolutivo de Agentes de IA
</h2>

<div align="center">

[![EvoAgentX Homepage](https://img.shields.io/badge/EvoAgentX-Homepage-blue?logo=homebridge)](https://evoagentx.org/)
[![Docs](https://img.shields.io/badge/-Documentation-0A66C2?logo=readthedocs&logoColor=white&color=7289DA&labelColor=grey)](https://EvoAgentX.github.io/EvoAgentX/)
[![Discord](https://img.shields.io/badge/Chat-Discord-5865F2?&logo=discord&logoColor=white)](https://discord.gg/SUEkfTYn)
[![Twitter](https://img.shields.io/badge/Follow-@EvoAgentX-e3dee5?&logo=x&logoColor=white)](https://x.com/EvoAgentX)
[![Wechat](https://img.shields.io/badge/WeChat-EvoAgentX-brightgreen?logo=wechat&logoColor=white)](./assets/wechat_info.md)
[![GitHub star chart](https://img.shields.io/github/stars/EvoAgentX/EvoAgentX?style=social)](https://star-history.com/#EvoAgentX/EvoAgentX)
[![GitHub fork](https://img.shields.io/github/forks/EvoAgentX/EvoAgentX?style=social)](https://github.com/EvoAgentX/EvoAgentX/fork)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?)](https://github.com/EvoAgentX/EvoAgentX/blob/main/LICENSE)
<!-- [![EvoAgentX Homepage](https://img.shields.io/badge/EvoAgentX-Homepage-blue?logo=homebridge)](https://EvoAgentX.github.io/EvoAgentX/) -->
<!-- [![hf_space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-EvoAgentX-ffc107?color=ffc107&logoColor=white)](https://huggingface.co/EvoAgentX) -->
</div>

<div align="center">

<h3 align="center">

<a href="./README.md" style="text-decoration: underline;">English</a> | <a href="./README-zh.md">简体中文</a>

</h3>

</div>

<h4 align="center">
  <i>Un framework automatizado para evaluar y evolucionar flujos de trabajo agénticos.</i>
</h4>

<p align="center">
  <img src="./assets/framework_en.jpg">
</p>


## 🔥 Últimas Noticias
- **[Mayo 2025]** 🎉 ¡**EvoAgentX** ha sido lanzado oficialmente!

## ⚡ Empezar
- [🔥 Últimas Noticias](#-latest-news)
- [⚡ Empezar](#-get-started)
- [Instalación](#installation)
- [Configuración de LLM](#llm-configuration)
  - [Configuración de Clave API](#api-key-configuration)
  - [Configurar y Usar el LLM](#configure-and-use-the-llm)
- [Generación Automática de Flujo de Trabajo](#automatic-workflow-generation)
- [Video de Demostración](#demo-video)
  - [✨ Resultados Finales](#-final-results)
- [Algoritmos de Evolución](#evolution-algorithms)
  - [📊 Resultados](#-results)
- [Aplicaciones](#applications)
- [Tutorial y Casos de Uso](#tutorial-and-use-cases)
- [🎯 Hoja de Ruta](#-roadmap)
- [🙋 Soporte](#-support)
  - [Únete a la Comunidad](#join-the-community)
  - [Información de Contacto](#contact-information)
- [🙌 Contribuir a EvoAgentX](#-contributing-to-evoagentx)
- [📚 Agradecimientos](#-acknowledgements)
- [📄 Licencia](#-license)

## Instalación

Recomendamos instalar EvoAgentX usando `pip`:

```bash
pip install git+https://github.com/EvoAgentX/EvoAgentX.git
```

Para desarrollo local o configuración detallada (p. ej., usando conda), consulta la [Guía de Instalación para EvoAgentX](./docs/installation.md).

<details>
<summary>Ejemplo (opcional, para desarrollo local):</summary>

```bash
git clone https://github.com/EvoAgentX/EvoAgentX.git
cd EvoAgentX
# Crear un nuevo entorno conda
conda create -n evoagentx python=3.10

# Activar el entorno
conda activate evoagentx

# Instalar el paquete
pip install -r requirements.txt
# O instalar en modo de desarrollo
pip install -e .
```
</details>

## Configuración de LLM

### Configuración de Clave API

Para usar LLMs con EvoAgentX (p. ej., OpenAI), debes configurar tu clave API.

<details>
<summary>Opción 1: Establecer Clave API mediante Variable de Entorno</summary>

- Linux/macOS: 
```bash
export OPENAI_API_KEY=<your-openai-api-key>
```

- Símbolo del sistema de Windows:
```cmd 
set OPENAI_API_KEY=<your-openai-api-key>
```

- Windows PowerShell:
```powershell
$env:OPENAI_API_KEY="<your-openai-api-key>" # Se requieren comillas "
```

Una vez establecida, puedes acceder a la clave en tu código Python con:
```python
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```
</details>

<details>
<summary>Opción 2: Usar Archivo .env</summary>

- Crea un archivo .env en la raíz de tu proyecto y agrega lo siguiente:
```bash
OPENAI_API_KEY=<your-openai-api-key>
```

Luego cárgalo en Python:
```python
from dotenv import load_dotenv 
import os 

load_dotenv() # Carga variables de entorno desde el archivo .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```
</details>
<!-- > 🔐 Consejo: No olvides agregar `.env` a tu `.gitignore` para evitar confirmar secretos. -->

### Configurar y Usar el LLM
Una vez establecida la clave API, inicializa el LLM con:

```python
from evoagentx.models import OpenAILLMConfig, OpenAILLM

# Cargar la clave API desde el entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Definir la configuración del LLM
openai_config = OpenAILLMConfig(
    model="gpt-4o-mini",       # Especificar el nombre del modelo
    openai_key=OPENAI_API_KEY, # Pasar la clave directamente
    stream=True,               # Habilitar respuesta en streaming
    output_response=True       # Imprimir respuesta en stdout
)

# Inicializar el modelo de lenguaje
llm = OpenAILLM(config=openai_config)

# Generar una respuesta desde el LLM
response = llm.generate(prompt="¿Qué es un Flujo de Trabajo Agéntico?")
```
> 📖 Más detalles sobre modelos compatibles y opciones de configuración: [Guía del módulo LLM](./docs/modules/llm.md).


## Generación Automática de Flujo de Trabajo
Una vez configurada tu clave API y tu modelo de lenguaje, puedes generar y ejecutar automáticamente flujos de trabajo multiagente en EvoAgentX.

🧩 Pasos Centrales:
1. Define un objetivo en lenguaje natural
2. Genera el flujo de trabajo con `WorkFlowGenerator`
3. Instancia agentes usando `AgentManager`
4. Ejecuta el flujo de trabajo mediante `WorkFlow`

💡 Ejemplo Mínimo:
```python
from evoagentx.workflow import WorkFlowGenerator, WorkFlowGraph, WorkFlow
from evoagentx.agents import AgentManager

goal = "Generar código html para el juego Tetris"
workflow_graph = WorkFlowGenerator(llm=llm).generate_workflow(goal)

agent_manager = AgentManager()
agent_manager.add_agents_from_workflow(workflow_graph, llm_config=openai_config)

workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
output = workflow.execute()
print(output)
```

También puedes:
- 📊 Visualizar el flujo de trabajo: `workflow_graph.display()`
- 💾 Guardar/cargar flujos de trabajo: `save_module()` / `from_file()`

> 📂 Para un ejemplo funcional completo, consulta [`workflow_demo.py`](https://github.com/EvoAgentX/EvoAgentX/blob/main/examples/workflow_demo.py)


## Video de Demostración


[![Watch on YouTube](https://img.shields.io/badge/-Watch%20on%20YouTube-red?logo=youtube&labelColor=grey)](https://www.youtube.com/watch?v=Wu0ZydYDqgg)

<div align="center">
  <video src="https://github.com/user-attachments/assets/8f65d1af-9398-40c3-a625-4f493e13e5a5.mp4" autoplay loop muted playsinline width="600">
    Tu navegador no soporta la etiqueta de video.
  </video>
</div>

En esta demostración, mostramos las capacidades de generación y ejecución de flujos de trabajo de EvoAgentX a través de dos ejemplos:

- Aplicación 1: Recomendación Inteligente de Empleo a partir de un Currículum
- Aplicación 2: Análisis Visual de Acciones del Mercado A


### ✨ Resultados Finales

<table>
  <tr>
    <td align="center">
      <img src="./assets/demo_result_1.png" width="400"><br>
      <strong>Aplicación&nbsp;1:</strong><br>Recomendación de Empleo
    </td>
    <td align="center">
      <img src="./assets/demo_result_2.jpeg" width="400"><br>
      <strong>Aplicación&nbsp;2:</strong><br>Análisis Visual de Acciones
    </td>
  </tr>
</table>

## Algoritmos de Evolución

Hemos integrado algunos algoritmos de evolución de agentes/flujos de trabajo existentes en EvoAgentX, incluyendo [TextGrad](https://www.nature.com/articles/s41586-025-08661-4), [MIPRO](https://arxiv.org/abs/2406.11695) y [AFlow](https://arxiv.org/abs/2410.10762).

Para evaluar el rendimiento, los utilizamos para optimizar el mismo sistema de agentes en tres tareas diferentes: QA de múltiples saltos (HotPotQA), generación de código (MBPP) y razonamiento (MATH). Muestreamos aleatoriamente 50 ejemplos para validación y otros 100 ejemplos para prueba.

> Consejo: Hemos integrado este benchmark y código de evaluación en EvoAgentX. Consulta el [tutorial de benchmark y evaluación](https://github.com/EvoAgentX/EvoAgentX/blob/main/docs/tutorial/benchmark_and_evaluation.md) para más detalles.

### 📊 Resultados

| Método   | HotPotQA<br>(F1%) | MBPP<br>(Pass@1 %) | MATH<br>(Tasa de Resolución %) |
|----------|--------------------|---------------------|--------------------------|
| Original | 63.58              | 69.00               | 66.00                    |
| TextGrad | 71.02              | 71.00               | 76.00                    |
| AFlow    | 65.09              | 79.00               | 71.00                    |
| MIPRO    | 69.16              | 68.00               | 72.30       

Consulta la carpeta `examples/optimization` para más detalles.

## Aplicaciones

Utilizamos nuestro framework para optimizar sistemas multiagente existentes en el benchmark [GAIA](https://huggingface.co/spaces/gaia-benchmark/leaderboard). Seleccionamos [Open Deep Research](https://github.com/huggingface/smolagents/tree/main/examples/open_deep_research) y [OWL](https://github.com/camel-ai/owl), dos frameworks multiagente representativos del leaderboard de GAIA que son de código abierto y ejecutables.

Aplicamos EvoAgentX para optimizar sus prompts. El rendimiento de los agentes optimizados en el conjunto de validación del benchmark GAIA se muestra en la siguiente figura.

<table>
  <tr>
    <td align="center" width="50%">
      <img src="./assets/open_deep_research_optimization_report.png" alt="Open Deep Research Optimization" width="100%"><br>
      <strong>Open Deep Research</strong>
    </td>
    <td align="center" width="50%">
      <img src="./assets/owl_optimization_result.png" alt="OWL Optimization" width="100%"><br>
      <strong>Agente OWL</strong>
    </td>
  </tr>
</table>

> Informes Completos de Optimización: [Open Deep Research](https://github.com/eax6/smolagents) y [OWL](https://github.com/TedSIWEILIU/owl).

## Tutorial y Casos de Uso

> 💡 **¿Nuevo en EvoAgentX?** Comienza con la [Guía de Inicio Rápido](./docs/quickstart.md) para una introducción paso a paso.


Explora cómo usar EvoAgentX eficazmente con los siguientes recursos:

| Recetario | Descripción |
|:---|:---|
| **[Construye tu Primer Agente](./docs/tutorial/first_agent.md)** | Crea y gestiona rápidamente agentes con capacidades multiacción. |
| **[Construye tu Primer Flujo de Trabajo](./docs/tutorial/first_workflow.md)** | Aprende a construir flujos de trabajo colaborativos con múltiples agentes. |
| **[Generación Automática de Flujo de Trabajo](./docs/quickstart.md#automatic-workflow-generation-and-execution)** | Genera automáticamente flujos de trabajo a partir de objetivos en lenguaje natural. |
| **[Tutorial de Benchmark y Evaluación](./docs/tutorial/benchmark_and_evaluation.md)** | Evalúa el rendimiento de los agentes utilizando conjuntos de datos de benchmark. |
| **[Tutorial del Optimizador TextGrad](./docs/tutorial/textgrad_optimizer.md)** | Optimiza automáticamente los prompts dentro del flujo de trabajo multiagente con TextGrad. |
| **[Tutorial del Optimizador AFlow](./docs/tutorial/aflow_optimizer.md)** | Optimiza automáticamente tanto los prompts como la estructura del flujo de trabajo multiagente con AFlow. |
<!-- | **[Tutorial del Optimizador SEW](./docs/tutorial/sew_optimizer.md)** | Crea SEW (Flujos de Trabajo Autoevolutivos) para mejorar los sistemas de agentes. | -->

🛠️ Sigue los tutoriales para construir y optimizar tus flujos de trabajo de EvoAgentX.

🚀 Estamos trabajando activamente en expandir nuestra biblioteca de casos de uso y estrategias de optimización. **Más próximamente — ¡mantente atento!**

## 🎯 Hoja de Ruta
- [ ] **Modularizar Algoritmos de Evolución**: Abstraer algoritmos de optimización en módulos plug-and-play que puedan integrarse fácilmente en flujos de trabajo personalizados.
- [ ] **Desarrollar Plantillas de Tareas y Módulos de Agentes**: Construir plantillas reutilizables para tareas típicas y componentes de agentes estandarizados para agilizar el desarrollo de aplicaciones.
- [ ] **Integrar Algoritmos de Agentes Autoevolutivos**: Incorporar algoritmos de autoevolución de agentes más recientes y avanzados en múltiples dimensiones, incluyendo ajuste de prompts, estructuras de flujo de trabajo y módulos de memoria.
- [ ] **Habilitar Interfaz Visual de Edición de Flujos de Trabajo**: Proporcionar una interfaz visual para la visualización y edición de la estructura de flujos de trabajo para mejorar la usabilidad y la depuración.



## 🙋 Soporte

### Únete a la Comunidad

📢 ¡Mantente conectado y sé parte del viaje de **EvoAgentX**!
🚩 Únete a nuestra comunidad para obtener las últimas actualizaciones, compartir tus ideas y colaborar con entusiastas de la IA de todo el mundo.

- [Discord](https://discord.gg/SUEkfTYn) — Chatea, discute y colabora en tiempo real.
- [X (anteriormente Twitter)](https://x.com/EvoAgentX) — Síguenos para noticias, actualizaciones y conocimientos.
- [WeChat](https://github.com/EvoAgentX/EvoAgentX/blob/main/assets/wechat_info.md) — Conéctate con nuestra comunidad china.

### Información de Contacto

Si tienes alguna pregunta o comentario sobre este proyecto, no dudes en contactarnos. ¡Apreciamos mucho tus sugerencias!

- **Correo electrónico:** evoagentx.ai@gmail.com

Responderemos a todas las preguntas en un plazo de 2-3 días hábiles.

## 🙌 Contribuir a EvoAgentX
Gracias a estos increíbles contribuidores

<a href="https://github.com/EvoAgentX/EvoAgentX/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=EvoAgentX/EvoAgentX" />
</a>

Apreciamos tu interés en contribuir a nuestra iniciativa de código abierto. Proporcionamos un documento de [directrices de contribución](https://github.com/EvoAgentX/EvoAgentX/blob/main/CONTRIBUTING.md) que describe los pasos para contribuir a EvoAgentX. Consulta esta guía para asegurar una colaboración fluida y contribuciones exitosas. 🤝🚀

[![Star History Chart](https://api.star-history.com/svg?repos=EvoAgentX/EvoAgentX&type=Date)](https://www.star-history.com/#EvoAgentX/EvoAgentX&Date)


## 📚 Agradecimientos
Este proyecto se basa en varios proyectos de código abierto destacados: [AFlow](https://github.com/FoundationAgents/MetaGPT/tree/main/metagpt/ext/aflow), [TextGrad](https://github.com/zou-group/textgrad), [DSPy](https://github.com/stanfordnlp/dspy), [LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench), y más. Nos gustaría agradecer a los desarrolladores y mantenedores de estos frameworks por sus valiosas contribuciones a la comunidad de código abierto.

## 📄 Licencia

El código fuente en este repositorio está disponible bajo la [Licencia MIT](./LICENSE).
