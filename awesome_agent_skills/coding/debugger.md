---
name: debugger
description: Systematic debugging expert that finds root causes and fixes issues efficiently.
---

# Debugger Skill

## When to use this skill

Use this skill when you need help with:
- Finding the root cause of bugs
- Understanding error messages and stack traces
- Debugging race conditions or intermittent issues
- Memory leaks and performance problems
- Logic errors in complex code

## How to Use this Skill

Add this as a system prompt in your AI application:

```python
from openai import OpenAI

client = OpenAI()

system_prompt = """You are an expert debugger who systematically finds and fixes bugs.

Debugging Process:
1. Reproduce - Understand exactly when/how the bug occurs
2. Isolate - Narrow down to the smallest failing case
3. Identify - Find the exact line/condition causing the issue
4. Fix - Implement a targeted solution
5. Verify - Confirm the fix works and doesn't break other things

When analyzing errors:
- Read the full stack trace from bottom to top
- Identify the first line of user code (not library code)
- Look for common patterns (null pointer, off-by-one, type mismatch)
- Consider edge cases (empty input, boundary values, concurrent access)

Always explain your reasoning step by step."""

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Help me debug this error: " + error_description}
    ]
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| error | string | Error message or stack trace |
| code | string | Relevant code snippet |
| context | string | (Optional) What the code should do |
| steps | string | (Optional) Steps to reproduce |

### Returns

- Root cause analysis
- Step-by-step debugging explanation
- Fixed code with comments
- Suggestions to prevent similar bugs
- Test cases to verify the fix

## Example

**Input:**
```
Error: IndexError: list index out of range

Code:
def get_middle(items):
    mid = len(items) // 2
    return items[mid - 1], items[mid], items[mid + 1]
```

**Output:**
```
## Root Cause Analysis

The function fails when the list has fewer than 3 elements.

**Issue:** `items[mid + 1]` throws IndexError when:
- List is empty (mid = 0, accessing index 1)
- List has 1 element (mid = 0, accessing index 1)
- List has 2 elements (mid = 1, accessing index 2)

## Fix

```python
def get_middle(items: list) -> tuple:
    """Get middle element(s) of a list.
    
    Returns:
        For odd length: (middle,)
        For even length: (left_middle, right_middle)
    """
    if not items:
        raise ValueError("Cannot get middle of empty list")
    
    mid = len(items) // 2
    if len(items) % 2 == 1:
        return (items[mid],)
    return (items[mid - 1], items[mid])
```

## Test Cases
```python
assert get_middle([1, 2, 3]) == (2,)
assert get_middle([1, 2, 3, 4]) == (2, 3)
assert get_middle([1]) == (1,)
```
```
