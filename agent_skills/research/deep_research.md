---
name: deep-research
description: Comprehensive research assistant that synthesizes information from multiple sources with citations.
---

# Deep Research Skill

## When to use this skill

Use this skill when you need:
- In-depth research on a topic
- Synthesis of multiple sources
- Properly cited information
- Balanced analysis of different viewpoints
- Research summaries with key findings

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are an expert researcher who provides thorough, well-cited analysis.

Research Process:
1. Clarify the research question
2. Identify key aspects to investigate
3. Gather information from multiple perspectives
4. Synthesize findings into coherent insights
5. Cite sources and note confidence levels

Output Format:
- Executive Summary (2-3 sentences)
- Key Findings (bulleted)
- Detailed Analysis (by topic)
- Sources & Citations
- Areas for Further Research

Citation Style:
- Use [1], [2], etc. for inline citations
- List full sources at the end
- Note if information is uncertain or contested"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Research the current state of quantum computing"}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| topic | string | Research question or topic |
| depth | string | (Optional) "overview", "detailed", or "comprehensive" |
| focus | string | (Optional) Specific angles to prioritize |
| sources | string | (Optional) Preferred source types |

### Returns

- Executive summary
- Key findings with citations
- Detailed analysis by subtopic
- Source list with credibility notes
- Gaps in current knowledge

## Example

**Input:**
```
Research the benefits and risks of intermittent fasting
```

**Output:**
```markdown
## Executive Summary

Intermittent fasting (IF) shows promising benefits for weight loss and metabolic health, though long-term effects remain under study. Most research supports its safety for healthy adults, with some populations requiring caution [1][2].

## Key Findings

- **Weight Loss**: IF is as effective as calorie restriction for weight loss [1]
- **Metabolic Health**: May improve insulin sensitivity by 20-31% [2]
- **Longevity**: Animal studies show promise; human data limited [3]
- **Risks**: Not recommended for pregnant women, diabetics without supervision, or those with eating disorder history [4]

## Detailed Analysis

### Weight Management
Studies comparing IF to traditional diets show similar weight loss results (5-8% body weight over 12 weeks). The main advantage is adherence—many find time-restricted eating easier to maintain than calorie counting [1].

### Metabolic Effects
Research indicates improvements in:
- Fasting insulin levels
- Blood pressure
- Inflammatory markers

However, effects vary significantly between individuals [2].

## Sources

[1] Varady KA, et al. "Clinical application of intermittent fasting." Nat Rev Endocrinol. 2022
[2] de Cabo R, Mattson MP. "Effects of Intermittent Fasting on Health." NEJM. 2019
[3] Longo VD, Panda S. "Fasting, circadian rhythms, and time-restricted feeding." Cell Metab. 2016
[4] Academy of Nutrition and Dietetics position paper, 2022

## Further Research Needed

- Long-term studies (5+ years)
- Effects on different age groups
- Optimal fasting windows
```
