# Python Expert Guidelines

**A comprehensive guide for AI agents writing and reviewing Python code**, organized by priority and impact.

---

## Table of Contents

### Correctness — **CRITICAL**
1. [Avoid Mutable Default Arguments](#avoid-mutable-default-arguments)
2. [Proper Error Handling](#proper-error-handling)

### Type Safety — **HIGH**
3. [Use Type Hints](#use-type-hints)
4. [Use Dataclasses](#use-dataclasses)

### Performance — **HIGH**
5. [Use List Comprehensions](#use-list-comprehensions)
6. [Use Context Managers](#use-context-managers)

### Style — **MEDIUM**
7. [Follow PEP 8 Style Guide](#follow-pep-8-style-guide)
8. [Write Docstrings](#write-docstrings)

---

## Correctness

### Avoid Mutable Default Arguments

**Impact: CRITICAL** | **Category: correctness** | **Tags:** bugs, defaults, mutable, gotcha

Mutable default arguments (like lists or dicts) are shared across all calls to the function.

#### Why This Matters

Because the default value is evaluated only once at function definition time, subsequent calls will persist changes made to the default object, leading to extremely subtle and frustrating bugs.

#### ❌ Incorrect

```python
def add_item(item, items=[]):  # BUG: [] is shared!
    items.append(item)
    return items

print(add_item("a"))  # ['a']
print(add_item("b"))  # ['a', 'b'] - Unexpected!
```

#### ✅ Correct

```python
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    """Add an item to a list, creating a new list if none provided.
    
    Args:
        item: The item to add
        items: Optional existing list to add to
        
    Returns:
        The list with the new item added
    """
    if items is None:
        items = []
    items.append(item)
    return items
```

[➡️ Full details: correctness-mutable-defaults.md](rules/correctness-mutable-defaults.md)

---

### Proper Error Handling

**Impact: CRITICAL** | **Category: correctness** | **Tags:** errors, exceptions, reliability

Always handle errors explicitly. Don't use bare except clauses or ignore errors silently.

#### ❌ Incorrect

```python
try:
    result = risky_operation()
except:
    pass  # Silent failure!
```

#### ✅ Correct

```python
try:
    config = json.loads(config_file.read())
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in config file: {e}")
    config = get_default_config()
except FileNotFoundError:
    logger.warning("Config file not found, using defaults")
    config = get_default_config()
```

[➡️ Full details: correctness-error-handling.md](rules/correctness-error-handling.md)

---

## Type Safety

### Use Type Hints

**Impact: HIGH** | **Category: type-safety** | **Tags:** types, mypy, annotations, documentation

Type hints enable static analysis, improve IDE support, and serve as documentation.

#### Why This Matters

Python's dynamic nature can lead to runtime errors that are hard to catch. Type hints allow tools like `mypy` to verify code correctness before execution.

#### ❌ Incorrect

```python
def get_user(id):
    return users.get(id)
```

#### ✅ Correct

```python
from typing import Optional, Dict, Any

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch user by ID.
    
    Args:
        user_id: The unique identifier for the user
        
    Returns:
        User dictionary if found, None otherwise
    """
    return users.get(user_id)
```

[➡️ Full details: type-hints.md](rules/type-hints.md)

---

### Use Dataclasses

**Impact: HIGH** | **Category: type-safety** | **Tags:** dataclasses, classes, data, boilerplate

Use the `@dataclass` decorator for classes that primarily store data.

#### Why This Matters

Dataclasses automatically generate `__init__`, `__repr__`, and `__eq__` methods, reducing boilerplate and ensuring consistent behavior for data containers.

#### ❌ Incorrect

```python
class User:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email
    
    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email})"
    
    def __eq__(self, other):
        return self.id == other.id and self.name == other.name
```

#### ✅ Correct

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

# With additional configuration
@dataclass(frozen=True)  # Immutable
class Config:
    api_key: str
    timeout: int = 30
```

[➡️ Full details: type-dataclasses.md](rules/type-dataclasses.md)

---

## Performance

### Use List Comprehensions

**Impact: HIGH** | **Category: performance** | **Tags:** comprehensions, pythonic, efficiency

Use list comprehensions for simple transformations and filtering.

#### Why This Matters

List comprehensions are more concise, readable to experienced Pythonistas, and generally faster than equivalent `for` loops because they are optimized in the CPython interpreter.

#### ❌ Incorrect

```python
squares = []
for x in range(10):
    squares.append(x ** 2)

# Filtering with loop
evens = []
for x in range(20):
    if x % 2 == 0:
        evens.append(x)
```

#### ✅ Correct

```python
# Simple transformation
squares = [x ** 2 for x in range(10)]

# With filtering
evens = [x for x in range(20) if x % 2 == 0]

# Nested (use sparingly - break into functions if complex)
matrix = [[i * j for j in range(3)] for i in range(3)]
```

[➡️ Full details: performance-comprehensions.md](rules/performance-comprehensions.md)

---

### Use Context Managers

**Impact: HIGH** | **Category: performance** | **Tags:** context-managers, with, resources, cleanup

Always use context managers (`with` statements) for resource cleanup.

#### Why This Matters

Manual cleanup is error-prone. If an exception occurs before `close()` is called, the resource (file handle, database connection, lock) may remain open, leading to leaks and system instability.

#### ❌ Incorrect

```python
f = open('file.txt')
data = f.read()
f.close()  # May never be called if exception occurs!
```

#### ✅ Correct

```python
with open('file.txt') as f:
    data = f.read()
# File is automatically closed, even if exception occurs

# Multiple resources
with open('input.txt') as infile, open('output.txt', 'w') as outfile:
    outfile.write(infile.read().upper())
```

[➡️ Full details: performance-context-managers.md](rules/performance-context-managers.md)

---

## Style

### Follow PEP 8 Style Guide

**Impact: MEDIUM** | **Category: style** | **Tags:** pep8, python, style, conventions

Python's official style guide ensures readable, consistent code.

#### Why This Matters

Readability is a core Python philosophy. Consistent naming and formatting make the codebase maintainable and reduce friction for teams.

#### ❌ Incorrect

```python
def CalculateTotal(itemPrice,qty):
  return itemPrice*qty

class user_account:
  pass

x=1+2
```

#### ✅ Correct

```python
def calculate_total(item_price: float, quantity: int) -> float:
    """Calculate the total price for items."""
    return item_price * quantity


class UserAccount:
    """Represents a user account in the system."""
    pass


x = 1 + 2
```

[➡️ Full details: style-pep8.md](rules/style-pep8.md)

---

### Write Docstrings

**Impact: MEDIUM** | **Category: style** | **Tags:** documentation, docstrings, google-style

Write comprehensive docstrings for all public functions, classes, and modules.

#### Why This Matters

Good documentation makes code self-explanatory and enables IDEs to provide better autocomplete and hover information. It also serves as the primary reference for API users.

#### ❌ Incorrect

```python
def process(data, config):
    # processes the data
    return result
```

#### ✅ Correct

```python
def process_user_data(
    data: Dict[str, Any], 
    config: ProcessConfig
) -> ProcessResult:
    """Process user data according to the provided configuration.
    
    Takes raw user data and applies transformations, validation,
    and enrichment based on the configuration settings.
    
    Args:
        data: Raw user data as a dictionary containing at minimum
            'user_id' and 'email' keys.
        config: Processing configuration specifying transformations
            to apply and validation rules.
            
    Returns:
        ProcessResult containing the transformed data and any
        validation warnings encountered.
        
    Raises:
        ValidationError: If required fields are missing from data.
        ConfigError: If config contains invalid transformation rules.
        
    Example:
        >>> config = ProcessConfig(normalize_email=True)
        >>> result = process_user_data({'user_id': 1, 'email': 'TEST@Example.com'}, config)
        >>> result.data['email']
        'test@example.com'
    """
    ...
```

[➡️ Full details: style-docstrings.md](rules/style-docstrings.md)

---

## Quick Reference

### Python Code Checklist

**Correctness (CRITICAL - address first)**
- [ ] No mutable default arguments
- [ ] Specific exception handling (no bare `except:`)
- [ ] Edge cases handled
- [ ] Input validation present

**Type Safety (HIGH)**
- [ ] Type hints on all functions
- [ ] Return types specified
- [ ] Using dataclasses for data containers
- [ ] Generic types where appropriate

**Performance (HIGH)**
- [ ] List comprehensions over loops where readable
- [ ] Context managers for all resources
- [ ] Generators for large data
- [ ] Built-in functions leveraged

**Style (MEDIUM)**
- [ ] PEP 8 compliant
- [ ] Docstrings on public functions
- [ ] Meaningful variable names
- [ ] 88-100 character line limit

---

## Severity Levels

| Level | Description | Examples | Action |
|-------|-------------|----------|--------|
| **CRITICAL** | Bugs, data corruption, security issues | Mutable defaults, bare except | Fix immediately |
| **HIGH** | Correctness risks, maintainability issues | Missing types, resource leaks | Fix before merge |
| **MEDIUM** | Code quality, readability | Style violations, missing docs | Fix or accept with TODO |
| **LOW** | Minor improvements, preferences | Minor formatting | Optional |

---

## Code Review Output Format

When reviewing Python code, structure your output as:

```markdown
## Summary
[Brief overview of the code and main issues found]

## Critical Issues 🔴

### 1. [Issue Title]
**File:** `path/to/file.py:line`
**Issue:** [Description of the problem]
**Impact:** [Why this matters]
**Fix:**
```python
# Corrected code
```

## High Priority 🟠

### 1. [Issue Title]
[Continue pattern...]

## Medium Priority 🟡

[Continue pattern...]

## Recommendations
- [General improvement suggestion]
- [Best practice to adopt]

## Summary
- 🔴 CRITICAL: X
- 🟠 HIGH: X
- 🟡 MEDIUM: X

**Recommendation:** [Overall assessment and next steps]
```

---

## References

- Individual rule files in `rules/` directory
- [PEP 8 - Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)
- [Python typing module documentation](https://docs.python.org/3/library/typing.html)
