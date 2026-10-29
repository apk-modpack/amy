"""Paquete de dominio puro de Wiki Agent.

Contiene entidades de dominio, value objects e interfaces base.
"""

from wiki_agent.domain.chat import Message, MessageRole, ConversationHistory
from wiki_agent.domain.actions import ActionType, ParsedCommand, CommandExecutionResult, AgentTurnResult
from wiki_agent.domain.agent_interface import CognitiveAgent

__all__ = [
    "Message",
    "MessageRole",
    "ConversationHistory",
    "ActionType",
    "ParsedCommand",
    "CommandExecutionResult",
    "AgentTurnResult",
    "CognitiveAgent",
]
