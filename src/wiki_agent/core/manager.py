import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from wiki_agent.backends.base import BaseWikiBackend
from wiki_agent.backends.local_markdown import LocalMarkdownBackend
from wiki_agent.backends.local_xml import LocalXMLBackend
from wiki_agent.models import WikiPage, PageMetadata, ConceptRelation, SearchResult
from wiki_agent.core.health import WikiHealthChecker, WikiHealthReport
from wiki_agent.core.indexer import WikiIndexer


class WikiKnowledgeManager:
    """Motor de gestiÃ³n conceptual y operaciones de alto nivel sobre la Wiki."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.backend = self._init_backend()
        self.health_checker = WikiHealthChecker(self.backend)
        self.indexer = WikiIndexer(self.backend)

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        default_config = {
            "wiki": {
                "backend": "local_xml",
                "local_path": "./data/wiki",
                "default_category": "General",
                "auto_create_links": True
            },
            "retrieval": {
                "search_limit": 10,
            },
            "export": {
                "default_format": "sharegpt",
                "output_dir": "./data/exports"
            }
        }
        if not config_path:
            candidates = ["config.yaml", "../config.yaml", "C:/Users/ENEKO/Desktop/SAUCE/IA/config.yaml"]
            for c in candidates:
                if Path(c).exists():
                    config_path = c
                    break

        if config_path and Path(config_path).exists():
            with open(config_path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
                for k, v in loaded.items():
                    if isinstance(v, dict) and k in default_config:
                        default_config[k].update(v)
                    else:
                        default_config[k] = v

        return default_config

    def _init_backend() -> BaseWikiBackend:
        pass

    def _init_backend(self) -> BaseWikiBackend:
        backend_type = self.config.get("wiki", {}).get("backend", "local_xml")
        local_path = self.config.get("wiki", {}).get("local_path", "./data/wiki")
        if backend_type == "local_xml":
            return LocalXMLBackend(base_path=local_path)
        elif backend_type == "local_markdown":
            return LocalMarkdownBackend(base_path=local_path)
        else:
            raise ValueError(f"Backend no soportado: {backend_type}")

    def get_concept(self, title: str) -> Optional[WikiPage]:
        """Obtiene un concepto con sus enlaces y backlinks."""
        return self.backend.read_page(title)

    def save_concept(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None,
        source_documents: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
        relations: Optional[List[ConceptRelation]] = None,
        sections: Optional[Dict[str, str]] = None,
    ) -> WikiPage:
        """Crea o actualiza un concepto en la Wiki.

        Args:
            title: Título del concepto.
            content: Texto principal (definición) del concepto.
            category: Categoría del concepto.
            tags: Etiquetas del concepto.
            aliases: Nombres alternativos del concepto.
            source_documents: Fuentes de información.
            extra: Metadatos adicionales.
            relations: Relaciones semánticas explícitas con otros conceptos.
            sections: Secciones adicionales con nombre (e.g. {"Ejemplos": "...", "Notas": "..."}).
        """
        existing = self.backend.read_page(title)
        cat = category or (existing.metadata.category if existing else self.config["wiki"]["default_category"])
        t = tags or (existing.metadata.tags if existing else [])
        a = aliases or (existing.metadata.aliases if existing else [])
        sources = source_documents or (existing.metadata.source_documents if existing else [])
        ex = extra or (existing.metadata.extra if existing else {})
        # Para relaciones: se fusionan las existentes con las nuevas (evitando duplicados por target)
        existing_relations = existing.relations if existing else []
        if relations is not None:
            existing_targets = {r.target.lower() for r in relations}
            merged = list(relations) + [r for r in existing_relations if r.target.lower() not in existing_targets]
        else:
            merged = existing_relations
        sec = sections if sections is not None else (existing.sections if existing else {})

        # Si content viene vacío o None y el concepto ya existe, preservar su contenido original
        if (content is None or not content.strip()) and existing:
            final_content = existing.content
        else:
            final_content = content or ""

        metadata = PageMetadata(
            title=title,
            category=cat,
            tags=t,
            aliases=a,
            source_documents=sources,
            extra=ex
        )
        page = WikiPage(metadata=metadata, content=final_content, sections=sec, relations=merged)
        self.backend.write_page(page)
        return page

    def append_note(self, title: str, note: str, section: str = "Notas y Actualizaciones") -> WikiPage:
        """AÃ±ade una nota o actualizaciÃ³n a un concepto existente sin sobreescribirlo."""
        page = self.backend.read_page(title)
        if not page:
            content = f"## {section}\n- {note}\n"
            return self.save_concept(title=title, content=content)

        current_content = page.content
        if f"## {section}" in current_content:
            new_content = current_content.replace(f"## {section}", f"## {section}\n- {note}")
        else:
            new_content = f"{current_content.strip()}\n\n## {section}\n- {note}\n"

        page.content = new_content
        self.backend.write_page(page)
        return page

    def delete_concept(self, title: str) -> bool:
        """Elimina un concepto de la Wiki."""
        return self.backend.delete_page(title)

    def search_knowledge(self, query: str, limit: Optional[int] = None) -> List[SearchResult]:
        """Busca conceptos e informaciÃ³n en la base de conocimientos."""
        l = limit or self.config.get("retrieval", {}).get("search_limit", 10)
        return self.backend.search(query, limit=l)

    def get_concept_network(self, title: str) -> Dict[str, Any]:
        """Obtiene la red semÃ¡ntica inmediata de un concepto."""
        page = self.backend.read_page(title)
        if not page:
            return {"title": title, "exists": False, "outgoing": [], "backlinks": []}

        return {
            "title": page.title,
            "exists": True,
            "category": page.metadata.category,
            "tags": page.metadata.tags,
            "outgoing_links": page.outgoing_links,
            "backlinks": page.backlinks
        }

    def list_all_concepts(self, category: Optional[str] = None) -> List[str]:
        """Lista los conceptos indexados."""
        return self.backend.list_pages(category=category)

    def check_health(self) -> Dict[str, Any]:
        """Ejecuta el diagnÃ³stico de integridad del conocimiento."""
        return self.health_checker.run_diagnostics().to_dict()

    def rebuild_indexes(self) -> List[str]:
        """Reconstruye todos los Ã­ndices por categorÃ­a y el Ã­ndice maestro."""
        all_pages = self.backend.get_all_pages()
        categories = {p.metadata.category for p in all_pages if p.metadata.category and p.metadata.category != "Sistema"}
        created = []
        for cat in categories:
            idx_page = self.indexer.generate_category_index(cat)
            created.append(idx_page.title)
        master = self.indexer.generate_global_index()
        created.append(master.title)
        return created