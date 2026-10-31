"""Definición del protocolo de comunicación de red entre la Sala de Chat y el Agente IA.

Diseñado bajo el principio de robustez, extensibilidad y desacoplamiento para resistir
cambios de sistemas y lenguajes futuros:
- Mensajes JSON delimitados por salto de línea ('\\n') [Newline-Delimited JSON].
- Versionado explícito de protocolo.
- Tipos de mensajes estructurados para ciclo de vida, mensajes, estado y métricas.
"""

import json
import time
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


PROTOCOL_VERSION = 1


class AgentState(str, Enum):
    """Estados formales del Agente IA visibles desde la Sala de Chat.

    Estos son los únicos estados válidos que el agente puede comunicar al servidor.
    Cualquier estado que no sea uno de éstos debe ser ignorado por el receptor.
    """
    LISTO      = "LISTO"       # El agente está disponible y esperando input
    PROCESANDO = "PROCESANDO"  # El agente está ejecutando un turno de razonamiento
    ERROR      = "ERROR"       # El agente encontró un error en el último turno


class MessageType(str, Enum):
    """Tipos de mensajes admitidos en el protocolo."""
    # Control y ciclo de vida de conexión
    HANDSHAKE = "handshake"
    HANDSHAKE_ACK = "handshake_ack"
    PING = "ping"
    PONG = "pong"
    DISCONNECT = "disconnect"
    ERROR = "error"

    # Conversación y estado
    CHAT_MESSAGE = "chat_message"       # Enviado desde la Sala de Chat hacia la IA
    AGENT_STATUS = "agent_status"       # Estado del agente (usa AgentState como valor de 'state')
    AGENT_RESPONSE = "agent_response"   # Respuesta final generada por la IA
    AGENT_LIST = "agent_list"           # Lista y presencia de agentes conectados en la sala


class NetworkMessage(BaseModel):
    """Estructura canónica de un mensaje de red."""
    version: int = Field(default=PROTOCOL_VERSION, description="Versión del protocolo")
    type: MessageType = Field(..., description="Tipo de mensaje")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Datos asociados al mensaje")
    timestamp: float = Field(default_factory=time.time, description="Timestamp UNIX en segundos")

    def to_json_line(self) -> bytes:
        """Serializa el mensaje a bytes JSON terminados en '\\n' para transmisión TCP."""
        data = self.model_dump(mode="json")
        return (json.dumps(data, ensure_ascii=False) + "\n").encode("utf-8")

    @classmethod
    def from_json_line(cls, line: str) -> "NetworkMessage":
        """Deserializa una línea JSON en un objeto NetworkMessage validado."""
        clean_line = line.strip()
        if not clean_line:
            raise ValueError("Línea vacía recibida en protocolo de red.")
        data = json.loads(clean_line)
        return cls(**data)


# --- Funciones constructoras de conveniencia ---

HUMAN_SENDER = "HUMAN"


def make_agent_list(agents: list) -> NetworkMessage:
    """Crea un mensaje con la lista de agentes conectados actualmente."""
    return NetworkMessage(
        type=MessageType.AGENT_LIST,
        payload={"agents": agents}
    )


def make_handshake(client_name: str, model_name: str, client_id: str = "", capabilities: Optional[list] = None) -> NetworkMessage:
    """Crea un mensaje de presentación del cliente (Agente IA)."""
    return NetworkMessage(
        type=MessageType.HANDSHAKE,
        payload={
            "client_name": client_name,
            "client_id": client_id,
            "model_name": model_name,
            "capabilities": capabilities or ["react_agent", "wiki_memory", "streaming_status", "identify"],
        }
    )


def make_handshake_ack(server_name: str = "Wiki-Memory Chat Room") -> NetworkMessage:
    """Crea la confirmación de handshake desde el servidor."""
    return NetworkMessage(
        type=MessageType.HANDSHAKE_ACK,
        payload={"server_name": server_name, "status": "ready"}
    )


def make_chat_message(text: str, sender: str = HUMAN_SENDER) -> NetworkMessage:
    """Crea un mensaje de conversación. Por defecto sender es 'HUMAN'."""
    return NetworkMessage(
        type=MessageType.CHAT_MESSAGE,
        payload={"text": text, "sender": sender}
    )


def make_agent_response(text: str, metadata: Optional[Dict[str, Any]] = None) -> NetworkMessage:
    """Crea un mensaje con la respuesta final de la IA."""
    return NetworkMessage(
        type=MessageType.AGENT_RESPONSE,
        payload={
            "text": text,
            "metadata": metadata or {}
        }
    )


def make_agent_status(state: "AgentState | str" = None, detail: str = "", status: "AgentState | str" = None) -> NetworkMessage:
    """Crea un mensaje de actualización de estado del agente.

    Args:
        state: Estado formal del agente (AgentState.LISTO / PROCESANDO / ERROR).
               También se acepta string crudo para compatibilidad hacia atrás.
        detail: Descripción opcional con contexto adicional (ej. 'Ciclo 2 de razonamiento').
        status: Alias de conveniencia retrocompatible para 'state'.
    """
    actual_state = state if state is not None else status
    state_value = actual_state.value if isinstance(actual_state, AgentState) else str(actual_state or "")
    return NetworkMessage(
        type=MessageType.AGENT_STATUS,
        payload={"state": state_value, "detail": detail}
    )


def make_error(error_message: str, code: str = "GENERAL_ERROR") -> NetworkMessage:
    """Crea un mensaje de reporte de error."""
    return NetworkMessage(
        type=MessageType.ERROR,
        payload={"error": error_message, "code": code}
    )


def make_ping() -> NetworkMessage:
    return NetworkMessage(type=MessageType.PING)


def make_pong() -> NetworkMessage:
    return NetworkMessage(type=MessageType.PONG)

