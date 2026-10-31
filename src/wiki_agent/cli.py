import json
import httpx
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.tools.ingest import DocumentIngestor
from wiki_agent.tools.collector import WebCollector
from wiki_agent.tools.dataset_exporter import DatasetExporter
from wiki_agent.tools.queue import IngestionQueueManager
from wiki_agent.logging_config import setup_logging
from wiki_agent.ui.renderer import ConsoleRenderer
from wiki_agent.ui.chat_session import InteractiveChatSession
import logging

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

setup_logging()
logger = logging.getLogger(__name__)

console = Console()


def get_process_memory_mb() -> float:
    """Obtiene el uso de memoria RAM (WorkingSetSize / RSS) del proceso actual en MB."""
    try:
        import ctypes
        from ctypes import wintypes

        class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            _fields_ = [
                ('cb', wintypes.DWORD),
                ('PageFaultCount', wintypes.DWORD),
                ('PeakWorkingSetSize', ctypes.c_size_t),
                ('WorkingSetSize', ctypes.c_size_t),
                ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                ('QuotaPagedPoolUsage', ctypes.c_size_t),
                ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                ('PagefileUsage', ctypes.c_size_t),
                ('PeakPagefileUsage', ctypes.c_size_t),
                ('PrivateUsage', ctypes.c_size_t),
            ]

        GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
        GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX), wintypes.DWORD]
        GetProcessMemoryInfo.restype = wintypes.BOOL

        handle = ctypes.windll.kernel32.GetCurrentProcess()
        counters = PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)

        if GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return counters.WorkingSetSize / (1024 * 1024)
    except Exception:
        pass
    return 0.0


def render_chat_header(llm, no_memory: bool, stats: Optional[Dict[str, Any]] = None) -> Panel:
    """Genera la cabecera principal mostrando únicamente el cuadro azul izquierdo."""
    provider = getattr(llm, 'provider', 'local')
    backend_desc = "llama-cpp-python (local, sin Ollama)" if provider == "llamacpp" else getattr(llm, 'base_url', 'Ollama')

    left_info = (
        f"[bold cyan]Modelo:[/bold cyan] {llm.model_name}\n"
        f"[bold cyan]Backend:[/bold cyan] {backend_desc}\n"
        f"[bold cyan]Memoria Wiki:[/bold cyan] {'[red]DESACTIVADA[/red]' if no_memory else '[green]ACTIVA[/green]'}\n"
        f"[bold cyan]Ruta:[/bold cyan] [dim]{Path.cwd()}[/dim]\n\n"
        "[dim]Comandos: /save <título> · /edit <título> · /read <título> · /stats · /clear · /exit[/dim]"
    )
    return Panel(
        left_info,
        title="🤖 Wiki-Memory Agent — Chat Autónomo",
        border_style="cyan"
    )


@click.group()
def main():
    """Wiki-Memory Agent CLI - GestiÃ³n de Memoria Conceptual y Base de Conocimientos."""
    pass


@main.command()
@click.argument("title")
def read(title: str):
    """Lee un concepto de la Wiki."""
    mgr = WikiKnowledgeManager()
    page = mgr.get_concept(title)
    if not page:
        console.print(f"[bold red]Concepto '{title}' no encontrado.[/bold red]")
        return

    meta = page.metadata
    console.print(Panel(
        f"[bold cyan]CategorÃ­a:[/bold cyan] {meta.category}\n"
        f"[bold cyan]Tags:[/bold cyan] {', '.join(meta.tags)}\n"
        f"[bold cyan]Enlaces Salientes:[/bold cyan] {', '.join(page.outgoing_links)}\n"
        f"[bold cyan]Backlinks (referenciado en):[/bold cyan] {', '.join(page.backlinks)}\n\n"
        f"{page.content}",
        title=f"ðŸ“– {page.title}",
        border_style="green"
    ))


@main.command()
@click.argument("title")
@click.argument("content")
@click.option("--category", "-c", default="General", help="CategorÃ­a del concepto.")
@click.option("--tags", "-t", default="", help="Tags separados por coma.")
def save(title: str, content: str, category: str, tags: str):
    """Crea o actualiza un concepto en la Wiki."""
    mgr = WikiKnowledgeManager()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    page = mgr.save_concept(title=title, content=content, category=category, tags=tag_list)
    console.print(f"[bold green]âœ“ Concepto '{page.title}' guardado correctamente en '{category}'.[/bold green]")


