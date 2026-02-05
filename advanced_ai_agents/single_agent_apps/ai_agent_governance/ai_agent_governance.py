"""
🛡️ AI Agent Governance - Policy-Based Sandboxing Tutorial

This tutorial demonstrates how to build a governance layer that enforces
deterministic policies on AI agents, preventing dangerous actions before execution.

Key concepts:
- Policy-based action validation
- Tool interception and wrapping
- Audit logging for compliance
- Rate limiting and resource controls
"""

import os
import json
import yaml
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from collections import defaultdict
import re

from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

class Decision(Enum):
    """Policy evaluation decision"""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class Action:
    """Represents an action an agent wants to perform"""
    name: str
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    agent_id: str = "default-agent"


@dataclass
class PolicyResult:
    """Result of a policy evaluation"""
    decision: Decision
    reason: str
    policy_name: str
    is_terminal: bool = True


@dataclass
class AuditEntry:
    """An entry in the audit log"""
    timestamp: datetime
    action: Action
    decision: Decision
    reason: str
    policy_matched: str


# ============================================================================
# POLICY ENGINE
# ============================================================================

class PolicyRule:
    """Base class for policy rules"""
    
    def __init__(self, name: str):
        self.name = name
    
    def evaluate(self, action: Action) -> Optional[PolicyResult]:
        """Evaluate the action against this rule. Returns None if rule doesn't apply."""
        raise NotImplementedError


class FilesystemPolicy(PolicyRule):
    """Policy for filesystem access control"""
    
    def __init__(self, allowed_paths: List[str], denied_paths: List[str]):
        super().__init__("filesystem")
        self.allowed_paths = [os.path.expanduser(p) for p in allowed_paths]
        self.denied_paths = [os.path.expanduser(p) for p in denied_paths]
    
    def evaluate(self, action: Action) -> Optional[PolicyResult]:
        # Check if action involves file paths
        path = None
        if action.kwargs.get("path"):
            path = action.kwargs["path"]
        elif action.kwargs.get("file_path"):
            path = action.kwargs["file_path"]
        elif action.args and isinstance(action.args[0], str) and "/" in action.args[0]:
            path = action.args[0]
        
        if not path:
            return None  # Rule doesn't apply
        
        path = os.path.abspath(os.path.expanduser(path))
        
        # Check denied paths first
        for denied in self.denied_paths:
            if path.startswith(os.path.abspath(denied)):
                return PolicyResult(
                    decision=Decision.DENY,
                    reason=f"Path '{path}' matches denied pattern '{denied}'",
                    policy_name=self.name
                )
        
        # Check if path is in allowed paths
        for allowed in self.allowed_paths:
            if path.startswith(os.path.abspath(allowed)):
                return PolicyResult(
                    decision=Decision.ALLOW,
                    reason=f"Path '{path}' is within allowed directory '{allowed}'",
                    policy_name=self.name
                )
        
        # Default deny if not explicitly allowed
        return PolicyResult(
            decision=Decision.DENY,
            reason=f"Path '{path}' is outside allowed directories",
            policy_name=self.name
        )


class NetworkPolicy(PolicyRule):
    """Policy for network access control"""
    
    def __init__(self, allowed_domains: List[str], block_all_others: bool = True):
        super().__init__("network")
        self.allowed_domains = allowed_domains
        self.block_all_others = block_all_others
    
    def evaluate(self, action: Action) -> Optional[PolicyResult]:
        # Check if action involves URLs or domains
        url = None
        for key in ["url", "endpoint", "domain", "host"]:
            if key in action.kwargs:
                url = action.kwargs[key]
                break
        
        if not url:
            # Check args for URL patterns
            for arg in action.args:
                if isinstance(arg, str) and ("http://" in arg or "https://" in arg):
                    url = arg
                    break
        
        if not url:
            return None  # Rule doesn't apply
        
        # Extract domain from URL
        domain_match = re.search(r"https?://([^/]+)", url)
        if domain_match:
            domain = domain_match.group(1)
        else:
            domain = url
        
        # Check if domain is allowed
        for allowed in self.allowed_domains:
            if domain == allowed or domain.endswith("." + allowed):
                return PolicyResult(
                    decision=Decision.ALLOW,
                    reason=f"Domain '{domain}' is in allowlist",
                    policy_name=self.name
                )
        
        if self.block_all_others:
            return PolicyResult(
                decision=Decision.DENY,
                reason=f"Domain '{domain}' not in allowlist",
                policy_name=self.name
            )
        
        return None


