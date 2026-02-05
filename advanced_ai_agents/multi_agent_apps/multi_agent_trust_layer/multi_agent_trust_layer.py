"""
🤝 Multi-Agent Trust Layer Tutorial

This tutorial demonstrates how to build a trust layer for multi-agent systems
that enables secure delegation, trust scoring, and policy enforcement.

Key concepts:
- Agent identity and registration
- Trust scoring based on behavior
- Delegation chains with scope narrowing
- Policy enforcement across agent interactions
- Full audit trail of agent communications
"""

import os
import json
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# TRUST LEVELS
# ============================================================================

class TrustLevel(Enum):
    """Trust levels based on score ranges"""
    SUSPENDED = "suspended"      # 0-299
    RESTRICTED = "restricted"    # 300-499
    PROBATION = "probation"      # 500-699
    STANDARD = "standard"        # 700-899
    TRUSTED = "trusted"          # 900-1000
    
    @classmethod
    def from_score(cls, score: int) -> "TrustLevel":
        if score >= 900:
            return cls.TRUSTED
        elif score >= 700:
            return cls.STANDARD
        elif score >= 500:
            return cls.PROBATION
        elif score >= 300:
            return cls.RESTRICTED
        else:
            return cls.SUSPENDED


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

@dataclass
class AgentIdentity:
    """Represents an agent's verified identity"""
    agent_id: str
    public_key: str
    human_sponsor: str  # Email of accountable human
    organization: str
    roles: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrustScore:
    """Agent's trust score with history"""
    agent_id: str
    score: int  # 0-1000
    level: TrustLevel
    history: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def update(self, delta: int, reason: str):
        """Update trust score with bounds checking"""
        old_score = self.score
        self.score = max(0, min(1000, self.score + delta))
        self.level = TrustLevel.from_score(self.score)
        self.last_updated = datetime.utcnow()
        self.history.append({
            "timestamp": self.last_updated.isoformat(),
            "old_score": old_score,
            "new_score": self.score,
            "delta": delta,
            "reason": reason
        })


@dataclass
class DelegationScope:
    """Defines what an agent can do under a delegation"""
    allowed_actions: Set[str]
    denied_actions: Set[str] = field(default_factory=set)
    allowed_domains: Set[str] = field(default_factory=set)
    max_tokens: int = 10000
    time_limit_minutes: int = 60
    max_sub_delegations: int = 0  # Can this agent delegate further?
    custom_constraints: Dict[str, Any] = field(default_factory=dict)
    
    def allows_action(self, action: str) -> bool:
        """Check if an action is allowed under this scope"""
        if action in self.denied_actions:
            return False
        if not self.allowed_actions:  # Empty means all allowed
            return True
        return action in self.allowed_actions
    
    def narrow(self, child_scope: "DelegationScope") -> "DelegationScope":
        """Create a narrowed scope for sub-delegation"""
        return DelegationScope(
            allowed_actions=self.allowed_actions & child_scope.allowed_actions,
            denied_actions=self.denied_actions | child_scope.denied_actions,
            allowed_domains=self.allowed_domains & child_scope.allowed_domains if self.allowed_domains else child_scope.allowed_domains,
            max_tokens=min(self.max_tokens, child_scope.max_tokens),
            time_limit_minutes=min(self.time_limit_minutes, child_scope.time_limit_minutes),
            max_sub_delegations=min(self.max_sub_delegations, child_scope.max_sub_delegations),
            custom_constraints={**self.custom_constraints, **child_scope.custom_constraints}
        )


@dataclass
class Delegation:
    """A delegation of authority from one agent to another"""
    delegation_id: str
    parent_agent: str
    child_agent: str
    scope: DelegationScope
    task_description: str
    created_at: datetime
    expires_at: datetime
    signature: str  # Signed by parent agent
    parent_delegation_id: Optional[str] = None  # For chain tracking
    tokens_used: int = 0
    is_revoked: bool = False
    
    def is_valid(self) -> bool:
        """Check if delegation is still valid"""
        if self.is_revoked:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        if self.tokens_used >= self.scope.max_tokens:
            return False
        return True


