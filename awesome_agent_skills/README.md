# Awesome Agent Skills

A curated collection of production-ready skills for AI agents and LLM applications.

## What Are Agent Skills?

Agent Skills are specialized prompts that transform a general-purpose AI into a domain expert. Each skill provides:

- 🎯 **Focused expertise** — Deep knowledge in a specific area
- 📋 **Consistent output** — Reliable, structured responses
- ⚡ **Quick integration** — Add capabilities in minutes
- 🔄 **Reusable patterns** — Works across projects

## Skills Collection

### 🖥️ Coding

| Skill | Description |
|-------|-------------|
| [python-expert](coding/python_expert.md) | Senior Python developer with focus on clean, maintainable code |
| [code-reviewer](coding/code_reviewer.md) | Thorough code review with security and performance focus |
| [debugger](coding/debugger.md) | Systematic debugging and root cause analysis |
| [fullstack-developer](coding/fullstack_developer.md) | Modern web development (React, Node.js, databases) |

### 🔍 Research

| Skill | Description |
|-------|-------------|
| [deep-research](research/deep_research.md) | Multi-source research with citations and synthesis |
| [fact-checker](research/fact_checker.md) | Verify claims and identify misinformation |
| [academic-researcher](research/academic_researcher.md) | Literature review and academic writing |

### ✍️ Writing

| Skill | Description |
|-------|-------------|
| [technical-writer](writing/technical_writer.md) | Clear documentation and technical content |
| [content-creator](writing/content_creator.md) | Engaging blog posts and social media content |
| [editor](writing/editor.md) | Professional editing and proofreading |

### 📋 Planning

| Skill | Description |
|-------|-------------|
| [project-planner](planning/project_planner.md) | Break down projects into actionable tasks |
| [sprint-planner](planning/sprint_planner.md) | Agile sprint planning and estimation |
| [strategy-advisor](planning/strategy_advisor.md) | High-level strategic thinking and business decisions |

### 📊 Data Analysis

| Skill | Description |
|-------|-------------|
| [data-analyst](data_analysis/data_analyst.md) | SQL, pandas, and statistical analysis |
| [visualization-expert](data_analysis/visualization_expert.md) | Chart selection and data visualization |

### ⚡ Productivity

| Skill | Description |
|-------|-------------|
| [email-drafter](productivity/email_drafter.md) | Professional email composition |
| [meeting-notes](productivity/meeting_notes.md) | Structured meeting summaries with action items |
| [decision-helper](productivity/decision_helper.md) | Structured decision-making frameworks |

## How to Use

### 1. Direct Prompting

Copy the skill content and paste it into your AI conversation as a system message.

### 2. OpenAI / Anthropic API

```python
from openai import OpenAI

client = OpenAI()

# Load skill from file
with open('awesome_agent_skills/coding/python_expert.md', 'r') as f:
    skill_content = f.read()

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": skill_content},
        {"role": "user", "content": "Write a function to merge two sorted lists"}
    ]
)
```

### 3. LangChain

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Load skill
with open('awesome_agent_skills/research/deep_research.md', 'r') as f:
    system_prompt = f.read()

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{input}")
])

chain = prompt | ChatOpenAI(model="gpt-4")
result = chain.invoke({"input": "Research the current state of quantum computing"})
```

### 4. AI Coding Assistants

Add skills to your project configuration:

**Cursor** (`.cursorrules`):
```
Include the content from awesome_agent_skills/coding/python_expert.md
```

**Claude Projects**:
Upload skill files to your project knowledge base.

## Skill Format

Each skill follows this structure:

```markdown
---
name: skill-name
description: Brief description of what the skill does.
---

# Skill Name

## When to use this skill
[Scenarios where this skill is helpful]

## How to Use this Skill
[Integration instructions with code examples]

### Parameters
[Input parameters the skill expects]

### Returns
[What output the skill provides]

## Example
[Input/output example]
```

## Contributing

We welcome contributions! To add a new skill:

1. Fork the repository
2. Create a new skill file in the appropriate category folder
3. Follow the skill format template above
4. Include practical examples
5. Submit a pull request

## License

MIT