class RateLimitPolicy(PolicyRule):
    """Policy for rate limiting agent actions"""
    
    def __init__(self, max_actions_per_minute: int = 60):
        super().__init__("rate_limit")
        self.max_actions_per_minute = max_actions_per_minute
        self.action_history: List[datetime] = []
    
    def evaluate(self, action: Action) -> Optional[PolicyResult]:
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        
        # Clean old entries
        self.action_history = [t for t in self.action_history if t > cutoff]
        
        if len(self.action_history) >= self.max_actions_per_minute:
            return PolicyResult(
                decision=Decision.DENY,
                reason=f"Rate limit exceeded: {len(self.action_history)}/{self.max_actions_per_minute} actions per minute",
                policy_name=self.name
            )
        
        self.action_history.append(now)
        return None  # Allow - doesn't block


class ApprovalRequiredPolicy(PolicyRule):
    """Policy requiring human approval for certain actions"""
    
    def __init__(self, actions_requiring_approval: List[str]):
        super().__init__("approval_required")
        self.actions_requiring_approval = actions_requiring_approval
    
    def evaluate(self, action: Action) -> Optional[PolicyResult]:
        if action.name in self.actions_requiring_approval:
            return PolicyResult(
                decision=Decision.REQUIRE_APPROVAL,
                reason=f"Action '{action.name}' requires human approval",
                policy_name=self.name
            )
        return None


class PolicyEngine:
    """Central policy evaluation engine"""
    
    def __init__(self):
        self.rules: List[PolicyRule] = []
        self.audit_log: List[AuditEntry] = []
    
    def add_rule(self, rule: PolicyRule):
        """Add a policy rule to the engine"""
        self.rules.append(rule)
    
    def evaluate(self, action: Action) -> PolicyResult:
        """Evaluate an action against all policy rules"""
        for rule in self.rules:
            result = rule.evaluate(action)
            if result and result.is_terminal:
                self._log_audit(action, result)
                return result
        
        # Default allow if no rule blocks
        result = PolicyResult(
            decision=Decision.ALLOW,
            reason="No policy rule blocked this action",
            policy_name="default"
        )
        self._log_audit(action, result)
        return result
    
    def _log_audit(self, action: Action, result: PolicyResult):
        """Log action and decision to audit trail"""
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            action=action,
            decision=result.decision,
            reason=result.reason,
            policy_matched=result.policy_name
        )
        self.audit_log.append(entry)
        logger.info(f"AUDIT: {result.decision.value.upper()} - {action.name} - {result.reason}")
    
    def get_audit_log(self) -> List[Dict]:
        """Get audit log as serializable dictionaries"""
        return [
            {
                "timestamp": entry.timestamp.isoformat(),
                "action": entry.action.name,
                "action_args": str(entry.action.kwargs),
                "decision": entry.decision.value,
                "reason": entry.reason,
                "policy_matched": entry.policy_matched
            }
            for entry in self.audit_log
        ]
    
    @classmethod
    def from_yaml(cls, yaml_content: str) -> "PolicyEngine":
        """Create a PolicyEngine from YAML configuration"""
        config = yaml.safe_load(yaml_content)
        engine = cls()
        
        policies = config.get("policies", {})
        
        if "filesystem" in policies:
            fs = policies["filesystem"]
            engine.add_rule(FilesystemPolicy(
                allowed_paths=fs.get("allowed_paths", []),
                denied_paths=fs.get("denied_paths", [])
            ))
        
        if "network" in policies:
            net = policies["network"]
            engine.add_rule(NetworkPolicy(
                allowed_domains=net.get("allowed_domains", []),
                block_all_others=net.get("block_all_others", True)
            ))
        
        if "execution" in policies:
            exe = policies["execution"]
            if "max_actions_per_minute" in exe:
                engine.add_rule(RateLimitPolicy(exe["max_actions_per_minute"]))
            if "require_approval_for" in exe:
                engine.add_rule(ApprovalRequiredPolicy(exe["require_approval_for"]))
        
        return engine


