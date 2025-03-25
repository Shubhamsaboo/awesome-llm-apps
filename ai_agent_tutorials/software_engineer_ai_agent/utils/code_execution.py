import subprocess

def execute_python_code(code):
    try:
        script_name = "generated_script.py"
        with open(script_name, "w") as f:
            f.write(code)
        
        result = subprocess.run(["python", script_name], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error: {e}"