@main.command()
@click.argument("title")
@click.argument("content")
@click.option("--category", "-c", default="General", help="Categoría del concepto.")
@click.option("--tags", "-t", default="", help="Tags separados por coma.")
def edit(title: str, content: str, category: str, tags: str):
    """Sobreescribe un concepto existente en la Wiki."""
    mgr = WikiKnowledgeManager()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    page = mgr.save_concept(title=title, content=content, category=category, tags=tag_list)
    console.print(f"[bold green]✓ Concepto '{page.title}' editado correctamente.[/bold green]")


@main.command()
@click.argument("title")
def delete(title: str):
    """Elimina un concepto de la Wiki."""
    mgr = WikiKnowledgeManager()
    success = mgr.delete_concept(title)
    if success:
        console.print(f"[bold green]✓ Concepto '{title}' eliminado correctamente.[/bold green]")
    else:
        console.print(f"[bold red]✗ No se pudo eliminar el concepto '{title}' (puede que no exista).[/bold red]")


@main.command()
@click.argument("file_path")
@click.option("--category", "-c", default="Documentos", help="CategorÃ­a asignada.")
@click.option("--split", is_flag=True, help="Segmentar documento por secciones ##.")
def ingest(file_path: str, category: str, split: bool):
    """Ingesta un archivo local (txt, md) en la Wiki con auto-enlazado."""
    mgr = WikiKnowledgeManager()
    ingestor = DocumentIngestor(mgr)
    result = ingestor.ingest_file(file_path, category=category, split_sections=split)
    if result.get("status") == "success":
        console.print(f"[bold green]âœ“ Ingesta completada con Ã©xito:[/bold green] {result}")
    else:
        console.print(f"[bold red]Error en la ingesta:[/bold red] {result.get('message')}")


@main.command()
@click.argument("url")
@click.option("--title", "-t", default=None, help="TÃ­tulo personalizado.")
@click.option("--category", "-c", default="Web", help="CategorÃ­a asignada.")
def collect_url(url: str, title: str, category: str):
    """Descarga e ingesta contenido de una URL en la Wiki."""
    mgr = WikiKnowledgeManager()
    collector = WebCollector(mgr)
    console.print(f"[cyan]Recopilando URL:[/cyan] {url}...")
    result = collector.fetch_url(url, custom_title=title, category=category)
    if result.get("status") == "success":
        console.print(f"[bold green]âœ“ URL integrada con Ã©xito:[/bold green] {result['title']}")
    else:
        console.print(f"[bold red]Error al recopilar URL:[/bold red] {result.get('message')}")


# --- Subcomandos de GestiÃ³n de Cola de Ingesta (Queue) ---
@main.group()
def queue():
    """GestiÃ³n de la cola fÃ­sica persistente de ingesta por lotes."""
    pass


@queue.command(name="add")
@click.argument("source")
@click.option("--title", "-t", default="Concepto Web", help="TÃ­tulo del concepto.")
@click.option("--category", "-c", default="General", help="CategorÃ­a asignada.")
@click.option("--type", "-k", "source_type", default="url", type=click.Choice(["url", "file", "text"]))
def queue_add(source: str, title: str, category: str, source_type: str):
    """AÃ±ade un elemento a la lista fÃ­sica de ingesta."""
    mgr = WikiKnowledgeManager()
    q_mgr = IngestionQueueManager(mgr)
    item = q_mgr.add_item(title=title, source=source, source_type=source_type, category=category)
    console.print(f"[bold green]âœ“ AÃ±adido a la cola:[/bold green] '{item.title}' ({item.source})")


@queue.command(name="status")
def queue_status():
    """Muestra el estado de la cola de ingesta persistente."""
    mgr = WikiKnowledgeManager()
    q_mgr = IngestionQueueManager(mgr)
    status = q_mgr.get_status()
    console.print(Panel(
        f"[bold cyan]Total en cola:[/bold cyan] {status['total']}\n"
        f"[bold yellow]Pendientes:[/bold yellow] {status['pending']}\n"
        f"[bold green]Completados:[/bold green] {status['completed']}\n"
        f"[bold red]Fallidos:[/bold red] {status['failed']}\n"
        f"[bold white]Archivo:[/bold white] {status['queue_file']}",
        title="ðŸ“‹ Estado de la Cola de Ingesta",
        border_style="cyan"
    ))