# ============================================================================
# GOVERNANCE WRAPPER
# ============================================================================

class PolicyViolation(Exception):
    """Raised when an action violates a policy"""
    pass


def get_human_approval(action: Action) -> bool:
    """Get human approval for an action (interactive prompt)"""
    print(f"\n⏸️  APPROVAL REQUIRED")
    print(f"   Action: {action.name}")
    print(f"   Args: {action.kwargs}")
    response = input("   Approve? [y/N]: ").strip().lower()
    return response == "y"


def governed_tool(policy_engine: PolicyEngine, require_interactive_approval: bool = True):
    """
    Decorator that wraps a tool function with governance checks.
    
    Args:
        policy_engine: The PolicyEngine to use for evaluation
        require_interactive_approval: If True, prompt for approval when needed
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create action representation
            action = Action(
                name=func.__name__,
                args=args,
                kwargs=kwargs
            )
            
            # Evaluate against policies
            result = policy_engine.evaluate(action)
            
            if result.decision == Decision.DENY:
                raise PolicyViolation(f"❌ DENIED: {result.reason}")
            
            elif result.decision == Decision.REQUIRE_APPROVAL:
                if require_interactive_approval:
                    if not get_human_approval(action):
                        raise PolicyViolation("❌ DENIED: Human rejected the action")
                else:
                    raise PolicyViolation(f"⏸️ PENDING: {result.reason}")
            
            # Action is allowed - execute
            print(f"✅ ALLOWED: {result.reason}")
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# EXAMPLE TOOLS (to be governed)
# ============================================================================

def create_governed_tools(policy_engine: PolicyEngine) -> Dict[str, Callable]:
    """Create a set of governed tools for the agent"""
    
    @governed_tool(policy_engine)
    def read_file(path: str) -> str:
        """Read contents of a file"""
        with open(path, "r") as f:
            return f.read()
    
    @governed_tool(policy_engine)
    def write_file(path: str, content: str) -> str:
        """Write content to a file"""
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to {path}"
    
    @governed_tool(policy_engine)
    def delete_file(path: str) -> str:
        """Delete a file"""
        os.remove(path)
        return f"Successfully deleted {path}"
    
    @governed_tool(policy_engine)
    def web_request(url: str) -> str:
        """Make a web request (simulated)"""
        return f"Simulated response from {url}"
    
    @governed_tool(policy_engine)
    def execute_shell(command: str) -> str:
        """Execute a shell command (simulated for safety)"""
        return f"Simulated execution of: {command}"
    
    return {
        "read_file": read_file,
        "write_file": write_file,
        "delete_file": delete_file,
        "web_request": web_request,
        "execute_shell": execute_shell
    }


# ============================================================================
# DEMO: SIMPLE AGENT WITH GOVERNANCE
# ============================================================================

class GovernedAgent:
    """A simple agent with governance layer"""
    
    def __init__(self, policy_engine: PolicyEngine):
        self.policy_engine = policy_engine
        self.tools = create_governed_tools(policy_engine)
        self.client = OpenAI()
    
    def run(self, user_request: str) -> str:
        """Process a user request with governance"""
        
        # Create system prompt with available tools
        system_prompt = """You are a helpful assistant with access to the following tools:
- read_file(path): Read a file
- write_file(path, content): Write to a file  
- delete_file(path): Delete a file
- web_request(url): Make a web request
- execute_shell(command): Execute a shell command

Analyze the user's request and respond with the tool call you would make.
Format: TOOL: tool_name(arg1="value1", arg2="value2")

