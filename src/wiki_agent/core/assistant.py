from typing import Dict, Any, List, Optional
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.models import WikiPage, SearchResult


class WikiAssistantEngine:
    """Motor de asistencia para el Agente IA: genera contextos enriquecidos y resuelve conceptos faltantes."""

    def __init__(self, manager: WikiKnowledgeManager):
        self.manager = manager

    def get_enriched_context(self, query: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Recupera el concepto más relevante junto con su red semántica (relaciones explícitas XML
        y backlinks), devolviendo un árbol de contexto estructurado ideal para inyectar en el
        prompt del LLM.

        max_depth controla la profundidad de navegación:
          - 1 (comportamiento original): solo primera línea de conceptos relacionados.
          - 2 (por defecto ahora): definición completa + secciones breves + títulos de 2.º nivel.
        """
        search_results = self.manager.search_knowledge(query, limit=3)
        if not search_results:
            return {
                "query": query,
                "found": False,
                "context_markdown": f"No se encontró información registrada sobre '{query}' en la Wiki.",
                "concepts": []
            }

        primary_title = search_results[0].title
        primary_page = self.manager.get_concept(primary_title)
        if not primary_page:
            return {"query": query, "found": False, "context_markdown": "", "concepts": []}

        # Construir contexto en Markdown enriquecido
        lines = [
            f"### Contexto de Memoria Wiki: {primary_page.title}",
            f"**Categoría:** {primary_page.metadata.category} | **Etiquetas:** {', '.join(primary_page.metadata.tags)}",
            "",
            "#### Definición / Contenido:",
            primary_page.content.strip(),
            ""
        ]

        # Secciones adicionales del concepto
        if primary_page.sections:
            for sec_name, sec_text in primary_page.sections.items():
                lines.append(f"#### {sec_name}:")
                lines.append(sec_text.strip())
                lines.append("")

        # Relaciones semánticas explícitas (XML)
        if primary_page.relations:
            lines.append("#### Relaciones Semánticas Explícitas:")
            # Agrupar por tipo de relación
            by_type: Dict[str, list] = {}
            for rel in primary_page.relations:
                by_type.setdefault(rel.relation_type, []).append(rel)
            type_labels = {
                "is_a": "Es un tipo de",
                "part_of": "Forma parte de",
                "relates_to": "Se relaciona con",
                "depends_on": "Depende de",
                "contradicts": "Contradice",
                "precedes": "Precede a",
            }
            for rel_type, rels in by_type.items():
                label = type_labels.get(rel_type, rel_type)
                for rel in rels[:5]:
                    sub_page = self.manager.get_concept(rel.target)
                    if sub_page and max_depth >= 2:
                        # Profundidad 2: incluir definición completa del concepto relacionado
                        sub_content = sub_page.content.strip()
                        sub_snippet = f"\n    > {sub_content[:300]}{'...' if len(sub_content) > 300 else ''}"
                        # Añadir secciones breves del concepto relacionado (máx. 2)
                        if sub_page.sections:
                            for sn, st in list(sub_page.sections.items())[:2]:
                                sub_snippet += f"\n    > **{sn}:** {st[:150]}{'...' if len(st) > 150 else ''}"
                        # Añadir sus propias relaciones como títulos (sin expandir más para evitar explosión)
                        if sub_page.relations:
                            sub_rel_titles = [f"[[{r.target}]]" for r in sub_page.relations[:4]]
                            sub_snippet += f"\n    > *Relacionado a su vez con: {', '.join(sub_rel_titles)}*"
                    elif sub_page:
                        # Profundidad 1 (comportamiento original): solo primera línea
                        sub_snippet = ": " + sub_page.content.strip().split("\n")[0][:100]
                    else:
                        sub_snippet = ""
                    desc_part = f" — {rel.description}" if rel.description else ""
                    lines.append(f"- **[{label}]** [[{rel.target}]]{desc_part}{sub_snippet}")
            lines.append("")
        elif primary_page.outgoing_links:
            # Fallback: enlaces heredados del Markdown migrado
            lines.append("#### Conceptos Relacionados (enlaces heredados):")
            for link in primary_page.outgoing_links[:5]:
                sub_page = self.manager.get_concept(link)
                if sub_page:
                    if max_depth >= 2:
                        sub_content = sub_page.content.strip()
                        snippet = f"\n    > {sub_content[:300]}{'...' if len(sub_content) > 300 else ''}"
                    else:
                        snippet = ": " + sub_page.content.strip().split("\n")[0][:120] + "..."
                    lines.append(f"- **[[{link}]]**:{snippet}")
                else:
                    lines.append(f"- **[[{link}]]**: _(Concepto pendiente de definir)_")
            lines.append("")

        # Backlinks (dónde se menciona este concepto)
        if primary_page.backlinks:
            lines.append(f"#### Mencionado en: {', '.join([f'[[{b}]]' for b in primary_page.backlinks])}")
            lines.append("")

        return {
            "query": query,
            "found": True,
            "primary_concept": primary_page.title,
            "category": primary_page.metadata.category,
            "context_markdown": "\n".join(lines),
            "outgoing_links": primary_page.outgoing_links,
            "backlinks": primary_page.backlinks,
            "relations": [{"type": r.relation_type, "target": r.target, "description": r.description} for r in primary_page.relations],
        }


    def get_concept_full_context(self, title: str) -> str:
        """Devuelve el contenido completo de un concepto para el comando /read.

        A diferencia de get_enriched_context (que parte de una búsqueda semántica),
        este método busca por título exacto (con fallback a búsqueda) y devuelve:
        - Definición completa sin truncar
        - Todas las secciones
        - Todas las relaciones con su primera línea de contenido
        - Backlinks
        """
        page = self.manager.get_concept(title)
        if not page:
            # Intentar búsqueda aproximada si no hay coincidencia exacta
            results = self.manager.search_knowledge(title, limit=1)
            if results:
                page = self.manager.get_concept(results[0].title)
        if not page:
            return f"No se encontró el concepto '[[{title}]]' en la Wiki."

        type_labels = {
            "is_a": "Es un tipo de", "part_of": "Forma parte de",
            "relates_to": "Se relaciona con", "depends_on": "Depende de",
            "contradicts": "Contradice", "precedes": "Precede a",
        }
        lines = [
            f"### [[{page.title}]] — Lectura Completa",
            f"**Categoría:** {page.metadata.category} | **Etiquetas:** {', '.join(page.metadata.tags)}",
            "",
            "#### Definición:",
            page.content.strip(),
            "",
        ]
        if page.sections:
            for sec_name, sec_text in page.sections.items():
                lines.append(f"#### {sec_name}:")
                lines.append(sec_text.strip())
                lines.append("")
        if page.relations:
            lines.append("#### Relaciones:")
            for rel in page.relations:
                label = type_labels.get(rel.relation_type, rel.relation_type)
                sub_page = self.manager.get_concept(rel.target)
                if sub_page:
                    sub_first = sub_page.content.strip().split("\n")[0][:120]
                    lines.append(f"- **[{label}]** [[{rel.target}]]: {sub_first}...")
                else:
                    lines.append(f"- **[{label}]** [[{rel.target}]]")
            lines.append("")
        if page.backlinks:
            lines.append(f"#### Mencionado en: {', '.join(f'[[{b}]]' for b in page.backlinks)}")
            lines.append("")
        return "\n".join(lines)

    def resolve_stub(self, title: str, summary: str, category: str = "General", tags: Optional[List[str]] = None) -> WikiPage:
        """Crea una ficha inicial para un concepto que estaba pendiente ('stub') resolviendo inconsistencias."""
        content = f"# {title}\n\n{summary.strip()}\n\n## Notas\n- Creado automÃ¡ticamente como resoluciÃ³n de concepto pendiente.\n"
        tags = tags or ["stub-resuelto"]
        return self.manager.save_concept(
            title=title,
            content=content,
            category=category,
            tags=tags
        )