@queue.command(name="list")
@click.option("--status", "-s", default=None, help="Filtrar por estado (pending, completed, failed).")
def queue_list(status: str):
    """Lista todos los elementos de la cola fÃ­sica."""
    mgr = WikiKnowledgeManager()
    q_mgr = IngestionQueueManager(mgr)
    items = q_mgr.list_items(status_filter=status)
    if not items:
        console.print("[yellow]La cola estÃ¡ vacÃ­a o no hay elementos con ese filtro.[/yellow]")
        return

    table = Table(title="Elementos en Cola de Ingesta")
    table.add_column("ID", style="dim")
    table.add_column("TÃ­tulo", style="cyan")
    table.add_column("Fuente", style="white")
    table.add_column("CategorÃ­a", style="magenta")
    table.add_column("Estado", style="green")

    for it in items:
        st_color = "yellow" if it["status"] == "pending" else ("green" if it["status"] == "completed" else "red")
        table.add_row(it["item_id"], it["title"], it["source"][:40], it["category"], f"[{st_color}]{it['status']}[/{st_color}]")

    console.print(table)


@queue.command(name="run")
@click.option("--count", "-n", default=None, type=int, help="Número de elementos a procesar.")
@click.option("--all", "until_empty", is_flag=True, help="Procesar hasta vaciar la cola.")
@click.option("--delay", "-d", default=1.0, type=float, help="Pausa en segundos entre peticiones.")
@click.option("--fact-check/--no-fact-check", "fact_check", default=None, help="Activar o desactivar verificación externa (fact-check).")
def queue_run(count: int, until_empty: bool, delay: float, fact_check: Optional[bool]):
    """Procesa de forma gradual la cola física de ingesta con verificación opcional."""
    mgr = WikiKnowledgeManager()
    q_mgr = IngestionQueueManager(mgr)

    # Pregunta interactiva si no se especificó flag en la terminal
    if fact_check is None:
        fact_check = click.confirm(
            "¿Desea activar la verificación de datos (fact-check externo con fuentes en internet) antes de procesar la cola?",
            default=False
        )

    fc_status = "[bold green]ACTIVADO[/bold green]" if fact_check else "[yellow]DESACTIVADO[/yellow]"
    console.print(f"[cyan]Iniciando procesamiento de cola (Pausa: {delay}s | Fact-Check: {fc_status})...[/cyan]")
    res = q_mgr.process_queue(count=count, until_empty=until_empty, delay_seconds=delay, fact_check=fact_check)
    console.print(f"[bold green]✓ Procesados:[/bold green] {res['processed']} | [bold yellow]Restantes:[/bold yellow] {res['remaining']}")
    if res.get("errors"):
        console.print(f"[bold red]Errores encontrados:[/bold red] {len(res['errors'])}")


@queue.command(name="clear")
def queue_clear():
    """Limpia la cola de ingesta."""
    mgr = WikiKnowledgeManager()
    q_mgr = IngestionQueueManager(mgr)
    q_mgr.clear()
    console.print("[bold yellow]✓ Cola de ingesta vaciada.[/bold yellow]")


@queue.command(name="enqueue-catalog")
@click.option("--count", "-n", default=5, type=int, help="Número de especies del catálogo a encolar.")
@click.option("--volume", "-v", default=None, type=int, help="Filtrar por volumen de la OMS (1, 2, 3 o 4).")
@click.option("--all", "all_plants", is_flag=True, help="Encolar todas las especies del catálogo.")
def queue_enqueue_catalog(count: int, volume: Optional[int], all_plants: bool):
    """Carga y encola especies medicinales desde el catálogo estructurado de la OMS."""
    catalog_path = Path("./data/catalogs/medicinal_plants_who_catalog.json")
    if not catalog_path.exists():
        console.print("[red]Catálogo no encontrado en data/catalogs/medicinal_plants_who_catalog.json[/red]")
        return

    with open(catalog_path, "r", encoding="utf-8") as f:
        plants = json.load(f)

    if volume:
        plants = [p for p in plants if p.get("who_volume") == volume]

    mgr = WikiKnowledgeManager()
    q_mgr = IngestionQueueManager(mgr)

    selected = plants if all_plants else plants[:count]
    enqueued = 0

    for p in selected:
        q_mgr.add_item(
            title=p["scientific_name"],
            source=p.get("source_url", f"https://es.wikipedia.org/wiki/{p['scientific_name'].replace(' ', '_')}"),
            category="Botánica",
            source_type="url",
            priority=p.get("who_volume", 1)
        )
        enqueued += 1

    console.print(f"[bold green]✓ Se han añadido {enqueued} especies medicinales de la OMS a la cola de ingesta.[/bold green]")


