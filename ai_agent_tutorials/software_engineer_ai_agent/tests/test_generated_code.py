import unittest
import os
from utils.code_execution import execute_python_file

class TestGeneratedCode(unittest.TestCase):

    def test_backend_code_execution(self):
        """Test if backend API code executes without errors."""
        file_path = "backend/generated_api.py"
        if os.path.exists(file_path):
            result = execute_python_file(file_path)
            self.assertNotIn("Traceback", result)

    def test_dsa_code_execution(self):
        """Test if DSA solution executes correctly."""
        file_path = "dsa/dsa_solution.py"
        if os.path.exists(file_path):
            result = execute_python_file(file_path)
            self.assertNotIn("Traceback", result)

if __name__ == "__main__":
    unittest.main()