@dataclass
class AuditEntry:
    """Audit log entry for agent interactions"""
    timestamp: datetime
    event_type: str
    agent_id: str
    action: str
    delegation_id: Optional[str]
    result: str  # "allowed", "denied", "error"
    details: Dict[str, Any]
    trust_impact: int = 0


# ============================================================================
# IDENTITY REGISTRY
# ============================================================================

class IdentityRegistry:
    """Manages agent identities"""
    
    def __init__(self):
        self.identities: Dict[str, AgentIdentity] = {}
        self.sponsor_to_agents: Dict[str, List[str]] = defaultdict(list)
    
    def register(self, identity: AgentIdentity) -> bool:
        """Register a new agent identity"""
        if identity.agent_id in self.identities:
            logger.warning(f"Agent {identity.agent_id} already registered")
            return False
        
        self.identities[identity.agent_id] = identity
        self.sponsor_to_agents[identity.human_sponsor].append(identity.agent_id)
        logger.info(f"Registered agent: {identity.agent_id} (sponsor: {identity.human_sponsor})")
        return True
    
    def get(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent identity"""
        return self.identities.get(agent_id)
    
    def revoke(self, agent_id: str, reason: str) -> bool:
        """Revoke an agent's identity"""
        if agent_id in self.identities:
            identity = self.identities.pop(agent_id)
            self.sponsor_to_agents[identity.human_sponsor].remove(agent_id)
            logger.warning(f"Revoked agent: {agent_id} - {reason}")
            return True
        return False


# ============================================================================
# TRUST SCORING ENGINE
# ============================================================================

class TrustScoringEngine:
    """Manages trust scores for agents"""
    
    # Score adjustments for various events
    SCORE_ADJUSTMENTS = {
        "task_completed": +10,
        "stayed_in_scope": +5,
        "accurate_output": +2,
        "scope_violation_attempt": -50,
        "inaccurate_output": -30,
        "resource_exceeded": -20,
        "security_violation": -100,
        "delegation_success": +15,
        "delegation_failure": -25,
    }
    
    def __init__(self, initial_score: int = 700):
        self.scores: Dict[str, TrustScore] = {}
        self.initial_score = initial_score
    
    def initialize(self, agent_id: str, initial_score: Optional[int] = None) -> TrustScore:
        """Initialize trust score for a new agent"""
        score = initial_score or self.initial_score
        trust_score = TrustScore(
            agent_id=agent_id,
            score=score,
            level=TrustLevel.from_score(score)
        )
        self.scores[agent_id] = trust_score
        return trust_score
    
    def get(self, agent_id: str) -> Optional[TrustScore]:
        """Get agent's trust score"""
        return self.scores.get(agent_id)
    
    def record_event(self, agent_id: str, event_type: str, custom_delta: Optional[int] = None) -> int:
        """Record an event and update trust score"""
        if agent_id not in self.scores:
            self.initialize(agent_id)
        
        delta = custom_delta if custom_delta is not None else self.SCORE_ADJUSTMENTS.get(event_type, 0)
        self.scores[agent_id].update(delta, event_type)
        
        logger.info(f"Trust update: {agent_id} {delta:+d} ({event_type}) → {self.scores[agent_id].score}")
        return delta


# ============================================================================
# DELEGATION MANAGER
# ============================================================================

class DelegationManager:
    """Manages delegation chains between agents"""
    
    def __init__(self, identity_registry: IdentityRegistry, trust_engine: TrustScoringEngine):
        self.delegations: Dict[str, Delegation] = {}
        self.agent_delegations: Dict[str, List[str]] = defaultdict(list)  # agent_id -> [delegation_ids]
        self.identity_registry = identity_registry
        self.trust_engine = trust_engine
    
    def create_delegation(
        self,
        parent_agent: str,
        child_agent: str,
        scope: DelegationScope,
        task_description: str,
        time_limit_minutes: Optional[int] = None,
        parent_delegation_id: Optional[str] = None
    ) -> Optional[Delegation]:
        """Create a new delegation from parent to child agent"""
        
        # Verify both agents exist
        if not self.identity_registry.get(parent_agent):
            logger.error(f"Parent agent not found: {parent_agent}")
            return None
        if not self.identity_registry.get(child_agent):
            logger.error(f"Child agent not found: {child_agent}")
            return None
        
        # Check parent's trust level
        parent_trust = self.trust_engine.get(parent_agent)
        if parent_trust and parent_trust.level == TrustLevel.SUSPENDED:
            logger.error(f"Suspended agent cannot delegate: {parent_agent}")
            return None
        
        # If this is a sub-delegation, narrow the scope
        if parent_delegation_id:
            parent_del = self.delegations.get(parent_delegation_id)
            if not parent_del or not parent_del.is_valid():
                logger.error(f"Invalid parent delegation: {parent_delegation_id}")
                return None
            if parent_del.scope.max_sub_delegations <= 0:
                logger.error(f"No sub-delegations allowed under: {parent_delegation_id}")
                return None
            scope = parent_del.scope.narrow(scope)
        
        # Create delegation
        delegation_id = f"del-{secrets.token_hex(8)}"
        time_limit = time_limit_minutes or scope.time_limit_minutes
        
        delegation = Delegation(
            delegation_id=delegation_id,
            parent_agent=parent_agent,
            child_agent=child_agent,
            scope=scope,
            task_description=task_description,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=time_limit),
            signature=self._sign_delegation(parent_agent, delegation_id),
            parent_delegation_id=parent_delegation_id
        )
        
        self.delegations[delegation_id] = delegation
        self.agent_delegations[child_agent].append(delegation_id)
        
        logger.info(f"Created delegation: {parent_agent} → {child_agent} ({delegation_id})")
        return delegation
    
    def _sign_delegation(self, agent_id: str, delegation_id: str) -> str:
        """Create a signature for a delegation (simplified - real impl would use crypto)"""
        data = f"{agent_id}:{delegation_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def validate_action(self, agent_id: str, action: str, delegation_id: Optional[str] = None) -> bool:
        """Validate if an agent can perform an action under their delegation"""
        
        if delegation_id:
            delegation = self.delegations.get(delegation_id)
            if not delegation:
                return False
            if not delegation.is_valid():
                return False
            if delegation.child_agent != agent_id:
                return False
            return delegation.scope.allows_action(action)
        
        # Check if agent has any valid delegation allowing this action
        for del_id in self.agent_delegations.get(agent_id, []):
            delegation = self.delegations.get(del_id)
            if delegation and delegation.is_valid() and delegation.scope.allows_action(action):
                return True
        
        return False
    
    def revoke_delegation(self, delegation_id: str, reason: str) -> bool:
        """Revoke a delegation"""
        if delegation_id in self.delegations:
            self.delegations[delegation_id].is_revoked = True
            logger.warning(f"Revoked delegation: {delegation_id} - {reason}")
            return True
        return False
    
    def get_active_delegations(self, agent_id: str) -> List[Delegation]:
        """Get all active delegations for an agent"""
        return [
            self.delegations[del_id]
            for del_id in self.agent_delegations.get(agent_id, [])
            if self.delegations[del_id].is_valid()
        ]


