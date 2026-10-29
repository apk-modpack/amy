"""Renderizador Rich y utilidades visuales de la interfaz de consola.

Encapsula el diseño visual, cabeceras, tablas, árbol conceptual y formato de métricas.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.table import Table


class ConsoleRenderer:
    """Gestiona los elementos visuales de la terminal con Rich."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    @staticmethod
    def get_process_memory_mb() -> float:
        """Obtiene el uso de memoria RAM (WorkingSetSize) del proceso actual en MB."""
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

    def render_header(self, llm: Any, no_memory: bool) -> Panel:
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

    def render_wiki_tree(self, concepts: List[str], manager: Any):
        """Renderiza el árbol jerárquico de conceptos wiki consultados."""
        self.console.print("[dim cyan]📚 Árbol conceptual consultado:[/dim cyan]")
        for i, concept in enumerate(concepts):
            is_last = (i == len(concepts) - 1)
            branch = "└──" if is_last else "├──"
            try:
                page = manager.get_concept(concept)
                links = page.outgoing_links[:3] if page and page.outgoing_links else []
                tags = page.metadata.tags[:2] if page and page.metadata.tags else []
                tag_str = f" [dim]{' '.join('#'+t for t in tags)}[/dim]" if tags else ""
                self.console.print(f"[dim cyan]  {branch} [[{concept}]]{tag_str}[/dim cyan]")
                for j, link in enumerate(links):
                    sub_last = (j == len(links) - 1)
                    sub_branch = "    └──" if sub_last else "    ├──"
                    self.console.print(f"[dim]  {sub_branch} → {link}[/dim]")
            except Exception:
                self.console.print(f"[dim cyan]  {branch} [[{concept}]][/dim cyan]")

    def render_turn_metrics(self, tok_per_sec: float, elapsed: float, ram_mb: float, wiki_count: int):
        """Muestra la insignia de métricas al final de cada turno."""
        self.console.print(Align.right(
            f"[dim]⚡ [bold magenta]{tok_per_sec:.1f} tok/s[/bold magenta] · "
            f"⏱️ [cyan]{elapsed:.2f}s[/cyan] · "
            f"💾 [yellow]RAM: {ram_mb:.1f} MB[/yellow] · "
            f"📚 [green]Wiki: {wiki_count} conceptos[/green][/dim]"
        ))

    def render_help(self):
        """Muestra la tabla de ayuda de comandos interactivos."""
        self.console.print(Panel(
            "[cyan]/stats[/cyan]            — Muestra métricas de la sesión y memoria\n"
            "[cyan]/tree[/cyan]             — Muestra árbol conceptual completo de la Wiki\n"
            "[cyan]/save <título>[/cyan]     — Guarda la última respuesta como concepto\n"
            "[cyan]/edit <título>[/cyan]     — Edita un concepto existente con la última respuesta\n"
            "[cyan]/read <título>[/cyan]     — Muestra un concepto de la Wiki\n"
            "[cyan]/delete <título>[/cyan]   — Elimina un concepto de la Wiki\n"
            "[cyan]/clear[/cyan]            — Limpia pantalla e historial de la sesión\n"
            "[cyan]/exit[/cyan]             — Termina el chat\n"
            "[cyan]/help[/cyan]             — Muestra esta ayuda",
            title="Comandos disponibles",
            border_style="dim"
        ))
