"""Sesión de chat interactiva (REPL) orientada a objetos.

Maneja el bucle de conversación con el usuario, la captura de comandos especiales
de terminal (/stats, /tree, /save, /edit, /read, /delete, /clear, /exit, /help) y
la coordinación con WikiAgent, ConsoleRenderer y TokenStreamProcessor.
"""

from typing import Optional, Dict, Any
import time
import httpx
import logging
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from wiki_agent.agent.loop import WikiAgent
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.ui.renderer import ConsoleRenderer
from wiki_agent.ui.stream_processor import TokenStreamProcessor
from wiki_agent.domain import CognitiveAgent, AgentTurnResult

logger = logging.getLogger(__name__)


class InteractiveChatSession:
    """Sesión interactiva en terminal con ciclo conversacional y métricas."""

    def __init__(
        self,
        agent: WikiAgent,
        manager: WikiKnowledgeManager,
        renderer: Optional[ConsoleRenderer] = None,
        console: Optional[Console] = None,
        no_memory: bool = False,
    ):
        self.agent = agent
        self.manager = manager
        self.console = console or Console()
        self.renderer = renderer or ConsoleRenderer(self.console)
        self.no_memory = no_memory

        self.stats: Dict[str, Any] = {
            "tok_s": 0.0,
            "latency": 0.0,
            "ram_mb": 0.0,
            "wiki_count": len(self.manager.list_all_concepts()),
            "start_time": time.time(),
        }
        self.turn_number = 0

    def start(self):
        """Inicia y mantiene el bucle interactivo hasta /exit o EOF."""
        self.console.clear()
        self.console.print(self.renderer.render_header(self.agent.llm, self.no_memory))
        self.console.print()

        logger.info(
            "SESIÓN CHAT | INICIADA. Modelo: %s | Memoria: %s",
            self.agent.llm.model_name,
            "DESACTIVADA" if self.no_memory else "ACTIVA"
        )

        while True:
            try:
                user_input = Prompt.ask("\n[bold green]Tú[/bold green]").strip()
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[dim]Saliendo...[/dim]")
                break

            if not user_input:
                continue

            # Despacho de comandos interactivos de la sesión
            if self._handle_session_command(user_input):
                continue

            # Turno de conversación con el agente
            self._execute_turn(user_input)

    def _handle_session_command(self, cmd: str) -> bool:
        """Procesa comandos especiales del shell interactivo. Retorna True si fue un comando consumido."""
        cmd_lower = cmd.lower()

        if cmd_lower in ("/exit", "/quit", "exit", "quit"):
            self.console.print("[dim]¡Hasta luego![/dim]")
            logger.info("SESIÓN CHAT | Finalizada por el usuario.")
            raise SystemExit(0)

        if cmd_lower in ("/clear", "clear"):
            self.agent.clear_history()
            self.console.clear()
            self.console.print(self.renderer.render_header(self.agent.llm, self.no_memory))
            self.console.print("[dim]Historial de conversación reiniciado.[/dim]")
            return True

        if cmd_lower == "/stats":
            self._show_stats()
            return True

        if cmd_lower == "/tree":
            self._show_wiki_tree_overview()
            return True

        if cmd_lower.startswith("/read "):
            title = cmd[6:].strip()
            self._read_concept(title)
            return True

        if cmd_lower in ("/help", "help"):
            self.renderer.render_help()
            return True

        if cmd_lower.startswith("/save "):
            title = cmd[6:].strip()
            if not title:
                self.console.print("[red]Uso: /save <título del concepto>[/red]")
            else:
                result = self.agent.save_last_response(title)
                self.console.print(f"[bold green]{result}[/bold green]")
            return True

        if cmd_lower.startswith("/edit "):
            title = cmd[6:].strip()
            if not title:
                self.console.print("[red]Uso: /edit <título del concepto>[/red]")
            else:
                result = self.agent.save_last_response(title)
                self.console.print(f"[bold green]{result} (Editado)[/bold green]")
            return True

        if cmd_lower.startswith("/delete "):
            title = cmd[8:].strip()
            if not title:
                self.console.print("[red]Uso: /delete <título del concepto>[/red]")
            else:
                result = self.agent.delete_concept(title)
                self.console.print(f"[bold green]{result}[/bold green]")
            return True

        return False

    def _execute_turn(self, user_input: str):
        """Ejecuta un turno completo de interacción entre el usuario y el agente."""
        self.turn_number += 1
        logger.info("SESIÓN CHAT | === TURNO %d — ENTRADA USUARIO ===", self.turn_number)
        logger.info("SESIÓN CHAT | TURNO %d | INPUT USUARIO: %r", self.turn_number, user_input)

        stream_processor = TokenStreamProcessor()
        agent_header_printed = {"done": False}

        def _print_agent_header():
            if not agent_header_printed["done"]:
                self.console.print("\n[bold magenta]Agente:[/bold magenta] ", end="")
                agent_header_printed["done"] = True

        def print_status(msg):
            if isinstance(msg, tuple):
                kind = msg[0]
                if kind == "wiki_tree":
                    concepts = msg[1]
                    logger.debug("SESIÓN CHAT | STATUS CALLBACK | wiki_tree | concepts=%s", concepts)
                    self.renderer.render_wiki_tree(concepts, self.manager)
                elif kind == "thought":
                    logger.debug("SESIÓN CHAT | STATUS CALLBACK | thought procesado en streaming.")
                elif kind == "cycle_start":
                    cycle_num = msg[1]
                    model_name = msg[2] if len(msg) > 2 else "?"
                    logger.debug("SESIÓN CHAT | STATUS CALLBACK | cycle_start | ciclo=%d", cycle_num)
                    stream_processor.reset_cycle()
                    print(f"\r{' ' * 80}\r", end="", flush=True)
                    self.console.print(f"[dim]🧠 Procesando modelo ({model_name}) - Ciclo {cycle_num}...[/dim]")
                return

            logger.debug("SESIÓN CHAT | STATUS CALLBACK | msg=%r", str(msg))
            print(f"\r{' ' * 80}\r", end="", flush=True)
            self.console.print(f"[dim]{msg}[/dim]")

        def on_bytes(total: int):
            if stream_processor.stream_active or stream_processor.has_started or stream_processor.in_thought:
                return
            if not agent_header_printed["done"]:
                return
            print(f"\r  ⏳ {total:.1f} bytes recibidos...                \r", end="", flush=True)

        try:
            start_time = time.perf_counter()
            result: AgentTurnResult = self.agent.chat(
                user_input,
                stream_callback=stream_processor,
                status_callback=print_status,
                bytes_callback=on_bytes,
            )
            elapsed = max(0.001, time.perf_counter() - start_time)
            tokens = getattr(stream_processor, "token_count", 0)
            tok_per_sec = (tokens / elapsed) if tokens > 0 else 0.0
            ram_now = self.renderer.get_process_memory_mb()
            wiki_total = len(self.manager.list_all_concepts())

            self.stats.update({
                "tok_s": tok_per_sec,
                "latency": elapsed,
                "ram_mb": ram_now,
                "wiki_count": wiki_total,
            })

            # Imprimir respuesta final limpia del resultado de dominio
            print(f"\r{' ' * 80}\r", end="", flush=True)
            _print_agent_header()
            print(result.response_text)

            if result.concepts_consulted:
                labels = "  ".join(f"[[{c}]]" for c in result.concepts_consulted)
                self.console.print(f"[dim]🔍 Contexto wiki: {labels}[/dim]")

            if result.executed_commands:
                logger.info("SESIÓN CHAT | TURNO %d | Comandos ejecutados: %s", self.turn_number, result.executed_commands)
                self.console.print(f"[dim]⚙️  Comandos ejecutados internamente: {', '.join(result.executed_commands)}[/dim]")

            self.renderer.render_turn_metrics(tok_per_sec, elapsed, ram_now, wiki_total)
            logger.info("SESIÓN CHAT | === TURNO %d — FIN ===", self.turn_number)
            self.console.print()

        except httpx.ConnectError as e:
            logger.error("SESIÓN CHAT | TURNO %d | ConnectError: %s", self.turn_number, e, exc_info=True)
            self.console.print("\n[bold red]Error: El servidor LLM dejó de responder. ¿Sigue corriendo?[/bold red]")
        except httpx.HTTPStatusError as e:
            logger.error("SESIÓN CHAT | TURNO %d | HTTPStatusError %d: %s", self.turn_number, e.response.status_code, e, exc_info=True)
            self.console.print(f"\n[bold red]Error HTTP del servidor LLM: {e.response.status_code}[/bold red]")
        except Exception as e:
            logger.error("SESIÓN CHAT | TURNO %d | Error inesperado: %s", self.turn_number, e, exc_info=True)
            self.console.print(f"\n[bold red]Error inesperado: {e}[/bold red]")

    def _show_stats(self):
        """Muestra una tabla con las estadísticas de la sesión."""
        uptime = int(time.time() - self.stats["start_time"])
        mins, secs = divmod(uptime, 60)

        table = Table(title="📊 Métricas de la Sesión y Memoria", border_style="cyan")
        table.add_column("Métrica", style="bold white")
        table.add_column("Valor", style="cyan")

        table.add_row("Turnos completados", str(self.agent.turn_count))
        table.add_row("Última velocidad", f"{self.stats['tok_s']:.1f} tok/s")
        table.add_row("Última latencia", f"{self.stats['latency']:.2f} s")
        table.add_row("Memoria RAM (RSS)", f"{self.stats['ram_mb']:.1f} MB")
        table.add_row("Conceptos en Wiki", str(self.stats["wiki_count"]))
        table.add_row("Tiempo de sesión", f"{mins}m {secs}s")

        self.console.print(table)

    def _show_wiki_tree_overview(self):
        """Muestra el árbol jerárquico completo de todos los conceptos en la wiki."""
        all_concepts = self.manager.list_all_concepts()
        self.console.print(f"[bold cyan]Total conceptos registrados: {len(all_concepts)}[/bold cyan]")
        for c in all_concepts:
            page = self.manager.get_concept(c)
            tags = f" [dim]{' '.join('#'+t for t in page.metadata.tags)}[/dim]" if page and page.metadata.tags else ""
            self.console.print(f"• [[{c}]]{tags}")

    def _read_concept(self, title: str):
        """Muestra el contenido de un concepto solicitado."""
        if not title:
            self.console.print("[red]Uso: /read <título>[/red]")
            return
        page = self.manager.get_concept(title)
        if not page:
            self.console.print(f"[bold red]Concepto '{title}' no encontrado.[/bold red]")
            return
        meta = page.metadata
        from rich.panel import Panel
        self.console.print(Panel(
            f"[bold cyan]Categoría:[/bold cyan] {meta.category}\n"
            f"[bold cyan]Tags:[/bold cyan] {', '.join(meta.tags)}\n\n"
            f"{page.content}",
            title=f"📖 {page.title}",
            border_style="green"
        ))
