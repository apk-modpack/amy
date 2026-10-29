from typing import List, Optional, Dict, Any
from mcp.server.fastmcp import FastMCP
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.core.assistant import WikiAssistantEngine
from wiki_agent.tools.ingest import DocumentIngestor
from wiki_agent.tools.collector import WebCollector
from wiki_agent.tools.dataset_exporter import DatasetExporter
from wiki_agent.tools.queue import GlobalIngestionQueueManager

mcp = FastMCP("wiki-memory-agent")
manager = WikiKnowledgeManager()
assistant = WikiAssistantEngine(manager)
ingestor = DocumentIngestor(manager)
collector = WebCollector(manager)
exporter = DatasetExporter(manager)
queue_mgr = GlobalIngestionQueueManager(manager)


@mcp.tool()
def wiki_get_context(query: str) -> Dict[str, Any]:
    """Obtiene el contexto enriquecido (definiciÃ³n + conceptos relacionados + backlinks) para la IA."""
    return assistant.get_enriched_context(query)


@mcp.tool()
def wiki_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Busca conceptos, notas y fragmentos en la base de conocimientos Wiki."""
    results = manager.search_knowledge(query, limit=limit)
    return [r.model_dump() for r in results]


@mcp.tool()
def wiki_read_concept(title: str) -> Dict[str, Any]:
    """Lee el contenido completo, metadatos, enlaces y backlinks de un concepto en la Wiki."""
    page = manager.get_concept(title)
    if not page:
        return {"error": f"Concepto '{title}' no encontrado en la Wiki."}
    return page.model_dump()


@mcp.tool()
def wiki_save_concept(
    title: str,
    content: str,
    category: str = "General",
    tags: Optional[List[str]] = None,
    aliases: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Crea o actualiza un concepto en la Wiki. Usa [[Concepto]] dentro del contenido para enlazar."""
    page = manager.save_concept(
        title=title,
        content=content,
        category=category,
        tags=tags or [],
        aliases=aliases or []
    )
    return {"status": "success", "title": page.title, "category": page.metadata.category}


@mcp.tool()
def wiki_resolve_stub(
    title: str,
    summary: str,
    category: str = "General",
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Crea la definiciÃ³n para un concepto pendiente de definir (stub) detectado por el sistema de salud."""
    page = assistant.resolve_stub(title=title, summary=summary, category=category, tags=tags)
    return {"status": "success", "title": page.title, "category": page.metadata.category}


@mcp.tool()
def wiki_append_note(title: str, note: str, section: str = "Notas y Actualizaciones") -> Dict[str, Any]:
    """AÃ±ade una nota o dato nuevo a un concepto existente sin sobreescribir el contenido previo."""
    page = manager.append_note(title=title, note=note, section=section)
    return {"status": "success", "title": page.title}


@mcp.tool()
def wiki_get_network(title: str) -> Dict[str, Any]:
    """Obtiene la red de enlaces salientes y entrantes (backlinks) de un concepto."""
    return manager.get_concept_network(title)


@mcp.tool()
def wiki_list_concepts(category: Optional[str] = None) -> List[str]:
    """Lista todos los conceptos registrados en la Wiki, opcionalmente por categorÃ­a."""
    return manager.list_all_concepts(category=category)


@mcp.tool()
def wiki_diagnose_health() -> Dict[str, Any]:
    """Ejecuta un chequeo de integridad: detecta enlaces pendientes, pÃ¡ginas huÃ©rfanas y sintaxis."""
    return manager.check_health()


@mcp.tool()
def wiki_rebuild_indexes() -> List[str]:
    """Reconstruye automÃ¡ticamente los Mapas de Contenido (MOCs) e Ãndice Maestro."""
    return manager.rebuild_indexes()


# --- Herramientas de Cola ÃšNICA GLOBAL de Ingesta ---
@mcp.tool()
def wiki_queue_add_item(source: str, title: str, category: str = "General", priority: int = 10) -> Dict[str, Any]:
    """AÃ±ade un elemento a la cola Ãºnica global de ingesta."""
    item = queue_mgr.add_item(title=title, source=source, category=category, priority=priority)
    return item.to_dict()


@mcp.tool()
def wiki_queue_get_status() -> Dict[str, Any]:
    """Consulta el estado de la cola global de ingesta (total, pendientes, completados)."""
    return queue_mgr.get_status()


@mcp.tool()
def wiki_queue_process_next(fact_check: bool = False) -> Dict[str, Any]:
    """Procesa estrictamente el siguiente concepto pendiente de la cola global única, con verificación opcional."""
    return queue_mgr.process_next(fact_check=fact_check)


@mcp.tool()
def wiki_queue_process_batch(count: Optional[int] = 5, delay_seconds: float = 1.0, fact_check: bool = False) -> Dict[str, Any]:
    """Procesa una tanda de elementos de la cola global con pausas y verificación opcional."""
    return queue_mgr.process_queue(count=count, delay_seconds=delay_seconds, fact_check=fact_check)


@mcp.tool()
def wiki_export_training_dataset(format_type: str = "sharegpt", output_path: Optional[str] = None) -> Dict[str, Any]:
    """Exporta el conocimiento de la Wiki a un dataset JSONL (sharegpt, alpaca, chatml) para fine-tuning."""
    out_file = exporter.export_to_jsonl(format_type=format_type, output_path=output_path)
    return {"status": "success", "output_file": out_file, "format": format_type}


@mcp.tool()
def wiki_generate_ollama_modelfile(base_model: str = "llama3.2", output_file: Optional[str] = None) -> Dict[str, Any]:
    """Genera un Modelfile de Ollama con la memoria de la Wiki inyectada en su System Prompt."""
    out_file = exporter.generate_ollama_modelfile(base_model=base_model, output_file=output_file)
    return {"status": "success", "modelfile": out_file, "base_model": base_model}


def run_server():
    mcp.run()


if __name__ == "__main__":
    run_server()