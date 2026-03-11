<!-- Add logo here -->
<div align="center">
  <a href="https://github.com/EvoAgentX/EvoAgentX">
    <img src="./assets/EAXLoGo.svg" alt="EvoAgentX" width="50%">
  </a>
</div>

<h2 align="center">
    Building a Self-Evolving Ecosystem of AI Agents
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
  <i>An automated framework for evaluating and evolving agentic workflows.</i>
</h4>

<p align="center">
  <img src="./assets/framework_en.jpg">
</p>


## 🔥 Latest News
- **[May 2025]** 🎉 **EvoAgentX** has been officially released!

## ⚡ Get Started
- [🔥 Latest News](#-latest-news)
- [⚡ Get Started](#-get-started)
- [Installation](#installation)
- [LLM Configuration](#llm-configuration)
  - [API Key Configuration](#api-key-configuration)
  - [Configure and Use the LLM](#configure-and-use-the-llm)
- [Automatic WorkFlow Generation](#automatic-workflow-generation)
- [Demo Video](#demo-video)
  - [✨ Final Results](#-final-results)
- [Evolution Algorithms](#evolution-algorithms)
  - [📊 Results](#-results)
- [Applications](#applications)
- [Tutorial and Use Cases](#tutorial-and-use-cases)
- [🎯 Roadmap](#-roadmap)
- [🙋 Support](#-support)
  - [Join the Community](#join-the-community)
  - [Contact Information](#contact-information)
- [🙌 Contributing to EvoAgentX](#-contributing-to-evoagentx)
- [📚 Acknowledgements](#-acknowledgements)
- [📄 License](#-license)

## Installation

We recommend installing EvoAgentX using `pip`:

```bash
pip install git+https://github.com/EvoAgentX/EvoAgentX.git
```

For local development or detailed setup (e.g., using conda), refer to the [Installation Guide for EvoAgentX](./docs/installation.md).

<details>
<summary>Example (optional, for local development):</summary>

```bash
git clone https://github.com/EvoAgentX/EvoAgentX.git
cd EvoAgentX
# Create a new conda environment
conda create -n evoagentx python=3.10

# Activate the environment
conda activate evoagentx

# Install the package
pip install -r requirements.txt
# OR install in development mode
pip install -e .
```
</details>

## LLM Configuration

### API Key Configuration 

To use LLMs with EvoAgentX (e.g., OpenAI), you must set up your API key.

<details>
<summary>Option 1: Set API Key via Environment Variable</summary> 

- Linux/macOS: 
```bash
export OPENAI_API_KEY=<your-openai-api-key>
```

- Windows Command Prompt: 
```cmd 
set OPENAI_API_KEY=<your-openai-api-key>
```

-  Windows PowerShell:
```powershell
$env:OPENAI_API_KEY="<your-openai-api-key>" # " is required 
```

Once set, you can access the key in your Python code with:
```python
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```
</details>

<details>
<summary>Option 2: Use .env File</summary> 

- Create a .env file in your project root and add the following:
```bash
OPENAI_API_KEY=<your-openai-api-key>
```

Then load it in Python:
```python
from dotenv import load_dotenv 
import os 

load_dotenv() # Loads environment variables from .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```
</details>
<!-- > 🔐 Tip: Don't forget to add `.env` to your `.gitignore` to avoid committing secrets. -->

### Configure and Use the LLM
Once the API key is set, initialise the LLM with:

```python
from evoagentx.models import OpenAILLMConfig, OpenAILLM

# Load the API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Define LLM configuration
openai_config = OpenAILLMConfig(
    model="gpt-4o-mini",       # Specify the model name
    openai_key=OPENAI_API_KEY, # Pass the key directly
    stream=True,               # Enable streaming response
    output_response=True       # Print response to stdout
)

# Initialize the language model
llm = OpenAILLM(config=openai_config)

# Generate a response from the LLM
response = llm.generate(prompt="What is Agentic Workflow?")
```
> 📖 More details on supported models and config options: [LLM module guide](./docs/modules/llm.md).


## Automatic WorkFlow Generation 
Once your API key and language model are configured, you can automatically generate and execute multi-agent workflows in EvoAgentX.

🧩 Core Steps:
1. Define a natural language goal
2. Generate the workflow with `WorkFlowGenerator`
3. Instantiate agents using `AgentManager`
4. Execute the workflow via `WorkFlow`

💡 Minimal Example:
```python
from evoagentx.workflow import WorkFlowGenerator, WorkFlowGraph, WorkFlow
from evoagentx.agents import AgentManager

goal = "Generate html code for the Tetris game"
workflow_graph = WorkFlowGenerator(llm=llm).generate_workflow(goal)

agent_manager = AgentManager()
agent_manager.add_agents_from_workflow(workflow_graph, llm_config=openai_config)

workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
output = workflow.execute()
print(output)
```

You can also:
- 📊 Visualise the workflow: `workflow_graph.display()`
- 💾 Save/load workflows: `save_module()` / `from_file()`

> 📂 For a complete working example, check out the [`workflow_demo.py`](https://github.com/EvoAgentX/EvoAgentX/blob/main/examples/workflow_demo.py)


## Demo Video


[![Watch on YouTube](https://img.shields.io/badge/-Watch%20on%20YouTube-red?logo=youtube&labelColor=grey)](https://www.youtube.com/watch?v=Wu0ZydYDqgg)

<div align="center">
  <video src="https://github.com/user-attachments/assets/8f65d1af-9398-40c3-a625-4f493e13e5a5.mp4" autoplay loop muted playsinline width="600">
    Your browser does not support the video tag.
  </video>
</div>

In this demo, we showcase the workflow generation and execution capabilities of EvoAgentX through two examples:

- Application 1: Intelligent Job Recommendation from Resume
- Application 2: Visual Analysis of A-Share Stocks


### ✨ Final Results

<table>
  <tr>
    <td align="center">
      <img src="./assets/demo_result_1.png" width="400"><br>
      <strong>Application&nbsp;1:</strong><br>Job Recommendation
    </td>
    <td align="center">
      <img src="./assets/demo_result_2.jpeg" width="400"><br>
      <strong>Application&nbsp;2:</strong><br>Stock Visual Analysis
    </td>
  </tr>
</table>

## Evolution Algorithms 

We have integrated some existing agent/workflow evolution algorithms into EvoAgentX, including [TextGrad](https://www.nature.com/articles/s41586-025-08661-4), [MIPRO](https://arxiv.org/abs/2406.11695) and [AFlow](https://arxiv.org/abs/2410.10762).

To evaluate the performance, we use them to optimize the same agent system on three different tasks: multi-hop QA (HotPotQA), code generation (MBPP) and reasoning (MATH). We randomly sample 50 examples for validation and other 100 examples for testing. 

> Tip: We have integrated these benchmark and evaluation code in EvoAgentX. Please refer to the [benchmark and evaluation tutorial](https://github.com/EvoAgentX/EvoAgentX/blob/main/docs/tutorial/benchmark_and_evaluation.md) for more details.

### 📊 Results 

| Method   | HotPotQA<br>(F1%) | MBPP<br>(Pass@1 %) | MATH<br>(Solve Rate %) |
|----------|--------------------|---------------------|--------------------------|
| Original | 63.58              | 69.00               | 66.00                    |
| TextGrad | 71.02              | 71.00               | 76.00                    |
| AFlow    | 65.09              | 79.00               | 71.00                    |
| MIPRO    | 69.16              | 68.00               | 72.30       

Please refer to the `examples/optimization` folder for more details. 

## Applications 

We use our framework to optimize existing multi-agent systems on the [GAIA](https://huggingface.co/spaces/gaia-benchmark/leaderboard) benchmark. We select [Open Deep Research](https://github.com/huggingface/smolagents/tree/main/examples/open_deep_research) and [OWL](https://github.com/camel-ai/owl), two representative multi-agent framework from the GAIA leaderboard that is open-source and runnable. 

We apply EvoAgentX to optimize their prompts. The performance of the optimized agents on the GAIA benchmark validation set is shown in the figure below.

<table>
  <tr>
    <td align="center" width="50%">
      <img src="./assets/open_deep_research_optimization_report.png" alt="Open Deep Research Optimization" width="100%"><br>
      <strong>Open Deep Research</strong>
    </td>
    <td align="center" width="50%">
      <img src="./assets/owl_optimization_result.png" alt="OWL Optimization" width="100%"><br>
      <strong>OWL Agent</strong>
    </td>
  </tr>
</table>

> Full Optimization Reports: [Open Deep Research](https://github.com/eax6/smolagents) and [OWL](https://github.com/TedSIWEILIU/owl).  

## Tutorial and Use Cases

> 💡 **New to EvoAgentX?** Start with the [Quickstart Guide](./docs/quickstart.md) for a step-by-step introduction.


Explore how to effectively use EvoAgentX with the following resources:

| Cookbook | Description |
|:---|:---|
| **[Build Your First Agent](./docs/tutorial/first_agent.md)** | Quickly create and manage agents with multi-action capabilities. |
| **[Build Your First Workflow](./docs/tutorial/first_workflow.md)** | Learn to build collaborative workflows with multiple agents. |
| **[Automatic Workflow Generation](./docs/quickstart.md#automatic-workflow-generation-and-execution)** | Automatically generate workflows from natural language goals. |
| **[Benchmark and Evaluation Tutorial](./docs/tutorial/benchmark_and_evaluation.md)** | Evaluate agent performance using benchmark datasets. |
| **[TextGrad Optimizer Tutorial](./docs/tutorial/textgrad_optimizer.md)** | Automatically optimise the prompts within multi-agent workflow with TextGrad. |
| **[AFlow Optimizer Tutorial](./docs/tutorial/aflow_optimizer.md)** | Automatically optimise both the prompts and structure of multi-agent workflow with AFlow. |
<!-- | **[SEW Optimizer Tutorial](./docs/tutorial/sew_optimizer.md)** | Create SEW (Self-Evolving Workflows) to enhance agent systems. | -->

🛠️ Follow the tutorials to build and optimize your EvoAgentX workflows.

🚀 We're actively working on expanding our library of use cases and optimization strategies. **More coming soon — stay tuned!**

## 🎯 Roadmap
- [ ] **Modularize Evolution Algorithms**: Abstract optimization algorithms into plug-and-play modules that can be easily integrated into custom workflows. 
- [ ] **Develop Task Templates and Agent Modules**: Build reusable templates for typical tasks and standardized agent components to streamline application development.
- [ ] **Integrate Self-Evolving Agent Algorithms**: Incorporate more recent and advanced agent self-evolution across multiple dimensions, including prompt tuning, workflow structures, and memory modules. 
- [ ] **Enable Visual Workflow Editing Interface**: Provide a visual interface for workflow structure display and editing to improve usability and debugging. 



## 🙋 Support

### Join the Community

📢 Stay connected and be part of the **EvoAgentX** journey!  
🚩 Join our community to get the latest updates, share your ideas, and collaborate with AI enthusiasts worldwide.

- [Discord](https://discord.gg/SUEkfTYn) — Chat, discuss, and collaborate in real-time.
- [X (formerly Twitter)](https://x.com/EvoAgentX) — Follow us for news, updates, and insights.
- [WeChat](https://github.com/EvoAgentX/EvoAgentX/blob/main/assets/wechat_info.md) — Connect with our Chinese community.

### Contact Information

If you have any questions or feedback about this project, please feel free to contact us. We highly appreciate your suggestions!

- **Email:** evoagentx.ai@gmail.com

We will respond to all questions within 2-3 business days.

## 🙌 Contributing to EvoAgentX
Thanks go to these awesome contributors

<a href="https://github.com/EvoAgentX/EvoAgentX/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=EvoAgentX/EvoAgentX" />
</a>

We appreciate your interest in contributing to our open-source initiative. We provide a document of [contributing guidelines](https://github.com/EvoAgentX/EvoAgentX/blob/main/CONTRIBUTING.md) which outlines the steps for contributing to EvoAgentX. Please refer to this guide to ensure smooth collaboration and successful contributions. 🤝🚀

[![Star History Chart](https://api.star-history.com/svg?repos=EvoAgentX/EvoAgentX&type=Date)](https://www.star-history.com/#EvoAgentX/EvoAgentX&Date)


## 📚 Acknowledgements 
This project builds upon several outstanding open-source projects: [AFlow](https://github.com/FoundationAgents/MetaGPT/tree/main/metagpt/ext/aflow), [TextGrad](https://github.com/zou-group/textgrad), [DSPy](https://github.com/stanfordnlp/dspy), [LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench), and more. We would like to thank the developers and maintainers of these frameworks for their valuable contributions to the open-source community.

## 📄 License

Source code in this repository is made available under the [MIT License](./LICENSE).
