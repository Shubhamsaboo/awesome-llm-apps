import os
import sys
import json
import importlib.util
from typing import Dict, Any

print("CWD:", os.getcwd(), file=sys.stderr)
print("FILES IN CWD:", os.listdir(), file=sys.stderr)
print("TOOLS_DIR:", os.path.join(os.path.dirname(__file__), 'tools'), file=sys.stderr)

TOOLS_DIR = os.path.join(os.path.dirname(__file__), 'tools')

class ToolManager:
    def __init__(self, tools_dir: str):
        self.tools_dir = tools_dir
        self.commands = {}  # command_name -> (tool_name, function)
        self.load_tools()

    def load_tools(self):
        if not os.path.isdir(self.tools_dir):
            return
        for tool_name in os.listdir(self.tools_dir):
            tool_path = os.path.join(self.tools_dir, tool_name)
            if not os.path.isdir(tool_path):
                continue
            mcp_json_path = os.path.join(tool_path, 'mcp.json')
            if not os.path.isfile(mcp_json_path):
                continue
            with open(mcp_json_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            entry_point = meta.get('entry_point')
            if not entry_point:
                continue
            entry_path = os.path.join(tool_path, entry_point)
            if not os.path.isfile(entry_path):
                continue
            # Dynamically import the tool's entry point
            spec = importlib.util.spec_from_file_location(f"{tool_name}_module", entry_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Register commands
            for cmd, cmd_meta in meta.get('commands', {}).items():
                if hasattr(module, cmd):
                    self.commands[cmd] = (tool_name, getattr(module, cmd))

    def dispatch(self, method: str, params: Dict[str, Any]):
        if method not in self.commands:
            raise Exception(f"Unknown command: {method}")
        tool_name, func = self.commands[method]
        return func(params)

def jsonrpc_response(result, id):
    response = {
        "jsonrpc": "2.0",
        "id": id
    }
    if result is not None:
        response["result"] = result
    return json.dumps(response)

def jsonrpc_error(message, id=None, code=-32603):
    response = {
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": message
        }
    }
    # Only include id if it's not None (for notifications, id can be None)
    if id is not None:
        response["id"] = id
    return json.dumps(response)

def handle_initialize(params):
    return {
        "protocolVersion": "2025-06-18",
        "capabilities": {
            "tools": {},
            "resources": {},
            "prompts": {}
        },
        "serverInfo": {
            "name": "native-mcp-server",
            "version": "1.0.0"
        }
    }

def handle_initialized(params):
    # Notification - no response needed
    return None

def handle_list_resources(params):
    return {"resources": []}

def handle_list_prompts(params):
    return {"prompts": []}

def handle_list_tools(params):
    tool_manager = ToolManager(TOOLS_DIR)
    tools = []
    for cmd, (tool_name, func) in tool_manager.commands.items():
        # Load the mcp.json to get command metadata
        tool_path = os.path.join(tool_manager.tools_dir, tool_name)
        mcp_json_path = os.path.join(tool_path, 'mcp.json')
        with open(mcp_json_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        
        cmd_meta = meta.get('commands', {}).get(cmd, {})
        tool_info = {
            "name": cmd,
            "description": cmd_meta.get('description', f'Tool: {cmd}'),
            "inputSchema": {
                "type": "object",
                "properties": cmd_meta.get('params', {}),
                "required": list(cmd_meta.get('params', {}).keys())
            }
        }
        tools.append(tool_info)
    
    return {"tools": tools}

def handle_call_tool(params):
    tool_manager = ToolManager(TOOLS_DIR)
    tool_name = params.get('name')
    arguments = params.get('arguments', {})
    
    if tool_name not in tool_manager.commands:
        raise Exception(f"Unknown tool: {tool_name}")
    
    result = tool_manager.dispatch(tool_name, arguments)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }

def main():
    tool_manager = ToolManager(TOOLS_DIR)
    
    # MCP protocol handlers
    mcp_handlers = {
        "initialize": handle_initialize,
        "notifications/initialized": handle_initialized,
        "tools/list": handle_list_tools,
        "tools/call": handle_call_tool,
        "resources/list": handle_list_resources,
        "prompts/list": handle_list_prompts
    }
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            # Skip empty lines
            line = line.strip()
            if not line:
                continue
                
            req = json.loads(line)
            method = req.get('method')
            params = req.get('params', {})
            id = req.get('id')
            
            # Handle notifications (no id field, no response expected)
            if id is None and method:
                if method in mcp_handlers:
                    try:
                        mcp_handlers[method](params)
                    except Exception as e:
                        # Notifications don't send error responses
                        print(f"Error in notification {method}: {e}", file=sys.stderr)
                continue
            
            # Handle requests (have id field, response expected)
            if not method:
                sys.stdout.write(jsonrpc_error("Missing method", id) + '\n')
                sys.stdout.flush()
                continue
            
            try:
                # Handle MCP protocol methods
                if method in mcp_handlers:
                    result = mcp_handlers[method](params)
                    if result is not None:  # Only send response if not a notification
                        sys.stdout.write(jsonrpc_response(result, id) + '\n')
                        sys.stdout.flush()
                else:
                    # Try to dispatch to tools (for backward compatibility)
                    result = tool_manager.dispatch(method, params)
                    sys.stdout.write(jsonrpc_response(result, id) + '\n')
                    sys.stdout.flush()
                
            except Exception as e:
                sys.stdout.write(jsonrpc_error(str(e), id) + '\n')
                sys.stdout.flush()
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}", file=sys.stderr)
            sys.stdout.write(jsonrpc_error(f"Invalid JSON: {e}", None) + '\n')
            sys.stdout.flush()
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)
            sys.stdout.write(jsonrpc_error(f"Server error: {e}", None) + '\n')
            sys.stdout.flush()

if __name__ == "__main__":
    main() 