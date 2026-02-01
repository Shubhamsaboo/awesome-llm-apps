# 🎯 Awesome Agent Skills

A curated collection of system prompts and skills for AI agents. These skills help AI assistants become more effective at specific tasks.

## What Are Agent Skills?

Agent Skills are structured instructions that enhance AI capabilities for specific domains. They're like "superpowers" you can give to AI assistants to make them experts in particular areas.

**Why use Skills?**
- 🎯 **Focused expertise**: Transform a general AI into a domain specialist
- 📋 **Consistency**: Get reliable, structured outputs every time  
- ⚡ **Efficiency**: Skip repetitive prompting—skills remember best practices
- 🔄 **Reusability**: Share skills across projects and teams

## How to Use These Skills

### Option 1: Direct Prompting
Copy the skill content and paste it at the start of your conversation:

```
[Paste skill content here]

Now, help me with: [your task]
```

### Option 2: System Prompt
If your AI platform supports system prompts, add the skill there for persistent behavior.

### Option 3: With AI Coding Agents
For tools like Claude Code, Cursor, or Windsurf:

1. Create a `SKILLS.md` or `.cursorrules` file in your project
2. Paste relevant skills
3. The agent will automatically follow these guidelines

### Option 4: Agent Frameworks
For LangChain, AutoGen, CrewAI, or similar frameworks:

```python
from langchain.agents import AgentExecutor

# Load skill as system message
skill_prompt = open("agent_skills/coding/python_expert.md").read()

agent = AgentExecutor(
    system_message=skill_prompt,
    # ... other config
)
```

## 📁 Skill Categories

### 🖥️ [Coding](./coding/)
Skills for software development, code review, debugging, and architecture.

| Skill | Description |
|-------|-------------|
| [Python Expert](./coding/python_expert.md) | Senior Python developer with focus on clean, maintainable code |
| [Code Reviewer](./coding/code_reviewer.md) | Thorough code review with security and performance focus |
| [Debugger](./coding/debugger.md) | Systematic debugging and root cause analysis |
| [Full Stack Developer](./coding/fullstack_developer.md) | Modern web development across the stack |

### 🔍 [Research](./research/)
Skills for information gathering, synthesis, and analysis.

| Skill | Description |
|-------|-------------|
| [Deep Research](./research/deep_research.md) | Multi-source research with citations and synthesis |
| [Fact Checker](./research/fact_checker.md) | Verify claims and identify misinformation |
| [Academic Researcher](./research/academic_researcher.md) | Literature review and academic writing |

### ✍️ [Writing](./writing/)
Skills for content creation, editing, and communication.

| Skill | Description |
|-------|-------------|
| [Technical Writer](./writing/technical_writer.md) | Clear documentation and technical content |
| [Content Creator](./writing/content_creator.md) | Engaging blog posts and social content |
| [Editor](./writing/editor.md) | Professional editing and proofreading |

### 📋 [Planning](./planning/)
Skills for project management, strategy, and task breakdown.

| Skill | Description |
|-------|-------------|
| [Project Planner](./planning/project_planner.md) | Break down projects into actionable steps |
| [Sprint Planner](./planning/sprint_planner.md) | Agile sprint planning and estimation |
| [Strategy Advisor](./planning/strategy_advisor.md) | High-level strategic thinking and advice |

### 📊 [Data Analysis](./data_analysis/)
Skills for working with data, visualization, and insights.

| Skill | Description |
|-------|-------------|
| [Data Analyst](./data_analysis/data_analyst.md) | SQL, pandas, and data exploration |
| [Visualization Expert](./data_analysis/visualization_expert.md) | Charts, dashboards, and visual storytelling |

### ⚡ [Productivity](./productivity/)
Skills for personal effectiveness and workflow optimization.

| Skill | Description |
|-------|-------------|
| [Email Drafter](./productivity/email_drafter.md) | Professional email composition |
| [Meeting Notes](./productivity/meeting_notes.md) | Structured meeting summaries and action items |
| [Decision Helper](./productivity/decision_helper.md) | Structured decision-making frameworks |

## 🎨 Creating Your Own Skills

### Skill Structure

A good skill includes:

```markdown
# Skill Name

## Role
Who the AI should act as.

## Expertise
Specific knowledge areas.

## Approach
How to handle tasks (methodology).

## Output Format
Expected structure of responses.

## Examples (Optional)
Sample inputs and outputs.

## Constraints
What NOT to do.
```

### Best Practices

1. **Be specific**: Vague instructions lead to vague outputs
2. **Include examples**: Show don't just tell
3. **Set boundaries**: Define what's out of scope
4. **Use structure**: Consistent formatting helps the AI parse instructions
5. **Test iteratively**: Refine based on actual outputs

## 🤝 Contributing

We welcome contributions! To add a new skill:

1. Fork this repository
2. Create your skill in the appropriate category folder
3. Follow the skill structure template
4. Test with at least 3 different scenarios
5. Submit a pull request

## 📚 Resources

- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [OpenAI Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)
- [Google Gemini Prompting](https://ai.google.dev/gemini-api/docs/prompting-intro)

## 📜 License

These skills are open source under the Apache 2.0 license. Use them freely in your projects!

---

**⭐ Found these useful? Star the repo and share with others!**
