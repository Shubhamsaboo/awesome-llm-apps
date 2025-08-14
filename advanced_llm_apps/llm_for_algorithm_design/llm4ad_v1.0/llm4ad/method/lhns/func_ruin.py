from __future__ import annotations

import copy
import ast
import random
import numpy as np
from typing import Any, List, Callable

from ...base import Function, TextFunctionProgramConverter, Program


class LHNSFunction(Function):
    features: str = ""

    @classmethod
    def convert_function_to_lhnsfunction(cls, function: Function) -> LHNSFunction:
        """Convert a Function object to a LHNSFunction object.
        """
        if isinstance(function, LHNSFunction):
            return function
        return LHNSFunction(
            name=function.name,
            args=function.args,
            return_type=function.return_type,
            docstring=function.docstring,
            body=function.body,
        )


class LHNSProgram(Program):
    functions: list[LHNSFunction]

    @classmethod
    def convert_program_to_lhnsprogram(cls, program: Program) -> LHNSProgram:
        """Convert a Program object to a LHNSProgram object.
        """
        if isinstance(program, LHNSProgram):
            return program
        return LHNSProgram(
            preface=program.preface,
            functions=[LHNSFunction.convert_function_to_lhnsfunction(func) for func in program.functions],
        )


class _LHNSProgramVisitor(ast.NodeVisitor):
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

    def return_program(self) -> LHNSProgram:
        return LHNSProgram(preface=self._preface, functions=self._functions)


class LHNSTextFunctionProgramConverter(TextFunctionProgramConverter):
    @classmethod
    def text_to_program(cls, program_str: str) -> LHNSProgram | None:
        """Returns Program object by parsing input text using Python AST.
        """
        try:
            # We assume that the program is composed of some preface (e.g. imports,
            # classes, assignments, ...) followed by a sequence of functions.
            tree = ast.parse(program_str)
            visitor = _LHNSProgramVisitor(program_str)
            visitor.visit(tree)
            return visitor.return_program()
        except:
            return None

    @classmethod
    def text_to_function(cls, program_str: str) -> LHNSFunction | None:
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


class LHNSFunctionRuin:
    @classmethod
    def delete_function_snips(cls, function: LHNSFunction, cooling_rate: float) -> (LHNSFunction, int):
        """
        Delete lines from the function body.
        Args:
            function: The function to delete lines from.
            cooling_rate: The number of lines to delete.
        Returns:
            The modified function without lines deleted.
        """
        func = copy.deepcopy(function)
        lines = copy.deepcopy(func.body.split('\n'))
        to_be_deleted_lines_index = []  # "#" and selected lines
        content_lines_index = []  # not "#", "" and import and def

        for index, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith('def ') or stripped_line.startswith('import') or stripped_line == "":
                continue
            if stripped_line.startswith('#'):
                to_be_deleted_lines_index.append(index)
            else:
                if "#" in line:
                    line.split('#', 1)[0].rstrip()
                content_lines_index.append(index)

        # when number_of_delete is a coefficient
        number_of_delete_lines = np.ceil(cooling_rate * len(content_lines_index)).astype(int)
        content_delete_lines = random.choices(content_lines_index,
                                              k=min([number_of_delete_lines, len(content_lines_index)]))
        if len(content_delete_lines) == 0:
            raise Exception("No content lines to delete")
        to_be_deleted_lines_index.extend(content_delete_lines)

        new_code = ""
        for indexI, i in enumerate(lines):
            if indexI not in to_be_deleted_lines_index:
                new_code += i
                if i != lines[-1]:
                    new_code += '\n'

        func.body = new_code

        return func, number_of_delete_lines

    @classmethod
    def find_code_features(cls, prev_function: LHNSFunction, new_function: LHNSFunction) -> List[str]:
        """
        Find the code features of the new function that are not in the previous function.
        Args:
            prev_function: The previous function.
            new_function: The new function.
        Returns:
            The code features of the new function that are not in the previous function.
        """
        p_code = prev_function.body
        n_code = new_function.body
        p_lines = copy.deepcopy(p_code.split('\n'))
        n_lines = copy.deepcopy(n_code.split('\n'))
        prev_content_lines = []  # not "#", "" and import and def
        new_content_lines = []  # not "#", "" and import and def

        code_features = []

        # extract effective lines
        for index, line in enumerate(p_lines):
            stripped_line = line.strip()
            if stripped_line.startswith('def ') or stripped_line.startswith(
                    'import') or stripped_line == "" or stripped_line.startswith('#'):
                continue
            else:
                if "#" in line:
                    line.split('#', 1)[0].rstrip()
                prev_content_lines.append(line.strip())

        for index, line in enumerate(n_lines):
            stripped_line = line.strip()
            if stripped_line.startswith('def ') or stripped_line.startswith(
                    'import') or stripped_line == "" or stripped_line.startswith('#'):
                continue
            else:
                if "#" in line:
                    line.split('#', 1)[0].rstrip()
                new_content_lines.append(line.rstrip())

        # compare
        for line in new_content_lines:
            if line.strip() not in prev_content_lines:
                code_features.append(line)

        return code_features

    @classmethod
    def merge_features(cls, function: LHNSFunction, features: List[str]) -> LHNSFunction:
        """
        Merge the features into the function.
        Args:
            function: The function to merge features into.
            features: The features to merge.
        Returns:
            The modified function with features merged.
        """
        func = copy.deepcopy(function)
        lines = copy.deepcopy(func.body.split('\n'))
        to_be_deleted_lines_index = []  # "#" and selected lines
        content_lines_index = []  # not "#", "" and import and def

        for index, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith('def ') or stripped_line.startswith('import') or stripped_line == "":
                continue
            if stripped_line.startswith('#'):
                to_be_deleted_lines_index.append(index)
            else:
                if "#" in line:
                    line.split('#', 1)[0].rstrip()
                content_lines_index.append(index)

        new_code = ""
        for indexI, i in enumerate(lines[:-1]):
            if indexI not in to_be_deleted_lines_index:
                new_code += i
                new_code += '\n'

        # insert code feature
        if features is not None:
            for i in features:
                new_code += i
                new_code += '\n'

        new_code += lines[-1]
        func.body = new_code

        return func
