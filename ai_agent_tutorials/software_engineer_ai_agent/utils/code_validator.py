import ast
import re

# Define dangerous modules, functions, and patterns
DANGEROUS_MODULES = {
    'os', 'subprocess', 'sys', 'shutil', 'requests', 'socket',
    'pickle', 'urllib', 'ftplib', 'telnetlib', 'smtplib'
}

DANGEROUS_FUNCTIONS = {
    'eval', 'exec', 'compile', 'open', '__import__', 'globals',
    'locals', 'getattr', 'setattr', 'delattr', '__getattribute__'
}

DANGEROUS_PATTERNS = [
    r"__import__\s*\(",
    r"importlib",
    r"ctypes",
    r"globals\s*\(",
]

class CodeSecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.security_issues = []
    
    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in DANGEROUS_MODULES or alias.name.split('.')[0] in DANGEROUS_MODULES:
                self.security_issues.append(f"Dangerous import: {alias.name}")
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        if node.module in DANGEROUS_MODULES or node.module.split('.')[0] in DANGEROUS_MODULES:
            self.security_issues.append(f"Dangerous import from: {node.module}")
        self.generic_visit(node)
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_FUNCTIONS:
            self.security_issues.append(f"Dangerous function call: {node.func.id}")
        elif isinstance(node.func, ast.Attribute) and node.func.attr in DANGEROUS_FUNCTIONS:
            self.security_issues.append(f"Dangerous attribute call: {node.func.attr}")
        self.generic_visit(node)
        
def validate_code(code):
    """
    Validates Python code for security issues
    
    Args:
        code (str): Python code to validate
        
    Returns:
        tuple: (is_valid, issues) - Boolean indicating if the code is safe and list of issues
    """
    # Check for dangerous patterns using regex
    pattern_issues = []
    for pattern in DANGEROUS_PATTERNS:
        matches = re.findall(pattern, code)
        if matches:
            pattern_issues.append(f"Dangerous pattern detected: {pattern}")
    
    # Check for dangerous imports and function calls using AST
    try:
        tree = ast.parse(code)
        visitor = CodeSecurityVisitor()
        visitor.visit(tree)
        ast_issues = visitor.security_issues
        
        all_issues = pattern_issues + ast_issues
        return len(all_issues) == 0, all_issues
    except SyntaxError as e:
        return False, [f"Syntax error in code: {str(e)}"]