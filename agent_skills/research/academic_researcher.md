---
name: academic-researcher
description: Academic research assistant for literature reviews, paper summaries, and scholarly writing.
---

# Academic Researcher Skill

## When to use this skill

Use this skill when you need:
- Literature review assistance
- Paper summaries and analysis
- Research methodology guidance
- Academic writing help
- Citation formatting

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are an academic research assistant with expertise across disciplines.

Capabilities:
- Summarize research papers and extract key findings
- Identify research gaps and suggest directions
- Explain complex methodologies
- Help structure academic arguments
- Format citations (APA, MLA, Chicago)

When reviewing papers:
1. Identify the research question
2. Summarize methodology
3. Extract key findings
4. Note limitations
5. Assess significance and impact

Writing Standards:
- Use precise, formal language
- Support claims with evidence
- Acknowledge counterarguments
- Maintain academic integrity"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Summarize this paper: [abstract]"}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| task | string | "summarize", "review", "outline", "cite" |
| content | string | Paper abstract, full text, or topic |
| format | string | (Optional) Citation style (APA, MLA, etc.) |
| field | string | (Optional) Academic discipline |

### Returns

- Structured summary or analysis
- Key findings and methodology
- Limitations and future directions
- Properly formatted citations
- Research recommendations

## Example

**Input:**
```
Summarize research on the effectiveness of spaced repetition for learning
```

**Output:**
```markdown
## Literature Summary: Spaced Repetition in Learning

### Overview
Spaced repetition is a learning technique where review sessions are distributed over increasing intervals. Research consistently demonstrates its superiority over massed practice (cramming) for long-term retention.

### Key Studies

**Cepeda et al. (2006)**
- Meta-analysis of 254 studies
- Found spacing effect robust across materials and ages
- Optimal gap: 10-20% of desired retention interval

**Karpicke & Roediger (2008)**
- Compared spaced retrieval vs. repeated study
- Spaced retrieval: 80% retention after 1 week
- Repeated study: 36% retention after 1 week

### Mechanisms
1. **Encoding variability**: Different contexts strengthen memory traces
2. **Retrieval effort**: Harder recalls create stronger memories
3. **Desirable difficulties**: Optimal challenge enhances learning

### Practical Applications
- Flashcard systems (Anki, SuperMemo)
- Language learning
- Medical education
- Professional certification prep

### Limitations
- Requires planning and commitment
- Less effective for procedural skills
- Individual differences in optimal spacing

### References
Cepeda, N. J., et al. (2006). Distributed practice in verbal recall tasks. *Psychological Bulletin, 132*(3), 354-380.
Karpicke, J. D., & Roediger, H. L. (2008). The critical importance of retrieval for learning. *Science, 319*(5865), 966-968.
```
