from mcp.server.fastmcp import FastMCP
from typing_extensions import Annotated
from typing import List
import subprocess
import uuid
import time
import os


mcp = FastMCP("terminal", port=3003)

CONTAINER_NAME = "attacker"

def run(command: List[str]) -> subprocess.CompletedProcess:
    """일반 docker exec 명령어 실행"""
    return subprocess.run(
        ["docker", "exec", CONTAINER_NAME] + command,
        capture_output=True, text=True, encoding='utf-8'
    )

def tmux_run(command: List[str]) -> subprocess.CompletedProcess:
    """tmux 명령어 실행"""
    return run(["tmux"] + command)

@mcp.tool(description="Create new terminal sessions")
def create_session(
    session_names: Annotated[List[str], "Session names to create"]
) -> Annotated[List[str], "List of created session names"]:
    """새 tmux 터미널 세션들 생성"""
    created_sessions = []
    
    for session_name in session_names:
        result = tmux_run(["new-session", "-d", "-s", session_name])
        if result.returncode != 0:
            raise Exception(f"Failed to create session '{session_name}': {result.stderr}")
        created_sessions.append(session_name)
    
    return created_sessions
    

@mcp.tool(description="List all active sessions")
def session_list() -> Annotated[List[str], "List of session IDs"]:
    result = tmux_run(["list-sessions"])
    if result.returncode != 0:
        return []
    return [line.split(":")[0].strip() for line in result.stdout.strip().split('\n') if line.strip()]

# @mcp.tool(description="Execute command in session")
# def command_exec(
#     session_id: Annotated[str, "Session ID"],
#     command: Annotated[str, "Command to execute"],
# ) -> Annotated[str, "Command output"]:
#     """command execute with file redirection and exit code checking"""
#     try:
#         channel = f"done-{session_id}-{uuid.uuid4().hex[:8]}"
#         timestamp = int(time.time())
#         output_file = f"/tmp/cmd_output_{session_id}_{timestamp}.txt"
#         status_file = f"/tmp/cmd_status_{session_id}_{timestamp}.txt"

#         # 강제 flush와 sync 추가
#         full_command = f"({command}) > {output_file} 2>&1; sync; echo $? > {status_file}; sync; tmux wait-for -S {channel}"
        
#         result = tmux_run(["send-keys", "-t", session_id, full_command, "Enter"])
#         if result.returncode != 0:
#             raise Exception(f"Failed to execute command: {result.stderr}")
        
#         wait_result = tmux_run(["wait-for", channel])
#         if wait_result.returncode != 0:
#             raise Exception(f"Command execution monitoring failed: {wait_result.stderr}")
        
#         # 추가 대기 시간
#         time.sleep(0.1)
        
#         try:
#             # 파일 존재 확인 먼저
#             output_check = run(["test", "-f", output_file])
#             status_check = run(["test", "-f", status_file])
            
#             if output_check.returncode != 0:
#                 raise Exception(f"Output file not found: {output_file}")
#             if status_check.returncode != 0:
#                 raise Exception(f"Status file not found: {status_file}")
            
#             # 파일 크기 확인 (디버깅용)
#             size_check = run(["ls", "-la", output_file, status_file])
#             print(f"DEBUG - File sizes: {size_check.stdout}")
            
#             # 상태 코드 확인
#             status_result = run(["cat", status_file])
#             if status_result.returncode != 0:
#                 raise Exception(f"Failed to read status file: {status_result.stderr}")
            
#             print(f"DEBUG - Status file content: '{status_result.stdout}'")
            
#             try:
#                 exit_code = int(status_result.stdout.strip())
#             except ValueError:
#                 raise Exception(f"Invalid exit code: '{status_result.stdout.strip()}'")
            
#             # 출력 읽기
#             output_result = run(["cat", output_file])
#             if output_result.returncode != 0:
#                 raise Exception(f"Failed to read output file: {output_result.stderr}")
            
