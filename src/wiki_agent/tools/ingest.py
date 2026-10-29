import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.tools.autolinker import AutoLinker


class DocumentIngestor:
    """Herramienta para procesar, segmentar y sintetizar documentos hacia la Wiki."""

    def __init__(self, manager: WikiKnowledgeManager):
        self.manager = manager

    def _get_autolinker(self) -> AutoLinker:
        concepts = self.manager.list_all_concepts()
        return AutoLinker(concepts)

    def ingest_text(
        self,
        title: str,
        text: str,
        category: str = "Documentos",
        tags: Optional[List[str]] = None,
        source_name: str = "Texto Directo",
        auto_link: bool = True
    ) -> Dict[str, Any]:
        """Integra un texto en la wiki, opcionalmente auto-enlazando conceptos existentes."""
        tags = tags or ["ingesta", "documento"]
        
        final_content = text
        if auto_link:
            linker = self._get_autolinker()
            final_content = linker.apply_links(text)

        page = self.manager.save_concept(
            title=title,
            content=final_content,
            category=category,
            tags=tags,
            source_documents=[source_name]
        )
        return {
            "status": "success",
            "title": page.title,
            "category": page.metadata.category,
            "links_detected": page.outgoing_links
        }

    def ingest_file(
        self,
        file_path: str,
        category: Optional[str] = None,
        auto_link: bool = True,
        split_sections: bool = False
    ) -> Dict[str, Any]:
        """Lee e integra un archivo de texto/cÃ³digo en la wiki."""
        p = Path(file_path)
        if not p.exists():
            return {"status": "error", "message": f"Archivo no encontrado: {file_path}"}

        text = p.read_text(encoding="utf-8", errors="ignore")
        cat = category or "Documentos"
        base_title = p.stem.replace("_", " ").title()

        if split_sections and "\n## " in text:
            # Segmentar por encabezados de segundo nivel ##
            sections = re.split(r"\n(?=## )", text)
            results = []
            for i, sec in enumerate(sections):
                lines = sec.strip().splitlines()
                first_line = lines[0]
                sec_title = first_line.replace("##", "").strip() if first_line.startswith("##") else f"{base_title} - Parte {i+1}"
                res = self.ingest_text(
                    title=f"{base_title} - {sec_title}",
                    text=sec,
                    category=cat,
                    tags=["segmento", "documento"],
                    source_name=f"{p.name}#{sec_title}",
                    auto_link=auto_link
                )
                results.append(res)
            return {"status": "success", "mode": "segmented", "sections_created": len(results), "items": results}

        return self.ingest_text(
            title=base_title,
            text=text,
            category=cat,
            source_name=p.name,
            auto_link=auto_link
        )