# ============================================================================
# POLICY ENGINE
# ============================================================================

class MultiAgentPolicyEngine:
    """Enforces policies for multi-agent interactions"""
    
    def __init__(self, trust_engine: TrustScoringEngine, delegation_manager: DelegationManager):
        self.trust_engine = trust_engine
        self.delegation_manager = delegation_manager
        self.role_policies: Dict[str, Dict[str, Any]] = {}
    
    def add_role_policy(self, role: str, policy: Dict[str, Any]):
        """Add a policy for a specific role"""
        self.role_policies[role] = policy
    
    def evaluate(
        self,
        agent_id: str,
        action: str,
        roles: List[str],
        delegation_id: Optional[str] = None
    ) -> tuple[bool, str]:
        """Evaluate if an action is allowed"""
        
        # Check trust level
        trust = self.trust_engine.get(agent_id)
        if not trust:
            return False, "Agent has no trust score"
        
        if trust.level == TrustLevel.SUSPENDED:
            return False, "Agent is suspended"
        
        # Check role-based policies
        for role in roles:
            policy = self.role_policies.get(role, {})
            
            # Check base trust requirement
            min_trust = policy.get("base_trust_required", 0)
            if trust.score < min_trust:
                return False, f"Trust score {trust.score} below minimum {min_trust} for role {role}"
            
            # Check denied actions
            if action in policy.get("denied_actions", []):
                return False, f"Action '{action}' denied for role {role}"
            
            # Check allowed actions (if specified, action must be in list)
            allowed = policy.get("allowed_actions", [])
            if allowed and action not in allowed:
                return False, f"Action '{action}' not in allowed list for role {role}"
        
        # Check delegation
        if delegation_id:
            if not self.delegation_manager.validate_action(agent_id, action, delegation_id):
                return False, f"Action '{action}' not allowed under delegation {delegation_id}"
        
        # Require approval for restricted agents
        if trust.level == TrustLevel.RESTRICTED:
            return False, "Agent is restricted - requires human approval"
        
        return True, "Action allowed"


