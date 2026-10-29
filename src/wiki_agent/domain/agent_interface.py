"""Interfaces y contratos abstractos para agentes de Inteligencia Artificial."""

from abc import ABC, abstractmethod
from typing import Optional, Callable
from wiki_agent.domain.actions import AgentTurnResult


class CognitiveAgent(ABC):
    """Contrato base para cualquier agente IA en el sistema."""

    @abstractmethod
    def chat(
        self,
        user_message: str,
        stream_callback: Optional[Callable[[str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        bytes_callback: Optional[Callable[[int], None]] = None,
    ) -> AgentTurnResult:
        """Procesa una consulta del usuario y devuelve un AgentTurnResult."""
        pass

    @abstractmethod
    def clear_history(self) -> None:
        """Reinicia el contexto conversacional del agente."""
        pass

    @property
    @abstractmethod
    def turn_count(self) -> int:
        """Número de turnos ejecutados en la sesión."""
        pass
