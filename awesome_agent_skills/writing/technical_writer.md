---
name: technical-writer
description: Creates clear documentation, guides, and technical content for developers and users.
---

# Technical Writer Skill

## When to use this skill

Use this skill when you need:
- API documentation
- README files and setup guides
- User manuals and tutorials
- Architecture documentation
- Changelog and release notes

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are an expert technical writer who creates clear, user-friendly documentation.

Writing Principles:
- Lead with the user's goal, not the feature
- Use active voice and present tense
- Include practical examples for every concept
- Structure content from simple to complex
- Test instructions before publishing

Document Structure:
1. Overview (what and why)
2. Prerequisites (what you need)
3. Quick Start (get running fast)
4. Detailed Guide (step-by-step)
5. Reference (API details, options)
6. Troubleshooting (common issues)

Style Guide:
- Use second person ("you")
- Keep sentences under 25 words
- One idea per paragraph
- Use lists for 3+ items
- Include code examples with comments"""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Write a README for my Python CLI tool"}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | "readme", "api", "tutorial", "reference" |
| product | string | What you're documenting |
| audience | string | (Optional) Technical level of readers |
| existing | string | (Optional) Current docs to improve |

### Returns

- Well-structured documentation
- Code examples with explanations
- Clear installation/setup steps
- Troubleshooting section
- Consistent formatting

## Example

**Input:**
```
Write a README for a CLI tool called "quicksort" that sorts lines in files
```

**Output:**
```markdown
# quicksort

Sort lines in files quickly from the command line.

## Installation

```bash
pip install quicksort
```

## Quick Start

Sort a file alphabetically:
```bash
quicksort data.txt
```

Sort in reverse order:
```bash
quicksort data.txt --reverse
```

## Usage

```bash
quicksort [OPTIONS] FILE
```

### Options

| Option | Description |
|--------|-------------|
| `-r, --reverse` | Sort in descending order |
| `-n, --numeric` | Sort numerically instead of alphabetically |
| `-o, --output FILE` | Write to file instead of stdout |
| `-u, --unique` | Remove duplicate lines |

### Examples

Sort numbers in a file:
```bash
quicksort numbers.txt --numeric
```

Sort and remove duplicates:
```bash
quicksort names.txt --unique -o sorted_names.txt
```

## Troubleshooting

**"File not found" error**
Ensure the file path is correct and you have read permissions.

**Numbers sorting incorrectly**
Add `--numeric` flag for numerical sorting (otherwise "10" comes before "2").

## License

MIT
```
