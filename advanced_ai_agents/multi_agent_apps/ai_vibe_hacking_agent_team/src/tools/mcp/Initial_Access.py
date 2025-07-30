
from mcp.server.fastmcp import FastMCP
from typing_extensions import Annotated
from typing import List, Optional, Union
import subprocess

mcp = FastMCP("initial_access", port=3002)


CONTAINER_NAME = "attacker"

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

# @mcp.tool(description="Brute-force authentication attacks using Patator")
# def patator(service: str, target: str, options: Optional[Union[str, List[str]]] = None) -> Annotated[str, "Command"]:
#     """
#     Executes a Patator brute-force attack.

#     Args:
#         service (str): Service name (e.g., ssh, ftp, mysql)
#         target (str): Target IP or URL
#         options (Optional[Union[str, List[str]]]): Additional patator options

#     Returns:
#         str: Executed shell command string
#     """
#     if options is None:
#         args_str = ""
#     elif isinstance(options, list):
#         args_str = " ".join(options)
#     else:
#         args_str = options

#     module = f"{service}_login"

#     # Determine default parameter based on service
#     if service in ["ssh", "ftp", "smb", "rdp", "telnet", "mysql"]:
#         target_param = f"host={target}"
#     elif service in ["http"]:
#         target_param = f"url={target}"
#     else:
#         target_param = target  # fallback

#     command = f"patator {module} {target_param} {args_str}"
#     return command_execution(command)

# tool 프롬프트
### patator - Credential Attacks
# **When to use**: Brute force authentication when weak or default credentials are suspected  
# **Supported Protocols**: ssh, ftp, http, smb, mysql, rdp, telnet 등  
# **Available wordlists**:  
# - Users: `root/data/wordlist/user.txt`  
# - Passwords: `root/data/wordlist/password.txt`

# **Examples**:
# - SSH brute-force:  
#   `patator ssh_login host=TARGET user=FILE0 password=FILE1 0=user.txt 1=password.txt`  
#   → ⚠️ *If you encounter a host key algorithm error (e.g., server supports only ssh-rsa)*,  
#   use the following workaround:  
#   `export PATATOR_SSH_PREFERRED_HOSTKEYS=ssh-rsa`  

# - HTTP login form:  
#   `patator http_fuzz url=http://TARGET/login.php method=POST body='u=admin&p=FILE0' 0=password.txt`

# **Tips**:
# - Use `-x ignore:mesg=...` to filter failed attempts  
# - Add delay or limit threads if needed to avoid lockout  
# - You can set preferred key exchange algorithms via `paramiko.Transport` if custom scripting is needed




@mcp.tool(description="Brute-force authentication attacks")
def hydra(target: str, options: Optional[Union[str, List[str]]] = None) -> Annotated[str, "Command"]:
    if options is None:
        args_str = ""
    elif isinstance(options, list):
        args_str = " ".join(options)
    else:
        args_str = options

    command = f"hydra {args_str} {target}"
    return command_execution(command)


@mcp.tool(description="Search exploit database for vulnerabilities")
def searchsploit(service_name: str, options: Optional[Union[str, List[str]]] = None) -> Annotated[str, "Command"]:
    if options is None:
        args_str = ""
    elif isinstance(options, list):
        args_str = " ".join(options)
    else:
        args_str = options

    command = f"searchsploit {args_str} {service_name}"
    return command_execution(command)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")