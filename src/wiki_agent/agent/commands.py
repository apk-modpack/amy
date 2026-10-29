"""Sistema de comandos internos del agente basado en el patrón Command / Dispatcher.

Desacopla la ejecución de comandos (/search, /read, /save, /edit, /delete) del bucle
del agente, permitiendo registrar nuevos comandos y testearlos de forma aislada.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class AgentCommand(ABC):
    """Clase base abstracta para comandos internos del agente."""

    def __init__(self, agent: Any):
        self.agent = agent

    @abstractmethod
    def execute(self, argument: str) -> str:
        """Ejecuta el comando con el argumento provisto y devuelve el resultado en texto."""
        pass


class SearchCommand(AgentCommand):
    """Ejecuta una búsqueda de conceptos en la Wiki."""

    def execute(self, argument: str) -> str:
        query = argument.strip().strip('"').strip("'")
        if not query:
            return "Error: Comando /search requiere un término de búsqueda."
        results = self.agent.manager.search_knowledge(query, limit=5)
        if not results:
            return f"Sin resultados para la búsqueda '{query}'."
        return "Resultados de búsqueda:\n" + "\n".join(f"- [[{r.title}]]: {r.snippet}" for r in results)


class ReadCommand(AgentCommand):
    """Recupera el contexto completo y detallado de un concepto."""

    def execute(self, argument: str) -> str:
        title = argument.strip().strip('"').strip("'")
        if not title:
            return "Error: Comando /read requiere un título."
        logger.info("ReadCommand | Leyendo concepto completo: %r", title)
        return self.agent.assistant.get_concept_full_context(title)


class SaveCommand(AgentCommand):
    """Guarda un nuevo concepto en la Wiki delegando en agent.save_last_response."""

    def execute(self, argument: str) -> str:
        title = argument.strip().strip('"').strip("'") or "Concepto Generado"
        res = self.agent.save_last_response(title)
        return f"Éxito: {res}" if res.startswith("✓") else res


class EditCommand(AgentCommand):
    """Modifica un concepto existente en la Wiki delegando en agent.save_last_response."""

    def execute(self, argument: str) -> str:
        title = argument.strip().strip('"').strip("'") or "Concepto Editado"
        res = self.agent.save_last_response(title)
        return f"Éxito: {res}" if res.startswith("✓") else res


class DeleteCommand(AgentCommand):
    """Elimina un concepto de la Wiki."""

    def execute(self, argument: str) -> str:
        title = argument.strip().strip('"').strip("'")
        if not title:
            return "Error: Comando /delete requiere un título."
        res = self.agent.delete_concept(title)
        return f"Éxito: {res}" if res.startswith("✓") else res


class CommandDispatcher:
    """Despachador orientado a objetos para comandos internos del agente."""

    def __init__(self, agent: Any):
        self.agent = agent
        self._registry: Dict[str, AgentCommand] = {}
        self._register_default_commands()

    def _register_default_commands(self):
        self.register("/search", SearchCommand(self.agent))
        self.register("/read", ReadCommand(self.agent))
        self.register("/save", SaveCommand(self.agent))
        self.register("/edit", EditCommand(self.agent))
        self.register("/delete", DeleteCommand(self.agent))

    def register(self, command_name: str, handler: AgentCommand):
        """Registra un nuevo manejador para un comando."""
        self._registry[command_name.lower()] = handler

    def dispatch(self, raw_cmd: str) -> str:
        """Parsea la línea de comando y la despacha al manejador correspondiente."""
        clean = raw_cmd.strip()
        parts = clean.split(maxsplit=1)
        if not parts:
            return "Error: Comando vacío."

        name = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        handler = self._registry.get(name)
        if not handler:
            return f"Error: Comando no reconocido '{clean}'"

        try:
            return handler.execute(arg)
        except Exception as e:
            logger.error("Error ejecutando comando interno %s: %s", clean, e, exc_info=True)
            return f"Error ejecutando comando: {e}"
