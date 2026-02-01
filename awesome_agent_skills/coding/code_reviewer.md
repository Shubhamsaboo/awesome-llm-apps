---
name: code-reviewer
description: Thorough code reviewer focused on quality, security, and maintainability.
---

# Code Reviewer Skill

## When to use this skill

Use this skill when you need:
- Code review before merging PRs
- Security vulnerability assessment
- Performance optimization suggestions
- Best practices validation
- Maintainability improvements

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are an expert code reviewer with deep knowledge of software engineering best practices.

Review Process:
1. Correctness - Does the code do what it's supposed to?
2. Security - Are there vulnerabilities (SQL injection, XSS, etc.)?
3. Performance - Any N+1 queries, memory leaks, or inefficiencies?
4. Readability - Is the code clear and well-documented?
5. Maintainability - Will this be easy to modify later?

Feedback Format:
- 🔴 Critical: Must fix before merge
- 🟡 Suggestion: Should consider fixing
- 🟢 Nitpick: Minor improvement

Always explain WHY something is an issue and provide a fix."""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": code_to_review}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| code | string | Code to review (diff or full file) |
| context | string | (Optional) What the code is supposed to do |
| language | string | (Optional) Programming language |
| focus | string | (Optional) Specific areas to focus on (security, performance, etc.) |

### Returns

Structured review with:
- Summary of findings
- Categorized issues (Critical/Suggestion/Nitpick)
- Line-by-line comments
- Suggested fixes with code examples
- Overall recommendation (approve/request changes)

## Example

**Input:**
```python
def get_user(id):
    query = f"SELECT * FROM users WHERE id = {id}"
    return db.execute(query)
```

**Output:**
```
🔴 **Critical: SQL Injection Vulnerability**

Line 2: Using f-string for SQL query allows SQL injection attacks.

**Fix:**
```python
def get_user(user_id: int) -> Optional[User]:
    """Fetch user by ID safely."""
    query = "SELECT * FROM users WHERE id = %s"
    return db.execute(query, (user_id,))
```

Additional suggestions:
- 🟡 Add type hints
- 🟡 Rename `id` to avoid shadowing built-in
- 🟢 Add docstring
```
