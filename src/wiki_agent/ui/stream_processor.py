"""Procesador de flujo continuo de tokens del LLM (streaming).

Maneja la máquina de estados durante la generación para mostrar en tiempo real
únicamente el razonamiento (<thought> o [PENSAMIENTO INTERNO]) en estilo tenue,
mientras suprime de forma transparente los bloques intermedios de respuesta o comandos.
"""

from typing import Optional
import sys


class TokenStreamProcessor:
    """Procesador de tokens con máquina de estados para terminal."""

    def __init__(
        self,
        thought_start: str = "<thought>",
        thought_end: str = "</thought>",
        response_start: str = "<response>",
    ):
        self.buffer = ""
        self.token_count = 0

        # Bloque Thought
        self.thought_start = thought_start
        self.thought_end = thought_end
        self.in_thought = False
        self.thought_printed = 0
        self.thought_done = False
        self.thought_header_shown = False
        self.active_end = thought_end

        # Bloque Response
        self.start_tag = response_start
        self.start_idx = -1
        self.has_started = False
        self.stream_active = False

    def reset_cycle(self):
        """Reinicia el procesador para un nuevo ciclo dentro del mismo turno."""
        self.buffer = ""
        self.in_thought = False
        self.thought_printed = 0
        self.thought_done = False
        self.thought_header_shown = False
        self.active_end = self.thought_end
        self.start_idx = -1
        self.has_started = False
        self.stream_active = False

    def __call__(self, token: str):
        """Consume cada token emitido por el LLM en streaming."""
        self.token_count += 1
        self.buffer += token

        # 1. Detección de inicio de Thought (<thought> o [PENSAMIENTO INTERNO])
        t_start = self.buffer.find(self.thought_start)
        active_end = self.thought_end
        tag_len = len(self.thought_start)

        if t_start == -1:
            t_start = self.buffer.find("[PENSAMIENTO INTERNO]")
            if t_start != -1:
                active_end = "[/PENSAMIENTO INTERNO]"
                tag_len = len("[PENSAMIENTO INTERNO]")

        if t_start != -1 and not self.in_thought:
            self.in_thought = True
            self.stream_active = True
            self.active_end = active_end
            self.thought_printed = t_start + tag_len
            if not self.thought_header_shown:
                print(f"\r{' ' * 80}\r", end="", flush=True)
                print("\n  \033[2m🧠 Razonando...", end="", flush=True)
                self.thought_header_shown = True

        # 2. Transmisión gradual de contenido dentro de Thought
        if self.in_thought:
            t_end = self.buffer.find(self.active_end, self.thought_printed)
            if t_end != -1:
                to_print = self.buffer[self.thought_printed:t_end]
                if to_print:
                    print(to_print, end="", flush=True)
                print("\033[0m\n", end="", flush=True)  # Reset de color ansi y salto
                self.thought_printed = t_end + len(self.active_end)
                self.in_thought = False
                self.thought_done = True
            else:
                to_print = self.buffer[self.thought_printed:]
                safe_len = len(to_print)
                for i in range(1, len(self.active_end)):
                    if to_print.endswith(self.active_end[:i]):
                        safe_len -= i
                        break
                if safe_len > 0:
                    print(to_print[:safe_len], end="", flush=True)
                    self.thought_printed += safe_len
            return

        # 3. Marcar si <response> o similar ha comenzado (no se imprime en vivo para evitar leaks)
        if self.start_idx == -1:
            self.start_idx = self.buffer.find(self.start_tag)
            if self.start_idx == -1:
                self.start_idx = self.buffer.find("[RESPUESTA AUTÓNOMA]")
            if self.start_idx != -1:
                self.has_started = True
