# This file is part of the LLM4AD project (https://github.com/Optima-CityU/llm4ad).
# Last Revision: 2025/2/16
#
# ------------------------------- Copyright --------------------------------
# Copyright (c) 2025 Optima Group.
# 
# Permission is granted to use the LLM4AD platform for research purposes. 
# All publications, software, or other works that utilize this platform 
# or any part of its codebase must acknowledge the use of "LLM4AD" and 
# cite the following reference:
# 
# Fei Liu, Rui Zhang, Zhuoliang Xie, Rui Sun, Kai Li, Xi Lin, Zhenkun Wang, 
# Zhichao Lu, and Qingfu Zhang, "LLM4AD: A Platform for Algorithm Design 
# with Large Language Model," arXiv preprint arXiv:2412.17287 (2024).
# 
# For inquiries regarding commercial use or licensing, please contact 
# http://www.llm4ad.com/contact.html
# --------------------------------------------------------------------------

"""
This file implements 2 classes representing unities of code:

- Function, containing all the information we need about functions: name, args,
  body and optionally a return type and a docstring.

- Program, which contains a code preface (which could be imports, global
  variables and classes, ...) and a list of Functions.

- For example, a function is shown below,
which is an un-executable program because 'np' is not defined, and 'WEIGHT' is not defined.
--------------------------------------------------------------------------------------------
def func(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    b = b + WEIGHT
    return a + b
--------------------------------------------------------------------------------------------

- A program is an executable object as shown below.
--------------------------------------------------------------------------------------------
import numpy as np
WEIGHT = 10

def func(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    b = b + WEIGHT
    return a + b
--------------------------------------------------------------------------------------------
"""

from __future__ import annotations

import ast
import copy
import dataclasses
from typing import Any, List, Callable


@dataclasses.dataclass
class Function:
    """A parsed Python function."""

    algorithm = ''
    name: str
    args: str
    body: str
    return_type: str | None = None
    docstring: str | None = None
    score: Any | None = None
    evaluate_time: float | None = None
    sample_time: float | None = None

    def __str__(self) -> str:
        return_type = f' -> {self.return_type}' if self.return_type else ''

        function = f'def {self.name}({self.args}){return_type}:\n'
        if self.docstring:
            # self.docstring is already indented on every line except the first one.
            # Here, we assume the indentation is always four spaces.
            new_line = '\n' if self.body else ''
            function += f'    """{self.docstring}"""{new_line}'
        # self.body is already indented.
        function += self.body + '\n\n'
        return function

    def __setattr__(self, name: str, value: str) -> None:
        # Ensure there aren't leading & trailing new lines in `body`.
        if name == 'body':
            value = value.strip('\n')
        # Ensure there aren't leading & trailing quotes in `docstring``.
        if name == 'docstring' and value is not None:
            if '"""' in value:
                value = value.strip()
                value = value.replace('"""', '')
        super().__setattr__(name, value)

    def __eq__(self, other: Function):
        assert isinstance(other, Function)
        return (self.name == other.name and
                self.args == other.args and
                self.return_type == other.return_type and
                self.body == other.body)


@dataclasses.dataclass(frozen=True)
class Program:
    """A parsed Python program."""

    # `preface` is everything from the beginning of the code till the first
    # function is found.
    preface: str
    functions: list[Function]

    def __str__(self) -> str:
        program = f'{self.preface}\n' if self.preface else ''
        program += '\n'.join([str(f) for f in self.functions])
        return program

    def find_function_index(self, function_name: str) -> int:
        """Returns the index of input function name."""
        function_names = [f.name for f in self.functions]
        count = function_names.count(function_name)
        if count == 0:
            raise ValueError(
                f'function {function_name} does not exist in program:\n{str(self)}'
            )
        if count > 1:
            raise ValueError(
                f'function {function_name} exists more than once in program:\n'
                f'{str(self)}'
            )
        index = function_names.index(function_name)
        return index

    def get_function(self, function_name: str) -> Function:
        index = self.find_function_index(function_name)
        return self.functions[index]

    def exec(self) -> List[Callable]:
        function_names = [f.name for f in self.functions]
        g = {}
        exec(str(self), g)
        callable_funcs = [g[name] for name in function_names]
        return callable_funcs


