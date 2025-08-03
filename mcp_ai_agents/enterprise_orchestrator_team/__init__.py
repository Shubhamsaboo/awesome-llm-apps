"""
Enterprise MCP AI Agent Team

A production-grade multi-agent system built with Google ADK that orchestrates 
knowledge management across local files and SaaS platforms using MCP 
(Model Context Protocol).

This package provides:
- File Analysis AI Agent for local document processing
- Notion AI Agent for Notion workspace management
- GitHub AI Agent for repository and issue management
- Figma AI Agent for design file management
- Enterprise MCP AI Agent Team (Router/Orchestrator) for intelligent task coordination
"""

from .agent import (
    EnterpriseMCPAIAgentTeam,
    root_agent  # Add root_agent for ADK web
)

__version__ = "1.0.0"
__author__ = "Enterprise MCP AI Agent Team"
__description__ = "Multi-agent knowledge management system with Google ADK and MCP"

__all__ = [
    "EnterpriseMCPAIAgentTeam",
    "root_agent"  # Export root_agent
]