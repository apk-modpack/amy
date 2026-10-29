"""Dominio para comandos internos del agente y resultados de ejecución.

Modela las acciones internas del agente como objetos fuertemente tipados
en lugar de cadenas de texto partidas con regex o splits manuales.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


class ActionType(str, Enum):
    """Tipos de acciones soportadas por el agente."""
    SEARCH = "search"
    READ = "read"
    SAVE = "save"
    EDIT = "edit"
    DELETE = "delete"


@dataclass(frozen=True)
class ParsedCommand:
    """Representa un comando emitido por el modelo con sus parámetros validados."""
    action: ActionType
    argument: str

    @classmethod
    def from_raw_string(cls, raw_cmd: str) -> Optional["ParsedCommand"]:
        """Intenta parsear una línea tipo '/save \"Título\"' en un ParsedCommand."""
        clean = raw_cmd.strip()
        parts = clean.split(maxsplit=1)
        if not parts:
            return None

        cmd_name = parts[0].lower().lstrip("/")
        arg = parts[1].strip().strip('"').strip("'") if len(parts) > 1 else ""

        try:
            action = ActionType(cmd_name)
            return cls(action=action, argument=arg)
        except ValueError:
            return None

    def to_slash_string(self) -> str:
        """Devuelve la representación tradicional en slash command."""
        return f"/{self.action.value} \"{self.argument}\"" if self.argument else f"/{self.action.value}"


@dataclass(frozen=True)
class CommandExecutionResult:
    """Resultado de la ejecución de una acción interna."""
    command: ParsedCommand
    success: bool
    output: str


@dataclass(frozen=True)
class AgentTurnResult:
    """Resultado completo de un turno de ejecución del agente.

    Sustituye la tupla mágica (human_response, commands, concepts)
    por un objeto de dominio rico y fuertemente tipado.
    """
    response_text: str
    concepts_consulted: List[str] = field(default_factory=list)
    executed_commands: List[str] = field(default_factory=list)
    thoughts: List[str] = field(default_factory=list)
    turn_latency: float = 0.0
    tokens_per_second: float = 0.0

    @property
    def has_actions(self) -> bool:
        """Indica si el agente ejecutó alguna acción interna en el turno."""
        return len(self.executed_commands) > 0

    def __iter__(self):
        """Permite desempaquetar como tupla (response_text, executed_commands, concepts_consulted) para compatibilidad."""
        return iter((self.response_text, self.executed_commands, self.concepts_consulted))

    def __getitem__(self, index: int):
        """Permite acceso por índice como tupla (response_text, executed_commands, concepts_consulted)."""
        return (self.response_text, self.executed_commands, self.concepts_consulted)[index]
