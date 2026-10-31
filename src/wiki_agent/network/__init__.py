"""Módulo de red y comunicación cliente-servidor para Wiki-Memory Agent."""

from wiki_agent.network.protocol import (
    NetworkMessage,
    MessageType,
    AgentState,
    PROTOCOL_VERSION,
    make_handshake,
    make_handshake_ack,
    make_chat_message,
    make_agent_response,
    make_agent_status,
    make_error,
)
from wiki_agent.network.connection import RobustSocketConnection
from wiki_agent.network.server import ChatRoomServer, get_local_ip_addresses
from wiki_agent.network.client import AgentNetworkClient

__all__ = [
    "NetworkMessage",
    "MessageType",
    "AgentState",
    "PROTOCOL_VERSION",
    "RobustSocketConnection",
    "ChatRoomServer",
    "AgentNetworkClient",
    "get_local_ip_addresses",
    "make_handshake",
    "make_handshake_ack",
    "make_chat_message",
    "make_agent_response",
    "make_agent_status",
    "make_error",
]

