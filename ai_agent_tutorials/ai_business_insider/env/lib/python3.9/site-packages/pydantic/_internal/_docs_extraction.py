"""Utilities related to attribute docstring extraction."""

from __future__ import annotations

import ast
import inspect
import textwrap
from typing import Any


class DocstringVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()

        self.target: str | None = None
        self.attrs: dict[str, str] = {}
        self.previous_node_type: type[ast.AST] | None = None

    def visit(self, node: ast.AST) -> Any:
        node_result = super().visit(node)
        self.previous_node_type = type(node)
        return node_result

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        if isinstance(node.target, ast.Name):
            self.target = node.target.id

    def visit_Expr(self, node: ast.Expr) -> Any:
        if (
            isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and self.previous_node_type is ast.AnnAssign
        ):
            docstring = inspect.cleandoc(node.value.value)
            if self.target:
                self.attrs[self.target] = docstring
            self.target = None


def _dedent_source_lines(source: list[str]) -> str:
    # Required for nested class definitions, e.g. in a function block
    dedent_source = textwrap.dedent(''.join(source))
    if dedent_source.startswith((' ', '\t')):
        # We are in the case where there's a dedented (usually multiline) string
        # at a lower indentation level than the class itself. We wrap our class
        # in a function as a workaround.
        dedent_source = f'def dedent_workaround():\n{dedent_source}'
    return dedent_source


def _extract_source_from_frame(cls: type[Any]) -> list[str] | None:
    frame = inspect.currentframe()

    while frame:
        if inspect.getmodule(frame) is inspect.getmodule(cls):
            lnum = frame.f_lineno
            try:
                lines, _ = inspect.findsource(frame)
            except OSError:
                # Source can't be retrieved (maybe because running in an interactive terminal),
                # we don't want to error here.
                pass
            else:
                block_lines = inspect.getblock(lines[lnum - 1 :])
                dedent_source = _dedent_source_lines(block_lines)
                try:
                    block_tree = ast.parse(dedent_source)
                except SyntaxError:
                    pass
                else:
                    stmt = block_tree.body[0]
                    if isinstance(stmt, ast.FunctionDef) and stmt.name == 'dedent_workaround':
                        # `_dedent_source_lines` wrapped the class around the workaround function
                        stmt = stmt.body[0]
                    if isinstance(stmt, ast.ClassDef) and stmt.name == cls.__name__:
                        return block_lines

        frame = frame.f_back


def extract_docstrings_from_cls(cls: type[Any], use_inspect: bool = False) -> dict[str, str]:
    """Map model attributes and their corresponding docstring.

    Args:
        cls: The class of the Pydantic model to inspect.
        use_inspect: Whether to skip usage of frames to find the object and use
            the `inspect` module instead.

    Returns:
        A mapping containing attribute names and their corresponding docstring.
    """
    if use_inspect:
        # Might not work as expected if two classes have the same name in the same source file.
        try:
            source, _ = inspect.getsourcelines(cls)
        except OSError:
            return {}
    else:
        source = _extract_source_from_frame(cls)

    if not source:
        return {}

    dedent_source = _dedent_source_lines(source)

    visitor = DocstringVisitor()
    visitor.visit(ast.parse(dedent_source))
    return visitor.attrs