# ============================================================================
# TRUST LAYER (MAIN INTERFACE)
# ============================================================================

class TrustLayer:
    """Main interface for the multi-agent trust layer"""
    
    def __init__(self):
        self.identity_registry = IdentityRegistry()
        self.trust_engine = TrustScoringEngine()
        self.delegation_manager = DelegationManager(self.identity_registry, self.trust_engine)
        self.policy_engine = MultiAgentPolicyEngine(self.trust_engine, self.delegation_manager)
        self.audit_log: List[AuditEntry] = []
    
    def register_agent(
        self,
        agent_id: str,
        human_sponsor: str,
        organization: str,
        roles: List[str],
        initial_trust: int = 700
    ) -> bool:
        """Register a new agent with the trust layer"""
        
        # Generate a key pair (simplified)
        public_key = hashlib.sha256(f"{agent_id}:{secrets.token_hex(16)}".encode()).hexdigest()
        
        identity = AgentIdentity(
            agent_id=agent_id,
            public_key=public_key,
            human_sponsor=human_sponsor,
            organization=organization,
            roles=roles
        )
        
        if self.identity_registry.register(identity):
            self.trust_engine.initialize(agent_id, initial_trust)
            return True
        return False
    
    def create_delegation(
        self,
        from_agent: str,
        to_agent: str,
        scope: Dict[str, Any],
        task_description: str,
        time_limit_minutes: int = 60
    ) -> Optional[str]:
        """Create a delegation from one agent to another"""
        
        delegation_scope = DelegationScope(
            allowed_actions=set(scope.get("allowed_actions", [])),
            denied_actions=set(scope.get("denied_actions", [])),
            allowed_domains=set(scope.get("allowed_domains", [])),
            max_tokens=scope.get("max_tokens", 10000),
            time_limit_minutes=time_limit_minutes,
            max_sub_delegations=scope.get("max_sub_delegations", 0)
        )
        
        delegation = self.delegation_manager.create_delegation(
            parent_agent=from_agent,
            child_agent=to_agent,
            scope=delegation_scope,
            task_description=task_description,
            time_limit_minutes=time_limit_minutes
        )
        
        return delegation.delegation_id if delegation else None
    
    def authorize_action(
        self,
        agent_id: str,
        action: str,
        delegation_id: Optional[str] = None
    ) -> tuple[bool, str]:
        """Authorize an action for an agent"""
        
        identity = self.identity_registry.get(agent_id)
        if not identity:
            self._log_audit(agent_id, action, "denied", delegation_id, {"reason": "Unknown agent"})
            return False, "Unknown agent"
        
        allowed, reason = self.policy_engine.evaluate(
            agent_id=agent_id,
            action=action,
            roles=identity.roles,
            delegation_id=delegation_id
        )
        
        # Update trust score based on result
        if allowed:
            self.trust_engine.record_event(agent_id, "stayed_in_scope")
        else:
            self.trust_engine.record_event(agent_id, "scope_violation_attempt")
        
        self._log_audit(
            agent_id, action,
            "allowed" if allowed else "denied",
            delegation_id,
            {"reason": reason}
        )
        
        return allowed, reason
    
    def record_task_result(self, agent_id: str, delegation_id: str, success: bool):
        """Record the result of a delegated task"""
        if success:
            self.trust_engine.record_event(agent_id, "task_completed")
            self.trust_engine.record_event(
                self.delegation_manager.delegations[delegation_id].parent_agent,
                "delegation_success"
            )
        else:
            self.trust_engine.record_event(agent_id, "delegation_failure")
    
    def get_trust_score(self, agent_id: str) -> Optional[int]:
        """Get an agent's trust score"""
        trust = self.trust_engine.get(agent_id)
        return trust.score if trust else None
    
    def get_trust_level(self, agent_id: str) -> Optional[TrustLevel]:
        """Get an agent's trust level"""
        trust = self.trust_engine.get(agent_id)
        return trust.level if trust else None
    
    def _log_audit(
        self,
        agent_id: str,
        action: str,
        result: str,
        delegation_id: Optional[str],
        details: Dict[str, Any]
    ):
        """Log an audit entry"""
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            event_type="action_authorization",
            agent_id=agent_id,
            action=action,
            delegation_id=delegation_id,
            result=result,
            details=details
        )
        self.audit_log.append(entry)
    
    def get_audit_log(self, agent_id: Optional[str] = None) -> List[Dict]:
        """Get audit log, optionally filtered by agent"""
        entries = self.audit_log
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "agent_id": e.agent_id,
                "action": e.action,
                "delegation_id": e.delegation_id,
                "result": e.result,
                "details": e.details
            }
            for e in entries
        ]


