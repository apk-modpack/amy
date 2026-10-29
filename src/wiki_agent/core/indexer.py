from datetime import datetime
from typing import Dict, List, Optional
from wiki_agent.backends.base import BaseWikiBackend
from wiki_agent.models import WikiPage, PageMetadata


class WikiIndexer:
    """Generador automÃ¡tico de Mapas de Contenido (MOCs) e Ãndices por CategorÃ­a."""

    def __init__(self, backend: BaseWikiBackend):
        self.backend = backend

    def generate_category_index(self, category: str) -> WikiPage:
        """Crea o actualiza la pÃ¡gina de Ã­ndice MOC de una categorÃ­a especÃ­fica."""
        titles = self.backend.list_pages(category=category)
        index_title = f"Ãndice_{category}"

        # Filtrar el propio Ã­ndice si ya existe en la lista
        concept_titles = [t for t in titles if t != index_title]

        lines = [
            f"# Mapa de Contenido: {category}\n",
            f"Ãndice generado automÃ¡ticamente para la categorÃ­a **{category}**.\n",
            f"Total de conceptos registrados: **{len(concept_titles)}**\n",
            "## Conceptos Disponibles\n"
        ]

        if not concept_titles:
            lines.append("_No hay conceptos registrados en esta categorÃ­a aÃºn._\n")
        else:
            for t in sorted(concept_titles):
                page = self.backend.read_page(t)
                tags_str = f" `[{', '.join(page.metadata.tags)}]`" if page and page.metadata.tags else ""
                lines.append(f"- [[{t}]]{tags_str}")

        lines.append(f"\n---\n_Ãšltima actualizaciÃ³n: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}_")
        content = "\n".join(lines)

        meta = PageMetadata(
            title=index_title,
            category=category,
            tags=["Ã­ndice", "moc", "sistema"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        page = WikiPage(metadata=meta, content=content)
        self.backend.write_page(page)
        return page

    def generate_global_index(self) -> WikiPage:
        """Crea o actualiza el Ã­ndice maestro global de la Wiki."""
        all_pages = self.backend.get_all_pages()
        categories: Dict[str, List[str]] = {}

        for p in all_pages:
            if p.title.startswith("Ãndice_") or p.title == "Ãndice_Maestro":
                continue
            cat = p.metadata.category or "General"
            categories.setdefault(cat, []).append(p.title)

        lines = [
            "# Ãndice Maestro de Conocimientos\n",
            "VisiÃ³n global de todas las categorÃ­as y conceptos integrados en la memoria de la IA.\n",
            "## CategorÃ­as Registradas\n"
        ]

        for cat, items in sorted(categories.items()):
            lines.append(f"### ðŸ“‚ {cat} (Total: {len(items)})")
            lines.append(f"- [[Ãndice_{cat}|Ver Ãndice Detallado de {cat}]]")
            for item in sorted(items)[:5]:  # Muestra previa de 5 conceptos
                lines.append(f"  - [[{item}]]")
            if len(items) > 5:
                lines.append(f"  - _... y {len(items) - 5} conceptos mÃ¡s._")
            lines.append("")

        lines.append(f"\n---\n_Ãšltima sincronizaciÃ³n global: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}_")
        content = "\n".join(lines)

        meta = PageMetadata(
            title="Ãndice_Maestro",
            category="Sistema",
            tags=["Ã­ndice", "maestro", "sistema"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        page = WikiPage(metadata=meta, content=content)
        self.backend.write_page(page)
        return page