@main.command()
@click.argument("query")
def search(query: str):
    """Busca conceptos en la Wiki."""
    mgr = WikiKnowledgeManager()
    results = mgr.search_knowledge(query)
    if not results:
        console.print(f"[yellow]No se encontraron resultados para '{query}'.[/yellow]")
        return

    table = Table(title=f"Resultados para '{query}'")
    table.add_column("TÃ­tulo", style="cyan", no_wrap=True)
    table.add_column("CategorÃ­a", style="magenta")
    table.add_column("Snippet", style="white")
    table.add_column("Score", style="green")

    for r in results:
        table.add_row(r.title, r.category, r.snippet, f"{r.score:.1f}")

    console.print(table)


@main.command()
@click.option("--category", "-c", default=None, help="Filtrar por categorÃ­a.")
def list_concepts(category: str):
    """Lista todos los conceptos de la Wiki."""
    mgr = WikiKnowledgeManager()
    concepts = mgr.list_all_concepts(category=category)
    console.print(f"[bold cyan]Total de conceptos:[/bold cyan] {len(concepts)}")
    for c in concepts:
        console.print(f" â€¢ [green]{c}[/green]")


@main.command()
def doctor():
    """Ejecuta el diagnÃ³stico de salud e integridad de la Wiki (Linter/Health Check)."""
    mgr = WikiKnowledgeManager()
    rep = mgr.check_health()

    console.print(Panel(
        f"[bold cyan]Total de pÃ¡ginas:[/bold cyan] {rep['total_pages']}\n"
        f"[bold cyan]PÃ¡ginas huÃ©rfanas (sin backlinks):[/bold cyan] {len(rep['orphan_pages'])}\n"
        f"[bold cyan]Enlaces pendientes / rotos (stubs):[/bold cyan] {len(rep['missing_stubs'])}\n"
        f"[bold cyan]Advertencias de sintaxis:[/bold cyan] {len(rep['syntax_warnings'])}",
        title="ðŸ©º DiagnÃ³stico de Salud de la Wiki",
        border_style="cyan"
    ))

    if rep["missing_stubs"]:
        table = Table(title="Enlaces Pendientes (Stubs a crear)")
        table.add_column("Referenciado en", style="yellow")
        table.add_column("Concepto Faltante", style="red")
        for stub in rep["missing_stubs"]:
            table.add_row(stub["referenced_in"], stub["missing_concept"])
        console.print(table)


@main.command()
def index():
    """Reconstruye los Ã­ndices MOC (Map of Content) y el Ãndice Maestro."""
    mgr = WikiKnowledgeManager()
    created = mgr.rebuild_indexes()
    console.print(f"[bold green]âœ“ Ãndices reconstruidos exitosamente:[/bold green] {', '.join(created)}")


@main.command()
@click.option("--format", "-f", "format_type", default="sharegpt", type=click.Choice(["sharegpt", "alpaca", "chatml", "openai"]))
@click.option("--output", "-o", default=None, help="Ruta del archivo de salida.")
def export(format_type: str, output: str):
    """Exporta el conocimiento a un dataset JSONL para fine-tuning."""
    mgr = WikiKnowledgeManager()
    exporter = DatasetExporter(mgr)
    out_file = exporter.export_to_jsonl(output_path=output, format_type=format_type)
    console.print(f"[bold green]âœ“ Dataset ({format_type}) exportado exitosamente en:[/bold green] {out_file}")


@main.command()
@click.option("--model", "-m", default="llama3.2", help="Modelo base de Ollama.")
@click.option("--output", "-o", default=None, help="Ruta de salida del Modelfile.")
def modelfile(model: str, output: str):
    """Genera un Modelfile de Ollama con la memoria de la Wiki inyectada."""
    mgr = WikiKnowledgeManager()
    exporter = DatasetExporter(mgr)
    out_file = exporter.generate_ollama_modelfile(base_model=model, output_file=output)
    console.print(f"[bold green]âœ“ Modelfile de Ollama generado en:[/bold green] {out_file}")


