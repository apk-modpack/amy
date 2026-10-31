"""Sesión de chat interactiva (REPL) orientada a objetos.

Maneja el bucle de conversación con el usuario, la captura de comandos especiales
de terminal (/stats, /tree, /save, /edit, /read, /delete, /clear, /exit, /help) y
la coordinación con WikiAgent, ConsoleRenderer y TokenStreamProcessor.

Soporta dos modos de entrada:
  - LOCAL: entrada por teclado (modo por defecto, comportamiento original).
  - NETWORK: entrada recibida desde la Sala de Chat remota a través de AgentNetworkClient.
"""

from typing import Optional, Dict, Any
import time
import httpx
import logging
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.panel import Panel

from wiki_agent.agent.loop import WikiAgent
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.ui.renderer import ConsoleRenderer
from wiki_agent.ui.stream_processor import TokenStreamProcessor
from wiki_agent.domain import CognitiveAgent, AgentTurnResult

logger = logging.getLogger(__name__)


class InteractiveChatSession:
    """Sesión interactiva en terminal con ciclo conversacional y métricas.

    Args:
        agent: Instancia del agente WikiAgent.
        manager: Gestor de la base de conocimientos wiki.
        renderer: Renderizador de consola Rich (opcional).
        console: Consola Rich (opcional).
        no_memory: Si True, desactiva la inyección de contexto wiki.
        network_client: Si se proporciona, la sesión opera en modo NETWORK,
                        recibiendo inputs desde la Sala de Chat remota en lugar
                        del teclado. El cliente ya debe estar conectado y con
                        el handshake completado antes de pasarlo aquí.
    """

    def __init__(
        self,
        agent: WikiAgent,
        manager: WikiKnowledgeManager,
        renderer: Optional[ConsoleRenderer] = None,
        console: Optional[Console] = None,
        no_memory: bool = False,
        network_client=None,   # Optional[AgentNetworkClient] — sin importar para evitar circular
    ):
        self.agent = agent
        self.manager = manager
        self.console = console or Console()
        self.renderer = renderer or ConsoleRenderer(self.console)
        self.no_memory = no_memory
        self._network_client = network_client
        self._network_mode = network_client is not None

        self.stats: Dict[str, Any] = {
            "tok_s": 0.0,
            "latency": 0.0,
            "ram_mb": 0.0,
            "wiki_count": len(self.manager.list_all_concepts()),
            "start_time": time.time(),
        }
        self.turn_number = 0

    # ─── Bucle principal ──────────────────────────────────────────────────────

    def start(self):
        """Inicia y mantiene el bucle interactivo hasta /exit o EOF."""
        self.console.clear()
        self.console.print(self.renderer.render_header(self.agent.llm, self.no_memory))

        # Mostrar indicador del modo de entrada activo
        if self._network_mode:
            self.console.print(Panel(
                "[bold cyan]Modo RED activo.[/bold cyan] "
                "Los inputs se reciben desde la Sala de Chat remota.\n"
                "[dim]La interfaz de terminal sigue activa para observación. "
                "Para terminar, cierra el agente o la Sala de Chat.[/dim]",
                border_style="cyan",
                title="🌐 Modo Sala de Chat"
            ))
        self.console.print()

        logger.info(
            "SESIÓN CHAT | INICIADA. Modelo: %s | Memoria: %s | Modo: %s",
            self.agent.llm.model_name,
            "DESACTIVADA" if self.no_memory else "ACTIVA",
            "NETWORK" if self._network_mode else "LOCAL"
        )

        if self._network_mode:
            self._run_network_loop()
        else:
            self._run_local_loop()

    # ─── Bucle LOCAL (teclado) ────────────────────────────────────────────────

    def _run_local_loop(self):
        """Bucle de entrada por teclado (modo original)."""
        while True:
            try:
                user_input = Prompt.ask("\n[bold green]Tú[/bold green]").strip()
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[dim]Saliendo...[/dim]")
                break

            if not user_input:
                continue

            if self._handle_session_command(user_input):
                continue

            self._execute_turn(user_input)

    # ─── Bucle NETWORK (Sala de Chat remota) ──────────────────────────────────

    def _run_network_loop(self):
        """Bucle de entrada desde la Sala de Chat vía red con cola asíncrona de mensajes."""
        import queue
        import threading
        from wiki_agent.network.protocol import MessageType, AgentState

        message_queue = queue.Queue()
        stop_event = threading.Event()

        def worker_loop():
            """Hilo trabajador que consume secuencialmente la cola de mensajes."""
            while not stop_event.is_set():
                try:
                    item = message_queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if item is None:
                    break

                sender, user_input = item
                remaining = message_queue.qsize()

                # Notificar a la Sala de Chat que el agente pasa a PROCESANDO
                status_detail = f"Respondiendo a {sender}..." if remaining == 0 else f"Respondiendo a {sender}... ({remaining} en cola)"
                self._send_network_state(AgentState.PROCESANDO, status_detail)

                # Comandos de sesión también se aceptan desde la red
                if self._handle_session_command(user_input):
                    next_state = AgentState.PROCESANDO if message_queue.qsize() > 0 else AgentState.LISTO
                    self._send_network_state(next_state, "Comando ejecutado")
                    message_queue.task_done()
                    continue

                # Formatear el mensaje con el prefijo de emisor si no es humano simple
                contextualized_input = f"[DE: {sender}]\n{user_input}" if sender != "HUMAN" else user_input

                # Ejecutar turno y capturar resultado
                result = self._execute_turn_network(contextualized_input)

                if result is not None:
                    meta = {
                        "tok_s": self.stats.get("tok_s", 0.0),
                        "latency": self.stats.get("latency", 0.0),
                        "ram_mb": self.stats.get("ram_mb", 0.0),
                        "wiki_count": self.stats.get("wiki_count", 0),
                    }
                    self._network_client.send_response(result.response_text, metadata=meta)
                else:
                    self._send_network_state(AgentState.ERROR, "Fallo al generar respuesta")

                message_queue.task_done()

                # Si no quedan más mensajes en cola, volver a estado LISTO
                if message_queue.qsize() == 0:
                    self._send_network_state(AgentState.LISTO, "Listo para nuevo mensaje")

        # Iniciar hilo de procesamiento de la cola
        worker_thread = threading.Thread(target=worker_loop, daemon=True, name="ChatSession-Worker")
        worker_thread.start()

        self.console.print("[dim]⏳ Esperando mensajes desde la Sala de Chat...[/dim]")
        # Notificar a la Sala de Chat que el agente está LISTO para recibir input
        self._send_network_state(AgentState.LISTO, "Esperando mensaje...")

        try:
            while True:
                try:
                    msg = self._network_client.receive_message()
                except KeyboardInterrupt:
                    self.console.print("\n[dim]Interrumpido por el usuario. Cerrando...[/dim]")
                    break
                except Exception as e:
                    logger.error("Error leyendo mensaje de red: %s", e)
                    self.console.print(f"\n[bold red]Error de red: {e}[/bold red]")
                    self._send_network_state(AgentState.ERROR, f"Fallo de conexión: {e}")
                    break

                if msg is None:
                    # La Sala de Chat cerró la conexión
                    self.console.print("\n[bold yellow]La Sala de Chat cerró la conexión.[/bold yellow]")
                    logger.info("SESIÓN CHAT | Sala de Chat desconectada.")
                    break

                if msg.type == MessageType.CHAT_MESSAGE:
                    user_input = msg.payload.get("text", "").strip()
                    sender = msg.payload.get("sender", "HUMAN")
                    if not user_input:
                        continue

                    # Mostrar en terminal lo que llegó desde la red indicando el remitente
                    sender_display = "Humano (HUMAN)" if sender == "HUMAN" else f"Agente ({sender})"
                    self.console.print(f"\n[bold green]De [{sender_display}]:[/bold green] {user_input}")

                    # Encolar el mensaje para procesamiento secuencial
                    message_queue.put((sender, user_input))
                    q_len = message_queue.qsize()
                    if q_len > 1:
                        self.console.print(f"[dim]📥 Mensaje encolado (posición {q_len})[/dim]")
                        self._send_network_status("queue", f"{q_len} mensajes en cola")

                elif msg.type == MessageType.AGENT_LIST:
                    agents = msg.payload.get("agents", [])
                    self._network_client.connected_agents = agents
                    nombres = [a.get("client_name", "Desconocido") for a in agents]
                    self.console.print(f"[dim]👥 Agentes presentes en la sala: {', '.join(nombres) if nombres else 'Ninguno'}[/dim]")

                elif msg.type == MessageType.PING:
                    from wiki_agent.network.protocol import make_pong
                    if hasattr(self._network_client, "_conn") and self._network_client._conn:
                        self._network_client._conn.send_message(make_pong())
        finally:
            stop_event.set()
            message_queue.put(None)
            worker_thread.join(timeout=1.0)

    def _send_network_state(self, state, detail: str = ""):
        """Envía una actualización del estado canónico del agente (LISTO/PROCESANDO/ERROR)."""
        if self._network_mode and self._network_client:
            try:
                self._network_client.send_state(state, detail)
            except Exception as e:
                logger.warning("No se pudo enviar estado formal de red: %s", e)

    def _send_network_status(self, status: str, detail: str = ""):
        """Envía un mensaje de estado al cliente de red si está en modo red."""
        if self._network_mode and self._network_client:
            try:
                self._network_client.send_status(status, detail)
            except Exception as e:
                logger.warning("No se pudo enviar estado de red: %s", e)

    # ─── Comandos de sesión ───────────────────────────────────────────────────

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

        if cmd_lower in ("/agents", "agents"):
            if self._network_mode and self._network_client:
                agents = getattr(self._network_client, "connected_agents", [])
                if not agents:
                    self.console.print("[yellow]No hay otros agentes registrados en la sala actualmente.[/yellow]")
                else:
                    self.console.print(f"[bold cyan]Agentes en la sala ({len(agents)}):[/bold cyan]")
                    for a in agents:
                        self.console.print(f"- [bold]{a.get('client_name')}[/bold] (Modelo: {a.get('model_name')}) [dim]ID: {a.get('client_id', 'N/A')}[/dim]")
            else:
                self.console.print("[yellow]El comando /agents solo está activo en modo red (conectado a una sala).[/yellow]")
            return True

        if cmd_lower in ("/identify", "identify", "/whoami"):
            res = self.agent.dispatcher.dispatch("/identify")
            self.console.print(Panel(res, title="🪪 Identidad del Agente", border_style="cyan"))
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

    # ─── Ejecución de turno ───────────────────────────────────────────────────

    def _execute_turn(self, user_input: str):
        """Ejecuta un turno completo de interacción (modo local — sin retorno)."""
        self._execute_turn_network(user_input)

    def _execute_turn_network(self, user_input: str) -> Optional[AgentTurnResult]:
        """Ejecuta un turno completo y retorna el resultado (modo red o local)."""
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
                    if self._network_mode:
                        self._send_network_status("searching", f"Consultando wiki: {', '.join(concepts[:3])}")
                elif kind == "thought":
                    logger.debug("SESIÓN CHAT | STATUS CALLBACK | thought procesado en streaming.")
                elif kind == "cycle_start":
                    cycle_num = msg[1]
                    model_name = msg[2] if len(msg) > 2 else "?"
                    logger.debug("SESIÓN CHAT | STATUS CALLBACK | cycle_start | ciclo=%d", cycle_num)
                    stream_processor.reset_cycle()
                    print(f"\r{' ' * 80}\r", end="", flush=True)
                    self.console.print(f"[dim]🧠 Procesando modelo ({model_name}) - Ciclo {cycle_num}...[/dim]")
                    if self._network_mode:
                        self._send_network_status("thinking", f"Ciclo {cycle_num} de razonamiento…")
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

            # Imprimir respuesta final limpia en la terminal
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

            if self._network_mode:
                self._send_network_status("done", "Respuesta lista")

            logger.info("SESIÓN CHAT | === TURNO %d — FIN ===", self.turn_number)
            self.console.print()

            return result

        except httpx.ConnectError as e:
            logger.error("SESIÓN CHAT | TURNO %d | ConnectError: %s", self.turn_number, e, exc_info=True)
            self.console.print("\n[bold red]Error: El servidor LLM dejó de responder. ¿Sigue corriendo?[/bold red]")
        except httpx.HTTPStatusError as e:
            logger.error("SESIÓN CHAT | TURNO %d | HTTPStatusError %d: %s", self.turn_number, e.response.status_code, e, exc_info=True)
            self.console.print(f"\n[bold red]Error HTTP del servidor LLM: {e.response.status_code}[/bold red]")
        except Exception as e:
            logger.error("SESIÓN CHAT | TURNO %d | Error inesperado: %s", self.turn_number, e, exc_info=True)
            self.console.print(f"\n[bold red]Error inesperado: {e}[/bold red]")

        return None

    # ─── Comandos de información ──────────────────────────────────────────────

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
        table.add_row("Modo de entrada", "🌐 RED" if self._network_mode else "⌨️  LOCAL")

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
        self.console.print(Panel(
            f"[bold cyan]Categoría:[/bold cyan] {meta.category}\n"
            f"[bold cyan]Tags:[/bold cyan] {', '.join(meta.tags)}\n\n"
            f"{page.content}",
            title=f"📖 {page.title}",
            border_style="green"
        ))