class _ProgramVisitor(ast.NodeVisitor):
    """Parses code to collect all required information to produce a `Program`.
    Note that we do not store function decorators.
    """

    def __init__(self, sourcecode: str):
        self._codelines: list[str] = sourcecode.splitlines()
        self._preface: str = ''
        self._functions: list[Function] = []
        self._current_function: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Collects all information about the function being parsed.
        """
        # We only care about first level functions.
        if node.col_offset == 0:
            self._current_function = node.name
            # --------------------------------------------------------------------------------------------
            # RZ: Here is an issue: some cases were not taken into consideration.
            # For instance, if the first parsed function has decorators,
            # these decorators will also be retained in the preceding code snippet.
            # However, in the algorithm's flow, these decorators are invalid,
            # leading to subsequent evaluations reporting errors.
            # --------------------------------------------------------------------------------------------
            # if not self._functions:
            #     self._preface = '\n'.join(self._codelines[:node.lineno - 1])
            # --------------------------------------------------------------------------------------------
            # Fix bugs: if the first function is decorated, find the smallest line_no of the decorator,
            # FIX bugs: and retrain the code above it as 'preface'.
            # --------------------------------------------------------------------------------------------
            if not self._functions:
                has_decorators = bool(node.decorator_list)
                if has_decorators:
                    # find the minimum line number and retain the code above
                    decorator_start_line = min(decorator.lineno for decorator in node.decorator_list)
                    self._preface = '\n'.join(self._codelines[:decorator_start_line - 1])
                else:
                    self._preface = '\n'.join(self._codelines[:node.lineno - 1])
            # --------------------------------------------------------------------------------------------
            function_end_line = node.end_lineno
            body_start_line = node.body[0].lineno - 1
            # Extract the docstring.
            docstring = None
            if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                docstring = f'    """{ast.literal_eval(ast.unparse(node.body[0]))}"""'
                if len(node.body) > 1:
                    # ----------------------------------------------------------------------------
                    # RZ: If the next line of the docstring is also comment that starts with "#"
                    # We should preserve it.
                    # ----------------------------------------------------------------------------
                    # body_start_line = node.body[1].lineno - 1
                    # ----------------------------------------------------------------------------
                    # Fix bugs: If we find the docstring, the function body start with
                    # Fix bugs: body[0].end_lineno, where body[0] refers to the docstring node.
                    # ----------------------------------------------------------------------------
                    body_start_line = node.body[0].end_lineno
                    # ----------------------------------------------------------------------------
                else:
                    body_start_line = function_end_line

            self._functions.append(Function(
                name=node.name,
                args=ast.unparse(node.args),
                return_type=ast.unparse(node.returns) if node.returns else None,
                docstring=docstring,
                body='\n'.join(self._codelines[body_start_line:function_end_line]),
            ))
        self.generic_visit(node)

    def return_program(self) -> Program:
        return Program(preface=self._preface, functions=self._functions)


class TextFunctionProgramConverter:
    """Convert text to Program instance and Function instance,
    Convert Program instance to Function instance, and Function instance to Program instance.
    """

    @classmethod
    def text_to_program(cls, program_str: str) -> Program | None:
        """Returns Program object by parsing input text using Python AST.
        """
        try:
            # We assume that the program is composed of some preface (e.g. imports,
            # classes, assignments, ...) followed by a sequence of functions.
            tree = ast.parse(program_str)
            visitor = _ProgramVisitor(program_str)
            visitor.visit(tree)
            return visitor.return_program()
        except:
            return None

    @classmethod
    def text_to_function(cls, program_str: str) -> Function | None:
        """Returns Function object by parsing input text using Python AST.
        """
        try:
            program = cls.text_to_program(program_str)
            if len(program.functions) != 1:
                raise ValueError(f'Only one function expected, got {len(program.functions)}'
                                 f':\n{program.functions}')
            return program.functions[0]
        except ValueError as value_err:
            raise value_err
        except:
            return None

    @classmethod
    def function_to_program(cls, function: str | Function, template_program: str | Program) -> Program | None:
        try:
            # convert function to Function instance
            if isinstance(function, str):
                function = cls.text_to_function(function)
            else:
                function = copy.deepcopy(function)

            # convert template_program to Program instance
            if isinstance(template_program, str):
                template_program = cls.text_to_program(template_program)
            else:
                template_program = copy.deepcopy(template_program)

            # assert that a program have one function
            if len(template_program.functions) != 1:
                raise ValueError(f'Only one function expected, got {len(template_program.functions)}'
                                 f':\n{template_program.functions}')

            # replace the function body with the new function body
            template_program.functions[0].body = function.body
            return template_program
        except ValueError as value_err:
            raise value_err
        except:
            return None

    @classmethod
    def program_to_function(cls, program: str | Program) -> Function | None:
        try:
            # convert program to Program instance
            if isinstance(program, str):
                program = cls.text_to_program(program)
            else:
                program = copy.deepcopy(program)

            # assert that a program have one function
            if len(program.functions) != 1:
                raise ValueError(f'Only one function expected, got {len(program.functions)}'
                                 f':\n{program.functions}')

            # return the function
            return program.functions[0]
        except ValueError as value_err:
            raise value_err
        except:
            return None
