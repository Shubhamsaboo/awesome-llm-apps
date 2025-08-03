"""
Enterprise Knowledge Orchestrator

A production-grade multi-agent system built with Google ADK that orchestrates 
knowledge management across local files and SaaS platforms using MCP 
(Model Context Protocol).

This package provides:
- File Analysis Agent for local document processing
- Notion Agent for Notion workspace management
- GitHub Agent for repository and issue management
- Figma Agent for design file management
- Router/Orchestrator Agent for intelligent task coordination
"""

from .agent import (
    EnterpriseKnowledgeOrchestrator,
    root_agent  # Add root_agent for ADK web
)

__version__ = "1.0.0"
__author__ = "Enterprise Knowledge Team"
__description__ = "Multi-agent knowledge management system with Google ADK and MCP"

__all__ = [
    "EnterpriseKnowledgeOrchestrator",
    "root_agent"  # Export root_agent
]