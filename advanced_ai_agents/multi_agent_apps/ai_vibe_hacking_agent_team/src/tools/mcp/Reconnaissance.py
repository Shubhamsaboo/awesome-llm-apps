# weather_server.py
from mcp.server.fastmcp import FastMCP
from typing_extensions import Annotated
from typing import List, Optional, Union
# from src.tools.mcp.command_execution import command_execution
import subprocess

CONTAINER_NAME = "attacker"
mcp = FastMCP("reconnaissance", port=3001)

def command_execution(command: Annotated[str, "Commands to run on Kali Linux"]) -> Annotated[str, "Command Execution Result"]:
    """
    Run one command at a time in a kali linux environment and return the result
    """
    try:
        # Docker 사용 가능 여부 확인
        docker_check = subprocess.run(
            ["docker", "ps"], 
            capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        
        if docker_check.returncode != 0:
            return f"[-] Docker is not available: {docker_check.stderr.strip()}"
            
        # 컨테이너 존재 여부 확인
        container_check = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}"],
            capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        
        if CONTAINER_NAME not in container_check.stdout:
            return f"[-] Container '{CONTAINER_NAME}' does not exist"
        
        # 컨테이너 실행 상태 확인
        running_check = subprocess.run(
            ["docker", "ps", "--filter", f"name={CONTAINER_NAME}"],
            capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        
        # 컨테이너가 실행 중이 아니면 시작
        if CONTAINER_NAME not in running_check.stdout:
            start_result = subprocess.run(
                ["docker", "start", CONTAINER_NAME],
                capture_output=True, text=True, encoding="utf-8", errors="ignore"
            )
            
            if start_result.returncode != 0:
                return f"[-] Failed to start container '{CONTAINER_NAME}': {start_result.stderr.strip()}"
            
        # ✅ Kali Linux 컨테이너에서 명령어 실행
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "sh", "-c", command],
            capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )
        
        if result.returncode != 0:
            return f"[-] Command execution error: {result.stderr.strip()}"
        
        return f"{result.stdout.strip()}"
    
    except FileNotFoundError:
        return "[-] Docker command not found. Is Docker installed and in PATH?"
    
    except Exception as e:
        return f"[-] Error: {str(e)} (Type: {type(e).__name__})"

# MCP 도구 정의
@mcp.tool(description="Network discovery and port scanning")
def nmap(target: str, options: Optional[Union[str, List[str]]] = None) -> Annotated[str, "command execution Result"]:
    if options is None:
        args_str = ""
    elif isinstance(options, list):
        args_str = " ".join(options)
    else:
        args_str = options
    command = f'nmap {args_str} {target}'
    return command_execution(command)

@mcp.tool(description="Web service analysis and content retrieval")
def curl(target: str = "", options: str = "") -> Annotated[str, "command execution Result"]:
    command = f'curl {options} {target}'
    return command_execution(command)

@mcp.tool(description="DNS information gathering")
def dig(target: str, options: str = "") -> Annotated[str, "command execution Result"]:
    command = f'dig {options} {target}'
    return command_execution(command)

@mcp.tool(description="Domain registration and ownership lookup")
def whois(target: str, options: str = "") -> Annotated[str, "command execution Result"]:
    command = f'whois {options} {target}'
    return command_execution(command)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")