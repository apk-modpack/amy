"""Dominio puro de conversación para el Agente IA.

Define entidades, value objects y colecciones de conversación con invariantes protegidas,
eliminando el uso de diccionarios crudos y tuplas desestructuradas.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


class MessageRole(str, Enum):
    """Roles válidos para los mensajes en el dominio de IA."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_OBSERVATION = "tool_observation"


@dataclass(frozen=True)
class Message:
    """Value object inmutable que representa un mensaje en la conversación."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_llm_dict(self) -> Dict[str, str]:
        """Convierte el mensaje al formato estándar que esperan los proveedores LLM."""
        # Las observaciones de herramientas se transmiten al LLM con el rol 'user' (observación del sistema)
        role_str = "user" if self.role == MessageRole.TOOL_OBSERVATION else self.role.value
        return {"role": role_str, "content": self.content}

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role=MessageRole.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        return cls(role=MessageRole.ASSISTANT, content=content)

    @classmethod
    def tool_observation(cls, content: str) -> "Message":
        return cls(role=MessageRole.TOOL_OBSERVATION, content=content)


class ConversationHistory:
    """Colección orientada a objetos (Aggregate) que gestiona el historial conversacional."""

    def __init__(self, initial_messages: Optional[List[Message]] = None):
        self._messages: List[Message] = list(initial_messages) if initial_messages else []

    def add_user_message(self, text: str) -> Message:
        msg = Message.user(f"[ENTRADA HUMANA]\n{text}")
        self._messages.append(msg)
        return msg

    def add_assistant_message(self, content: str) -> Message:
        msg = Message.assistant(content)
        self._messages.append(msg)
        return msg

    def add_tool_observation(self, content: str) -> Message:
        msg = Message.tool_observation(content)
        self._messages.append(msg)
        return msg

    def clear(self):
        """Limpia el historial de la conversación."""
        self._messages.clear()

    @property
    def messages(self) -> List[Message]:
        return list(self._messages)

    @property
    def turn_count(self) -> int:
        """Número de turnos iniciados por el usuario humano."""
        return sum(1 for m in self._messages if m.role == MessageRole.USER and "[ENTRADA HUMANA]" in m.content)

    def to_llm_payload(self, system_prompts: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """Construye la lista completa de diccionarios lista para ser enviada al LLM."""
        payload: List[Dict[str, str]] = []
        if system_prompts:
            for sys_text in system_prompts:
                payload.append(Message.system(sys_text).to_llm_dict())
        for m in self._messages:
            payload.append(m.to_llm_dict())
        return payload