# ============================================================================
# EXAMPLE: GOVERNED MULTI-AGENT SYSTEM
# ============================================================================

class GovernedAgent:
    """An agent that operates within the trust layer"""
    
    def __init__(self, agent_id: str, trust_layer: TrustLayer):
        self.agent_id = agent_id
        self.trust_layer = trust_layer
        self.current_delegation: Optional[str] = None
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action through the trust layer"""
        
        allowed, reason = self.trust_layer.authorize_action(
            self.agent_id,
            action,
            self.current_delegation
        )
        
        if not allowed:
            return {
                "success": False,
                "error": f"Action denied: {reason}",
                "trust_score": self.trust_layer.get_trust_score(self.agent_id)
            }
        
        # Simulate action execution
        result = self._execute_action(action, params)
        
        return {
            "success": True,
            "result": result,
            "trust_score": self.trust_layer.get_trust_score(self.agent_id)
        }
    
    def _execute_action(self, action: str, params: Dict[str, Any]) -> str:
        """Simulate executing an action"""
        return f"Executed {action} with params {params}"


# ============================================================================
# MAIN DEMO
# ============================================================================

def main():
    print("🤝 Multi-Agent Trust Layer Demo")
    print("=" * 40)
    
    # Initialize trust layer
    trust_layer = TrustLayer()
    
    # Add role policies
    trust_layer.policy_engine.add_role_policy("researcher", {
        "base_trust_required": 500,
        "allowed_actions": ["web_search", "read_document", "summarize", "analyze"],
        "denied_actions": ["execute_code", "send_email", "delete_file"]
    })
    
    trust_layer.policy_engine.add_role_policy("writer", {
        "base_trust_required": 600,
        "allowed_actions": ["write_document", "edit_document", "summarize"],
        "denied_actions": ["execute_code", "web_search"]
    })
    
    trust_layer.policy_engine.add_role_policy("orchestrator", {
        "base_trust_required": 800,
        "allowed_actions": [],  # Can do anything not explicitly denied
        "denied_actions": ["delete_system_files"]
    })
    
    # Register agents
    print("\n📋 Registering agents...")
    
    trust_layer.register_agent(
        agent_id="orchestrator-001",
        human_sponsor="alice@company.com",
        organization="Acme Corp",
        roles=["orchestrator"],
        initial_trust=900
    )
    print("✅ Registered: orchestrator-001 (Sponsor: alice@company.com)")
    
    trust_layer.register_agent(
        agent_id="researcher-002",
        human_sponsor="bob@company.com",
        organization="Acme Corp",
        roles=["researcher"],
        initial_trust=750
    )
    print("✅ Registered: researcher-002 (Sponsor: bob@company.com)")
    
    trust_layer.register_agent(
        agent_id="writer-003",
        human_sponsor="carol@company.com",
        organization="Acme Corp",
        roles=["writer"],
        initial_trust=700
    )
    print("✅ Registered: writer-003 (Sponsor: carol@company.com)")
    
    # Create delegation chain
    print("\n🔐 Creating delegation chain...")
    
    delegation_id = trust_layer.create_delegation(
        from_agent="orchestrator-001",
        to_agent="researcher-002",
        scope={
            "allowed_actions": ["web_search", "summarize"],
            "allowed_domains": ["arxiv.org", "github.com"],
            "max_tokens": 50000
        },
        task_description="Research recent papers on AI safety",
        time_limit_minutes=30
    )
    print(f"✅ Delegation: orchestrator-001 → researcher-002")
    print(f"   ID: {delegation_id}")
    print(f"   Scope: web_search, summarize")
    print(f"   Time Limit: 30 minutes")
    
    # Create governed agents
    researcher = GovernedAgent("researcher-002", trust_layer)
    researcher.current_delegation = delegation_id
    
    writer = GovernedAgent("writer-003", trust_layer)
    
    # Test actions
    print("\n" + "=" * 40)
    print("🧪 Testing Agent Actions")
    print("=" * 40)
    
    # Test 1: Allowed action within delegation
    print("\n🤖 researcher-002: web_search (within scope)")
    result = researcher.execute("web_search", {"query": "AI safety papers 2024"})
    print(f"   Result: {'✅ ALLOWED' if result['success'] else '❌ DENIED'}")
    print(f"   Trust Score: {result['trust_score']}")
    
    # Test 2: Denied action outside delegation
    print("\n🤖 researcher-002: send_email (outside scope)")
    result = researcher.execute("send_email", {"to": "test@example.com"})
    print(f"   Result: {'✅ ALLOWED' if result['success'] else '❌ DENIED'}")
    if not result['success']:
        print(f"   Reason: {result['error']}")
    print(f"   Trust Score: {result['trust_score']}")
    
    # Test 3: Writer tries action not in role
    print("\n🤖 writer-003: web_search (not in role)")
    result = writer.execute("web_search", {"query": "test"})
    print(f"   Result: {'✅ ALLOWED' if result['success'] else '❌ DENIED'}")
    if not result['success']:
        print(f"   Reason: {result['error']}")
    print(f"   Trust Score: {result['trust_score']}")
    
    # Test 4: Writer does allowed action
    print("\n🤖 writer-003: write_document (in role)")
    result = writer.execute("write_document", {"content": "Report draft"})
    print(f"   Result: {'✅ ALLOWED' if result['success'] else '❌ DENIED'}")
    print(f"   Trust Score: {result['trust_score']}")
    
    # Show final trust scores
    print("\n" + "=" * 40)
    print("📊 Final Trust Scores")
    print("=" * 40)
    
    for agent_id in ["orchestrator-001", "researcher-002", "writer-003"]:
        score = trust_layer.get_trust_score(agent_id)
        level = trust_layer.get_trust_level(agent_id)
        print(f"   {agent_id}: {score} ({level.value})")
    
    # Show audit log
    print("\n" + "=" * 40)
    print("📋 Audit Log")
    print("=" * 40)
    
    for entry in trust_layer.get_audit_log():
        status = "✅" if entry["result"] == "allowed" else "❌"
        print(f"   {status} {entry['agent_id']}: {entry['action']} - {entry['result']}")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
