from typing import List, Dict, Any, Set
from wiki_agent.backends.base import BaseWikiBackend
from wiki_agent.models import WikiPage


class WikiHealthReport:
    """Informe detallado sobre la integridad, enlaces y salud de la base de conocimientos."""

    def __init__(self):
        self.total_pages: int = 0
        self.categories: Dict[str, int] = {}
        self.orphan_pages: List[str] = []      # PÃ¡ginas sin ningÃºn backlink
        self.missing_stubs: List[Dict[str, Any]] = []  # Enlaces [[X]] que no existen como pÃ¡ginas
        self.syntax_warnings: List[str] = []   # Advertencias de frontmatter o formato
        self.tag_distribution: Dict[str, int] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_pages": self.total_pages,
            "categories": self.categories,
            "orphan_pages": self.orphan_pages,
            "missing_stubs": self.missing_stubs,
            "syntax_warnings": self.syntax_warnings,
            "tag_distribution": self.tag_distribution,
            "is_healthy": len(self.syntax_warnings) == 0 and len(self.missing_stubs) == 0
        }


class WikiHealthChecker:
    """Herramienta de diagnÃ³stico e inspecciÃ³n de integridad de la Wiki."""

    def __init__(self, backend: BaseWikiBackend):
        self.backend = backend

    def run_diagnostics(self) -> WikiHealthReport:
        """Ejecuta un anÃ¡lisis exhaustivo de todas las pÃ¡ginas y enlaces."""
        report = WikiHealthReport()
        all_pages = self.backend.get_all_pages()
        report.total_pages = len(all_pages)

        existing_titles: Set[str] = {p.title.strip().lower() for p in all_pages}
        # AÃ±adir tambiÃ©n aliases
        for p in all_pages:
            for alias in p.metadata.aliases:
                existing_titles.add(alias.strip().lower())

        for page in all_pages:
            # 1. Contar categorÃ­as
            cat = page.metadata.category or "General"
            report.categories[cat] = report.categories.get(cat, 0) + 1

            # 2. Contar tags
            for t in page.metadata.tags:
                report.tag_distribution[t] = report.tag_distribution.get(t, 0) + 1

            # 3. Detectar pÃ¡ginas huÃ©rfanas (sin backlinks y que no sean un Ã­ndice principal)
            backlinks = self.backend.get_backlinks(page.title)
            if not backlinks and not page.title.lower().startswith("Ã­ndice") and not page.title.lower().startswith("index"):
                report.orphan_pages.append(page.title)

            # 4. Detectar enlaces rotos o pendientes (stubs)
            for link in page.outgoing_links:
                cleaned_link = link.strip().lower()
                if cleaned_link not in existing_titles:
                    report.missing_stubs.append({
                        "referenced_in": page.title,
                        "missing_concept": link
                    })

            # 5. Comprobar integridad bÃ¡sica del contenido
            if not page.content.strip():
                report.syntax_warnings.append(f"La pÃ¡gina '{page.title}' no tiene contenido.")

        return report