#             output = output_result.stdout
#             print(f"DEBUG - Output length: {len(output)} chars")
#             print(f"DEBUG - Output preview: '{output[:100]}...'")
            
#             # 파일 정리
#             run(["rm", "-f", output_file, status_file])
            
#             # 명령어 실패 시 예외 발생
#             if exit_code != 0:
#                 raise Exception(f"Command failed with exit code {exit_code}: {output.strip()}")
            
#             return output.strip()
            
#         except Exception as e:
#             # 파일 정리 (에러 발생 시에도)
#             run(["rm", "-f", output_file, status_file])
#             raise Exception(f"Failed to process command result: {str(e)}")
    
#     except Exception as e:
#         raise Exception(f"Failed to execute command: {str(e)}")

@mcp.tool(description="Execute command in session")
def command_exec(
    session_id: Annotated[str, "Session ID"],
    command: Annotated[str, "Command to execute"],
) -> Annotated[str, "Command output"]:
    """command execute with file redirection and exit code checking"""
    try:
        channel = f"done-{session_id}-{uuid.uuid4().hex[:8]}"
        timestamp = int(time.time())
        output_file = f"/tmp/cmd_output_{session_id}_{timestamp}.txt"
        status_file = f"/tmp/cmd_status_{session_id}_{timestamp}.txt"

        # 명령어 실행 후 상태 코드를 별도 파일에 저장
        full_command = f"({command}) > {output_file} 2>&1; echo $? > {status_file}; tmux wait-for -S {channel}"
        
        result = tmux_run(["send-keys", "-t", session_id, full_command, "Enter"])
        if result.returncode != 0:
            raise Exception(f"Failed to execute command: {result.stderr}")
        
        wait_result = tmux_run(["wait-for", channel])
        if wait_result.returncode != 0:
            raise Exception(f"Command execution monitoring failed: {wait_result.stderr}")
        
        try:
            # 상태 코드 확인
            status_result = run(["cat", status_file])
            if status_result.returncode != 0:
                raise Exception(f"Failed to read status file: {status_result.stderr}")
            
            try:
                exit_code = int(status_result.stdout.strip())
            except ValueError:
                raise Exception(f"Invalid exit code: {status_result.stdout.strip()}")
            
            # 출력 읽기
            output_result = run(["cat", output_file])
            if output_result.returncode != 0:
                raise Exception(f"Failed to read output file: {output_result.stderr}")
            
            output = output_result.stdout

            # 파일 정리
            run(["rm", "-f", output_file, status_file])
            
            # 명령어 실패 시 예외 발생
            if exit_code != 0:
                raise Exception(f"Command failed with exit code {exit_code}: {output.strip()}")
            
            return output.strip()
            
        except Exception as e:
            # 파일 정리 (에러 발생 시에도)
            run(["rm", "-f", output_file, status_file])
            raise Exception(f"Failed to process command result: {str(e)}")
    
    except Exception as e:
        raise Exception(f"Failed to execute command: {str(e)}")

@mcp.tool(description="Kill terminal sessions")
def kill_session(
    session_names: Annotated[List[str], "Session names to kill"]
) -> Annotated[List[str], "Results for each session"]:
    """tmux 세션들 종료"""
    results = []
    
    for session_name in session_names:
        try:
            result = tmux_run(["kill-session", "-t", session_name])
            if result.returncode == 0:
                results.append(f"Session {session_name} killed successfully")
            else:
                results.append(f"Session {session_name} killed (with warning: {result.stderr})")
        except Exception as e:
            results.append(f"Failed to kill session {session_name}: {str(e)}")
    
    return results

@mcp.tool(description="Kill server, Kill all session")
def kill_server() -> Annotated[str, "Result"]:
    try:
        tmux_run(["kill-server"])
        return f"Server killed"

    except Exception as e:
        return f"Server killed (with warning: {str(e)})"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")