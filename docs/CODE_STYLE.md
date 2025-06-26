# Coding Standards

## General Guidelines

### Code Formatting

- All languages: Line length: 100 characters
- Python: Use Ruff for linting and Black for formatting
- TypeScript: Use Prettier for formatting
- Follow language-specific conventions

### Documentation

- Python: Use NumPy-style docstrings with type hints
- TypeScript: Use JSDoc with type annotations
- Markdown: Use consistent heading levels and formatting
- Include clear descriptions and examples

### Naming Conventions

- Python: Use snake_case for variables/functions, PascalCase for classes
- TypeScript: Use camelCase for variables/functions, PascalCase for classes/interfaces
- Use descriptive names that clearly indicate purpose

### Imports

- Python:
  - Group imports in order: standard library, third-party, local
  - Use absolute imports
  - Sort imports alphabetically
- TypeScript:
  - Use explicit relative paths
  - Group imports by type
  - Avoid wildcard imports

## Language-Specific Guidelines

### Python

- Follow PEP 8 conventions
- Use type hints
- Use pytest for testing
- Use conventional commits format
- Include module-level docstrings

### TypeScript

- Use TypeScript features (interfaces, types)
- Use proper access modifiers
- Document complex logic
- Use proper error handling

### Markdown

- Use consistent heading levels
- Format code blocks properly
- Use proper list formatting
- Include proper links formatting
- Follow consistent table structure

## Requirements Management

### Python

- Use requirements.txt for production
- Use dev-requirements.txt for development
- Pin versions
- Document dependencies
- Keep dependencies updated

### TypeScript

- Use package.json
- Separate devDependencies
- Use consistent version ranges
- Document usage

## Examples

### Python Example

```python
"""
Module docstring describing the purpose of the module.

Example:
    This module provides functionality for XYZ.

Attributes:
    CONSTANT_NAME: Description of the constant.
"""

from __future__ import annotations

import os
from typing import List, Optional

from third_party import library
from local_package import module


class ExampleClass:
    """Class docstring describing the class.

    Attributes:
        attribute: Description of the attribute.
    """

    def __init__(self, param: str) -> None:
        """Initialize the ExampleClass.

        Args:
            param: Description of the parameter.
        """
        self.attribute = param

    def method(self, param: int) -> str:
        """Method docstring describing the method.

        Args:
            param: Description of the parameter.

        Returns:
            str: Description of the return value.

        Raises:
            ValueError: Description of when this exception is raised.
        """
        return str(param)


def example_function(param: str) -> None:
    """Function docstring describing the function.

    Args:
        param: Description of the parameter.
    """
    pass
```

### TypeScript Example

```typescript
/**
 * Module description
 */
export interface ExampleInterface {
  property: string;
  method(): void;
}

export class ExampleClass implements ExampleInterface {
  /**
   * Constructor documentation
   * @param param Description of parameter
   */
  constructor(private param: string) {}

  /**
   * Method documentation
   * @param value Description of parameter
   * @returns Description of return value
   */
  method(value: number): string {
    return value.toString();
  }
}
```

### Naming Conventions

- Use snake_case for variables and functions
- Use PascalCase for classes
- Use UPPER_CASE for constants
- Use descriptive names that clearly indicate purpose

### Documentation

- Use NumPy-style docstrings for functions and classes
- Include type hints for all function parameters and return values
- Document all public classes and methods
- Include module-level docstrings

### Imports

- Group imports in the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Use absolute imports instead of relative imports
- Sort imports alphabetically within each group

### Error Handling

- Use specific exceptions instead of general ones
- Provide meaningful error messages
- Document potential exceptions in docstrings

### Testing

- Write unit tests for all functions
- Use pytest for testing
- Aim for 100% test coverage

### Version Control

- Commit messages should follow conventional commits format
- Use feature branches for development
- Follow semantic versioning for releases

## Example Code Structure

```python
"""
Module docstring describing the purpose of the module.

Example:
    This module provides functionality for XYZ.

Attributes:
    CONSTANT_NAME: Description of the constant.
"""

from __future__ import annotations

import os
from typing import List, Optional

from third_party import library
from local_package import module


class ExampleClass:
    """Class docstring describing the class.

    Attributes:
        attribute: Description of the attribute.
    """

    def __init__(self, param: str) -> None:
        """Initialize the ExampleClass.

        Args:
            param: Description of the parameter.
        """
        self.attribute = param

    def method(self, param: int) -> str:
        """Method docstring describing the method.

        Args:
            param: Description of the parameter.

        Returns:
            str: Description of the return value.

        Raises:
            ValueError: Description of when this exception is raised.
        """
        return str(param)


def example_function(param: str) -> None:
    """Function docstring describing the function.

    Args:
        param: Description of the parameter.
    """
    pass
```