@main.command()
def mcp():
    """Inicia el servidor MCP para Antigravity u otros clientes."""
    from wiki_agent.mcp_server import run_server
    console.print("[bold green]Iniciando servidor MCP de Wiki-Memory Agent...[/bold green]")
    run_server()


@main.command()
@click.option("--model", "-m", default=None, help="Modelo a usar (sobreescribe config.yaml).")
@click.option("--no-memory", "no_memory", is_flag=True, help="Desactiva la inyección de contexto Wiki.")
@click.option("--url", default=None, help="URL de la API (solo aplica al provider 'ollama').")
@click.option(
    "--connect", "-c", "chat_room_host", default=None,
    help="IP o hostname de la Sala de Chat a la que conectarse (activa modo red)."
)
@click.option(
    "--port", "-p", "chat_room_port", default=8765, show_default=True,
    help="Puerto de la Sala de Chat (solo con --connect)."
)
def chat(model: Optional[str], no_memory: bool, url: Optional[str],
         chat_room_host: Optional[str], chat_room_port: int):
    """Inicia una sesión de chat interactiva usando la Wiki como memoria.

    \b
    Modos de operación:
      Sin --connect: entrada por teclado (modo local original).
      Con --connect <IP>: recibe inputs desde la Sala de Chat remota (modo red).

    \b
    Ejemplos:
      wiki-agent chat
      wiki-agent chat --connect 192.168.1.10
      wiki-agent chat --connect 192.168.1.10 --port 9000

    \b
    Comandos especiales durante el chat:
      /save <título>    Guarda la última respuesta como concepto en la Wiki
      /clear            Limpia el historial de la sesión actual
      /stats            Muestra métricas de la sesión
      /exit o /quit     Termina el chat
      /help             Muestra esta ayuda
    """
    from wiki_agent.llm import get_llm_backend, OllamaBackend
    from wiki_agent.agent import WikiAgent

    mgr = WikiKnowledgeManager()
    cfg = mgr.config

    # Construir backend con posibles overrides de CLI
    llm_cfg = cfg.get("llm", {})
    if model:
        llm_cfg["model"] = model
    if url:
        llm_cfg["base_url"] = url

    llm = get_llm_backend({"llm": llm_cfg})

    # Si no se proporcionó host, preguntar interactivamente si el usuario quiere conectarse
    network_client = None
    if chat_room_host is None:
        console.print()
        console.print(Panel(
            "[bold cyan]Modo de entrada[/bold cyan]\n\n"
            "Puedes operar en modo local (entrada por teclado) o conectarte\n"
            "a una [bold]Sala de Chat[/bold] que actúe como interfaz gráfica.\n\n"
            "[dim]Deja vacío para modo local. Escribe una IP para modo red.[/dim]",
            title="🌐 Wiki-Memory Agent — Configuración de Entrada",
            border_style="cyan"
        ))
        raw = input("  IP de la Sala de Chat [Enter = modo local]: ").strip()
        if raw:
            chat_room_host = raw

    # Si hay host (manual o por flag), activar modo red
    if chat_room_host:
        from wiki_agent.network.client import AgentNetworkClient
        from wiki_agent.agent.identity import AgentIdentityManager
        ident = AgentIdentityManager()
        console.print(f"\n[dim]Conectando con la Sala de Chat en [cyan]{chat_room_host}:{chat_room_port}[/cyan] como [bold]{ident.agent_name}[/bold]...[/dim]")
        network_client = AgentNetworkClient(
            host=chat_room_host,
            port=chat_room_port,
            model_name=llm.model_name,
            client_name=ident.agent_name,
            client_id=ident.agent_id,
        )
        try:
            network_client.connect()
            console.print(f"[bold green]✓ Conectado a la Sala de Chat ({chat_room_host}:{chat_room_port})[/bold green]")
        except Exception as e:
            console.print(Panel(
                f"[bold red]No se pudo conectar con la Sala de Chat.[/bold red]\n\n"
                f"IP: [cyan]{chat_room_host}[/cyan] · Puerto: [cyan]{chat_room_port}[/cyan]\n\n"
                f"Error: {e}\n\n"
                f"[dim]¿Está la Sala de Chat iniciada? Abre primero [yellow]iniciar_sala_de_chat.bat[/yellow].[/dim]",
                title="❌ Error de Conexión",
                border_style="red"
            ))
            return

    logger.info(
        "SESIÓN CHAT INICIADA | Modelo: %s | URL: %s | no_memory: %s | stream: %s | "
        "context_concepts: %s | modo: %s",
        llm.model_name,
        getattr(llm, 'base_url', 'N/A'),
        no_memory,
        llm_cfg.get('stream', True),
        0 if no_memory else llm_cfg.get('context_concepts', 3),
        "NETWORK" if network_client else "LOCAL"
    )

    # --- Banner de inicio y verificación de backend ---
    renderer = ConsoleRenderer(console)
    console.print()
    console.print(renderer.render_header(llm, no_memory))

    provider = llm_cfg.get('provider', 'ollama')
    check_msg = "Verificando modelo local GGUF..." if provider == 'llamacpp' else "Verificando conexión con Ollama..."
    console.print(f"[dim]{check_msg}[/dim]", end=" ")
    if not llm.is_available():
        logger.error("SESIÓN CHAT | Backend LLM no disponible. Provider: %s | Modelo: %s", provider, llm.model_name)
        console.print()
        if provider == 'llamacpp':
            model_path = llm_cfg.get('model_path', './models/aaa.gguf')
            console.print(Panel(
                f"[bold red]No se encontró el fichero GGUF o llama-cpp-python no está instalado.[/bold red]\n\n"
                f"Fichero esperado: [cyan]{model_path}[/cyan]\n\n"
                f"Instala la dependencia con:\n"
                f"  [yellow]pip install -e .[local][/yellow]",
                title="❌ Error — Backend LlamaCpp",
                border_style="red"
            ))
        else:
            console.print(Panel(
                f"[bold red]No se pudo conectar con Ollama.[/bold red]\n\n"
                f"Asegúrate de que Ollama está corriendo:\n"
                f"  [yellow]ollama serve[/yellow]\n\n"
                f"Y de que el modelo está descargado:\n"
                f"  [yellow]ollama pull {llm.model_name}[/yellow]\n\n"
                f"URL configurada: [cyan]{getattr(llm, 'base_url', 'N/A')}[/cyan]",
                title="❌ Error de conexión Ollama",
                border_style="red"
            ))
        if network_client:
            network_client.disconnect()
        return

    logger.info("SESIÓN CHAT | Backend LLM verificado correctamente. Provider: %s", provider)
    console.print("[bold green]✓ Listo[/bold green]")

    # --- Inicializar agente y sesión interactiva POO ---
    stream = llm_cfg.get("stream", True)
    context_concepts = 0 if no_memory else llm_cfg.get("context_concepts", 3)
    agent = WikiAgent(
        manager=mgr,
        llm=llm,
        context_concepts=context_concepts,
        stream=stream,
    )

    session = InteractiveChatSession(
        agent=agent,
        manager=mgr,
        renderer=renderer,
        console=console,
        no_memory=no_memory,
        network_client=network_client,
    )

    try:
        session.start()
    finally:
        if network_client and network_client.is_connected:
            network_client.disconnect()
        if hasattr(llm, "shutdown"):
            llm.shutdown()


@main.command(name="chat-room")
@click.option(
    "--port", "-p", default=8765, show_default=True,
    help="Puerto TCP en el que escucha la Sala de Chat."
)
def chat_room_cmd(port: int):
    """Inicia la Sala de Chat (interfaz gráfica con ventana).

    \b
    La Sala de Chat es el programa servidor que muestra la interfaz gráfica
    donde el usuario escribe mensajes y recibe respuestas del Agente IA.

    \b
    Flujo de uso:
      1. Ejecuta este comando primero: wiki-agent chat-room
      2. En otra terminal, inicia el agente: wiki-agent chat --connect <IP>
    """
    try:
        from wiki_agent.chat_room import run_chat_room
        console.print(f"[bold cyan]Iniciando Sala de Chat en puerto {port}...[/bold cyan]")
        run_chat_room(port=port)
    except ImportError as e:
        console.print(Panel(
            f"[bold red]Error al importar la Sala de Chat.[/bold red]\n\n"
            f"Asegúrate de tener tkinter disponible (viene con Python estándar).\n\n"
            f"Detalle: {e}",
            title="❌ Error",
            border_style="red"
        ))


if __name__ == "__main__":
    main()