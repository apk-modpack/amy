"""Gestor de Identidad del Agente IA.

Maneja la persistencia y lectura de la identidad local del agente:
- Almacena agent_id único, agent_name y timestamp de creación.
- Si el archivo no existe, genera un nombre aleatorio persistente.
- Regla estricta: 'HUMAN' es un nombre reservado y jamás puede ser adoptado por un agente.
"""

import json
import os
import random
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

RESERVED_NAMES = {"HUMAN", "HUMANO", "USER", "USUARIO"}

ADJECTIVES = [
    "Nexus", "Cyber", "Aura", "Quantum", "Vector", "Echo", "Prism",
    "Synapse", "Nova", "Apex", "Logic", "Cortex", "Stellar", "Hyper",
    "Neural", "Vortex", "Matrix", "Kinetics", "Astral", "Helios"
]

NOUNS = [
    "Agent", "Core", "Mind", "Pilot", "Scribe", "Node", "Weaver",
    "Watcher", "Archon", "Spark", "Seeker", "Engine", "Beacon",
    "Guardian", "Catalyst", "Oracle", "Cipher", "Sentinel"
]


def generate_random_agent_name() -> str:
    """Genera un nombre aleatorio distintivo para el agente."""
    adj = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    num = random.randint(10, 99)
    name = f"{adj}-{noun}-{num}"
    if name.upper() in RESERVED_NAMES:
        return f"Agent-{uuid.uuid4().hex[:6]}"
    return name


class AgentIdentityManager:
    """Administra la identidad persistente de este agente."""

    DEFAULT_PATH = Path("data/agent_identity.json")

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = Path(file_path) if file_path else self.DEFAULT_PATH
        self._identity: Dict[str, Any] = {}
        self.load_or_create()

    @property
    def agent_id(self) -> str:
        return self._identity.get("agent_id", "")

    @property
    def agent_name(self) -> str:
        return self._identity.get("agent_name", "Desconocido")

    def load_or_create(self) -> Dict[str, Any]:
        """Carga la identidad existente o crea una nueva con nombre aleatorio."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                name = str(data.get("agent_name", "")).strip()
                if not name or name.upper() in RESERVED_NAMES:
                    logger.warning("Nombre de agente inválido o reservado ('%s'). Regenerando.", name)
                    data["agent_name"] = generate_random_agent_name()
                    self._save(data)
                self._identity = data
                logger.info("Identidad de agente cargada: %s (ID: %s)", self.agent_name, self.agent_id)
                return self._identity
            except Exception as e:
                logger.error("Error al leer archivo de identidad (%s): %s. Se regenerará.", self.file_path, e)

        # Si no existe o hubo error, crear nueva identidad
        new_identity = {
            "agent_id": str(uuid.uuid4()),
            "agent_name": generate_random_agent_name(),
            "created_at": str(uuid.uuid1()),
        }
        self._save(new_identity)
        self._identity = new_identity
        logger.info("Nueva identidad creada: %s (ID: %s)", self.agent_name, self.agent_id)
        return self._identity

    def _save(self, data: Dict[str, Any]):
        """Persiste la identidad en disco de manera segura."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

