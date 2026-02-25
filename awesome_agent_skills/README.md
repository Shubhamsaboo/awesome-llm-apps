# Awesome Agent Skills

A curated collection of skills for AI agents following the [Agent Skills](https://agentskills.io) format.

## What Are Agent Skills?

Agent Skills are packaged instructions and scripts that extend agent capabilities. They follow the [Agent Skills specification](https://agentskills.io/specification) - a simple, open format for giving agents new capabilities and expertise.

Each skill contains:
- **SKILL.md** - Instructions for the agent
- **scripts/** - Helper scripts for automation (optional)
- **references/** - Supporting documentation (optional)

## Available Skills

### 🖥️ Coding

| Skill | Description |
|-------|-------------|
| [python-expert](python-expert/) | Senior Python developer with focus on clean, maintainable code |
| [code-reviewer](code-reviewer/) | Thorough code review with security and performance focus |
| [debugger](debugger/) | Systematic debugging and root cause analysis |
| [fullstack-developer](fullstack-developer/) | Modern web development (React, Node.js, databases) |

### 🔍 Research

| Skill | Description |
|-------|-------------|
| [deep-research](deep-research/) | Multi-source research with citations and synthesis |
| [fact-checker](fact-checker/) | Verify claims and identify misinformation |
| [academic-researcher](academic-researcher/) | Literature review and academic writing |

### ✍️ Writing

| Skill | Description |
|-------|-------------|
| [technical-writer](technical-writer/) | Clear documentation and technical content |
| [content-creator](content-creator/) | Engaging blog posts and social media content |
| [editor](editor/) | Professional editing and proofreading |

### 📋 Planning

| Skill | Description |
|-------|-------------|
| [project-planner](project-planner/) | Break down projects into actionable tasks |
| [sprint-planner](sprint-planner/) | Agile sprint planning and estimation |
| [strategy-advisor](strategy-advisor/) | High-level strategic thinking and business decisions |

### 📊 Data Analysis

| Skill | Description |
|-------|-------------|
| [data-analyst](data-analyst/) | SQL, pandas, and statistical analysis |
| [visualization-expert](visualization-expert/) | Chart selection and data visualization |

### ⚡ Productivity

| Skill | Description |
|-------|-------------|
| [email-drafter](email-drafter/) | Professional email composition |
| [meeting-notes](meeting-notes/) | Structured meeting summaries with action items |
| [decision-helper](decision-helper/) | Structured decision-making frameworks |

### 🏭 Operations (by [Evos](https://github.com/ai-evos/agent-skills))

| Skill | Description |
|-------|-------------|
| [logistics-exception-management](logistics-exception-management/) | Freight exceptions, shipment delays, damage claims, and carrier disputes |
| [carrier-relationship-management](carrier-relationship-management/) | Carrier selection, rate negotiation, scorecarding, and portfolio strategy |
| [customs-trade-compliance](customs-trade-compliance/) | HS classification, trade documentation, duty optimization, and sanctions screening |
| [inventory-demand-planning](inventory-demand-planning/) | Demand forecasting, safety stock optimization, and promotional planning |
| [returns-reverse-logistics](returns-reverse-logistics/) | Returns processing, disposition decisions, fraud detection, and vendor recovery |
| [production-scheduling](production-scheduling/) | Finite capacity scheduling, changeover optimization, and disruption response |
| [quality-nonconformance](quality-nonconformance/) | NCR lifecycle, root cause analysis, CAPA management, and SPC interpretation |
| [energy-procurement](energy-procurement/) | Energy pricing, procurement strategies, demand charge management, and renewables |

## Installation

### Using npx (Recommended)

```bash
npx skills add shubhamsaboo/awesome-agent-skills
```

### Manual Installation

Clone or download individual skill directories and reference them in your agent's configuration.

## Usage

Skills are automatically available once installed. Agents use them when relevant tasks are detected based on the skill's description and triggers.

### Examples

When you ask your agent:
- **"Review this React component for performance"** → Triggers `code-reviewer` skill
- **"Research the benefits of intermittent fasting"** → Triggers `deep-research` skill  
- **"Help me debug this Python function"** → Triggers `debugger` skill
- **"Draft an email to decline a meeting"** → Triggers `email-drafter` skill

### Integration with Agent Products

Agent Skills work with any skills-compatible agent product. Examples:

- **Claude Desktop / claude.ai** - Upload SKILL.md files to project knowledge
- **Cursor / VSCode** - Reference skills in `.cursorrules` or custom instructions
- **Custom agents** - Load SKILL.md content as system prompts or agent instructions
- **AI frameworks** - Use with LangChain, AutoGen, or custom agent frameworks

## Skill Structure

Each skill follows the [Agent Skills specification](https://agentskills.io/specification):

```
skill-name/
├── SKILL.md          # Required: Instructions for the agent
├── scripts/          # Optional: Helper scripts
├── references/       # Optional: Supporting documentation
└── assets/          # Optional: Images, templates, etc.
```

### SKILL.md Format

```yaml
---
name: skill-name
description: |
  What the skill does and when to use it.
  Include triggers like "use when debugging" or "when user mentions code review".
license: MIT
metadata:
  author: awesome-llm-apps
  version: "1.0.0"
---

# Skill Name

Instructions for the agent to follow...
```

## Creating Your Own Skills

1. Create a new directory with your skill name (lowercase, hyphens only)
2. Add a `SKILL.md` file with YAML frontmatter
3. Write clear, actionable instructions for the agent
4. (Optional) Add supporting scripts or reference materials

See the [Agent Skills specification](https://agentskills.io/specification) for complete details.

## Contributing

We welcome contributions! To add a new skill:

1. Fork the repository
2. Create a new skill directory following the specification
3. Ensure SKILL.md has proper YAML frontmatter
4. Include clear instructions and examples
5. Submit a pull request

## Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [Agent Skills Documentation](https://agentskills.io)
- [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) - Official examples
- [Anthropic Skills](https://github.com/anthropics/skills) - More examples
