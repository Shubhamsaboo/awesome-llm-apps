import ast
from dataclasses import dataclass
import json
from pathlib import Path
import re
import unittest


source = Path(__file__).with_name("dependency_upgrade_advisor.py")
tree = ast.parse(source.read_text(encoding="utf-8"))
names = {"Dependency", "_REQ_LINE", "_SPECIFIER", "_CURRENT_OPERATORS",
         "_MAX_NAME_LENGTH", "_NAME_OK", "_NPM_COMPARATOR", "_pypi_version",
         "_npm_version", "parse_dependencies"}
nodes = [node for node in tree.body
         if getattr(node, "name", None) in names
         or isinstance(node, ast.Assign) and any(getattr(target, "id", None) in names for target in node.targets)]
namespace = {"dataclass": dataclass, "json": json, "re": re}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), namespace)


class MarkerVersionTests(unittest.TestCase):
    def test_python_marker_is_not_the_package_version(self):
        dependencies = namespace["parse_dependencies"](
            'requests; python_version >= "3.12"\n'
            'urllib3<3; python_version >= "3.10"\n'
            'pydantic!=1.0; python_version > "3.9"\n'
        )
        self.assertEqual([dependency.version for dependency in dependencies], ["", "", ""])

    def test_pin_is_preserved_before_environment_markers(self):
        dependencies = namespace["parse_dependencies"]('requests>=2.31.0; python_version >= "3.12"')
        self.assertEqual(dependencies[0].version, "2.31.0")


if __name__ == "__main__":
    unittest.main()
