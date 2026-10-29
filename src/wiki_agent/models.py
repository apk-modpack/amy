from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Tipos de relación semántica soportados entre conceptos.
RELATION_TYPES = {"relates_to", "is_a", "part_of", "depends_on", "contradicts", "precedes"}


class PageMetadata(BaseModel):
    """Metadatos asociados a una página o concepto en la Wiki."""
    title: str
    category: str = "General"
    tags: List[str] = Field(default_factory=list)
    aliases: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source_documents: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


class ConceptRelation(BaseModel):
    """Relación semántica explícita entre dos conceptos del grafo de conocimiento."""
    source: str
    target: str
    relation_type: str = "relates_to"  # relates_to, is_a, part_of, depends_on, contradicts, precedes
    description: Optional[str] = None


class WikiPage(BaseModel):
    """Representación unificada de un concepto en la Wiki.

    El campo `content` contiene el texto principal (definición) del concepto.
    El campo `sections` almacena secciones adicionales con nombre (e.g. "Ejemplos", "Notas").
    El campo `relations` contiene las relaciones semánticas explícitas con otros conceptos.
    Los campos `outgoing_links` y `backlinks` se mantienen por compatibilidad con el
    sistema de búsqueda de backlinks heredado.
    """
    metadata: PageMetadata
    content: str
    sections: Dict[str, str] = Field(default_factory=dict)
    relations: List[ConceptRelation] = Field(default_factory=list)
    outgoing_links: List[str] = Field(default_factory=list)
    backlinks: List[str] = Field(default_factory=list)

    @property
    def title(self) -> str:
        return self.metadata.title

    def get_relation_targets(self) -> List[str]:
        """Devuelve los títulos de todos los conceptos con los que este tiene relación explícita."""
        return [r.target for r in self.relations]


class SearchResult(BaseModel):
    """Resultado de búsqueda en la Wiki."""
    title: str
    category: str
    tags: List[str]
    snippet: str
    score: float
    path: Optional[str] = None


class TrainingExample(BaseModel):
    """Ejemplo para entrenamiento de IA local."""
    prompt: str
    response: str
    concept: str
    format_type: str = "sharegpt"
    metadata: Dict[str, Any] = Field(default_factory=dict)