If no tool is needed, just respond normally."""
        
        # Get LLM response
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ],
            max_tokens=500
        )
        
        llm_response = response.choices[0].message.content
        print(f"\n🤖 Agent response: {llm_response}")
        
        # Parse and execute tool call if present
        if "TOOL:" in llm_response:
            tool_line = llm_response.split("TOOL:")[1].strip().split("\n")[0]
            return self._execute_tool_call(tool_line)
        
        return llm_response
    
    def _execute_tool_call(self, tool_call: str) -> str:
        """Parse and execute a tool call string"""
        # Simple parser for tool_name(kwargs)
        match = re.match(r"(\w+)\((.*)\)", tool_call)
        if not match:
            return f"Could not parse tool call: {tool_call}"
        
        tool_name = match.group(1)
        args_str = match.group(2)
        
        # Parse kwargs
        kwargs = {}
        for arg in args_str.split(", "):
            if "=" in arg:
                key, value = arg.split("=", 1)
                kwargs[key.strip()] = value.strip().strip('"\'')
        
        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name}"
        
        try:
            result = self.tools[tool_name](**kwargs)
            return f"Tool result: {result}"
        except PolicyViolation as e:
            return str(e)
        except Exception as e:
            return f"Tool error: {e}"


# ============================================================================
# MAIN DEMO
# ============================================================================

def main():
    print("🛡️ AI Agent Governance Demo")
    print("=" * 40)
    
    # Define policy configuration
    policy_yaml = """
policies:
  filesystem:
    allowed_paths: 
      - /workspace
      - /tmp
    denied_paths:
      - /etc
      - /home
      - ~/.ssh
      
  network:
    allowed_domains:
      - api.openai.com
      - api.github.com
    block_all_others: true
    
  execution:
    max_actions_per_minute: 60
    require_approval_for:
      - delete_file
      - execute_shell
"""
    
    print("\n📋 Loading policy configuration...")
    policy_engine = PolicyEngine.from_yaml(policy_yaml)
    print("✅ Policy engine initialized with rules:")
    for rule in policy_engine.rules:
        print(f"   - {rule.name}")
    
    # Create governed tools
    tools = create_governed_tools(policy_engine)
    
    # Demo: Test various actions
    print("\n" + "=" * 40)
    print("📝 Testing Governance Layer")
    print("=" * 40)
    
    test_cases = [
        ("read_file", {"path": "/etc/passwd"}),
        ("write_file", {"path": "/workspace/report.md", "content": "# Analysis Report\n"}),
        ("web_request", {"url": "https://api.github.com/users"}),
        ("web_request", {"url": "https://unknown-site.com/api"}),
        ("read_file", {"path": "/workspace/data.txt"}),
    ]
    
    for tool_name, kwargs in test_cases:
        print(f"\n🤖 Testing: {tool_name}({kwargs})")
        try:
            # We need to create a temp file for the read test
            if tool_name == "read_file" and kwargs["path"] == "/workspace/data.txt":
                os.makedirs("/workspace", exist_ok=True)
                with open("/workspace/data.txt", "w") as f:
                    f.write("Test data")
            
            result = tools[tool_name](**kwargs)
            print(f"   Result: {result}")
        except PolicyViolation as e:
            print(f"   {e}")
        except Exception as e:
            print(f"   Error: {e}")
    
    # Print audit log
    print("\n" + "=" * 40)
    print("📊 Audit Log")
    print("=" * 40)
    for entry in policy_engine.get_audit_log():
        print(f"   {entry['decision'].upper():8} | {entry['action']:15} | {entry['reason'][:50]}")
    
    # Demo with LLM agent (optional - requires API key)
    if os.getenv("OPENAI_API_KEY"):
        print("\n" + "=" * 40)
        print("🤖 LLM Agent Demo (with governance)")
        print("=" * 40)
        
        agent = GovernedAgent(policy_engine)
        
        demo_requests = [
            "Read the contents of /etc/passwd",
            "Write a summary to /workspace/summary.md", 
            "Make a request to api.github.com to get user info"
        ]
        
        for request in demo_requests:
            print(f"\n👤 User: {request}")
            result = agent.run(request)
            print(f"📤 Result: {result}")
    else:
        print("\n💡 Set OPENAI_API_KEY to run the full LLM agent demo")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
