"""Gestor de Lista de Tareas Cognitivas del Agente.

Permite al agente descomponer peticiones complejas en pasos discretos,
seguir su progreso durante turnos multi-ciclo y determinar si la respuesta está lista.
"""

from typing import List, Dict, Any, Optional
import uuid
import time
import logging

logger = logging.getLogger(__name__)


class TaskItem:
    """Representa una tarea cognitiva discreta dentro del plan del agente."""

    def __init__(self, description: str, task_id: Optional[str] = None, completed: bool = False):
        self.task_id = task_id or str(uuid.uuid4())[:8]
        self.description = description.strip()
        self.completed = completed
        self.created_at = time.time()

    def mark_completed(self):
        self.completed = True

    def mark_pending(self):
        self.completed = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "completed": self.completed,
        }

    def __repr__(self) -> str:
        status = "✓" if self.completed else "○"
        return f"[{status}] {self.description}"


class AgentTaskManager:
    """Gestiona el plan de trabajo cognitivo activo del agente."""

    def __init__(self):
        self._tasks: List[TaskItem] = []

    def clear(self):
        """Limpia la lista completa de tareas."""
        self._tasks.clear()

    def set_tasks(self, descriptions: List[str]):
        """Inicializa la lista de tareas a partir de una lista de descripciones."""
        self._tasks = [TaskItem(desc) for desc in descriptions if desc.strip()]
        logger.info("Plan cognitivo inicializado con %d tareas.", len(self._tasks))

    def add_task(self, description: str) -> TaskItem:
        """Añade una nueva tarea al plan."""
        item = TaskItem(description)
        self._tasks.append(item)
        logger.info("Tarea añadida: %s", item)
        return item

    def complete_task(self, identifier: Any) -> bool:
        """Marca una tarea como completada por índice numérico (1-based), ID o texto."""
        if isinstance(identifier, int):
            idx = identifier - 1
            if 0 <= idx < len(self._tasks):
                self._tasks[idx].mark_completed()
                logger.info("Tarea completada por índice #%d: %s", identifier, self._tasks[idx])
                return True
            return False

        ident_str = str(identifier).strip()
        if ident_str.isdigit():
            idx = int(ident_str) - 1
            if 0 <= idx < len(self._tasks):
                self._tasks[idx].mark_completed()
                logger.info("Tarea completada por índice numérico #%s: %s", ident_str, self._tasks[idx])
                return True
            return False

        ident_lower = ident_str.lower()
        for t in self._tasks:
            if not t.completed and (t.task_id.lower() == ident_lower or ident_lower in t.description.lower()):
                t.mark_completed()
                logger.info("Tarea completada: %s", t)
                return True
        # Si no coincidió específicamente pero hay tareas pendientes, completar la primera no realizada
        for t in self._tasks:
            if not t.completed:
                t.mark_completed()
                logger.info("Tarea completada (siguiente en cola): %s", t)
                return True
        return False

    def complete_next(self) -> Optional[TaskItem]:
        """Marca la siguiente tarea pendiente como completada."""
        for t in self._tasks:
            if not t.completed:
                t.mark_completed()
                logger.info("Siguiente tarea completada: %s", t)
                return t
        return None

    @property
    def has_pending_tasks(self) -> bool:
        """Indica si quedan tareas pendientes de ejecución."""
        return any(not t.completed for t in self._tasks)

    @property
    def pending_tasks(self) -> List[TaskItem]:
        return [t for t in self._tasks if not t.completed]

    @property
    def completed_tasks(self) -> List[TaskItem]:
        return [t for t in self._tasks if t.completed]

    @property
    def total_count(self) -> int:
        return len(self._tasks)

    @property
    def pending_count(self) -> int:
        return len(self.pending_tasks)

    @property
    def completed_count(self) -> int:
        return len(self.completed_tasks)

    def to_list(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._tasks]

    def render_summary(self) -> str:
        """Devuelve una vista formateada en texto de la lista de tareas."""
        if not self._tasks:
            return "Sin tareas activas."
        lines = []
        for i, t in enumerate(self._tasks, 1):
            mark = "[x]" if t.completed else "[ ]"
            lines.append(f"{mark} {i}. {t.description}")
        return "\n".join(lines)
