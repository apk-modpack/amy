"""Sala de Chat GUI - Programa Servidor.

Ventana gráfica tkinter que actúa como interfaz humana de la sala de chat.
Gestiona la conexión de red con el Agente IA, muestra el historial de mensajes
y permite al usuario escribir y enviar mensajes.

Diseñado para ser robusto: tkinter no requiere dependencias externas y funciona
en cualquier instalación estándar de Python.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
import socket
import time
from datetime import datetime
from typing import Optional
import sys
import os

# Añadir el src al path si se ejecuta como script independiente
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.join(_PROJECT_ROOT, "src"))

from wiki_agent.network.server import ChatRoomServer, get_local_ip_addresses
from wiki_agent.network.protocol import MessageType, AgentState

logger = logging.getLogger(__name__)


# ─── Paleta de colores ────────────────────────────────────────────────────────
class Colors:
    BG_DARK      = "#1E1E2E"     # Fondo principal
    BG_PANEL     = "#2A2A3E"     # Fondo de paneles laterales
    BG_INPUT     = "#252535"     # Fondo de la entrada de texto
    BORDER       = "#3D3D5C"     # Color de borde
    TEXT_MAIN    = "#CDD6F4"     # Texto principal
    TEXT_DIM     = "#6E6C7E"     # Texto tenue
    TEXT_USER    = "#A6E3A1"     # Verde pastel (mensajes de usuario)
    TEXT_AI      = "#89B4FA"     # Azul pastel (mensajes de la IA)
    TEXT_STATUS  = "#FAB387"     # Naranja pastel (mensajes de sistema)
    TEXT_META    = "#CBA6F7"     # Morado pastel (métricas y metadatos)
    ACCENT_GREEN = "#A6E3A1"
    ACCENT_RED   = "#F38BA8"
    ACCENT_CYAN  = "#89DCEB"
    ACCENT_YELLOW = "#F9E2AF"
    BTN_SEND_BG  = "#89B4FA"     # Fondo botón Enviar
    BTN_SEND_FG  = "#1E1E2E"     # Texto botón Enviar


class ChatRoomApp:
    """Aplicación de ventana gráfica de la Sala de Chat."""

    DEFAULT_PORT = 8765
    PING_INTERVAL_MS = 5000          # ms entre latidos de conexión en la UI

    def __init__(self, root: tk.Tk, port: int = DEFAULT_PORT):
        self.root = root
        self.port = port
        self._server: Optional[ChatRoomServer] = None
        self._agent_connected = False

        self._setup_window()
        self._build_ui()
        self._start_server()

        # Programar el primer ciclo de actualización de UI
        self.root.after(self.PING_INTERVAL_MS, self._periodic_ui_refresh)

    # ─── Configuración de ventana ─────────────────────────────────────────────

    def _setup_window(self):
        self.root.title("Wiki-Memory — Sala de Chat")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        self.root.configure(bg=Colors.BG_DARK)

        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Barra de menú
        menubar = tk.Menu(
            self.root,
            bg=Colors.BG_PANEL, fg=Colors.TEXT_MAIN,
            activebackground=Colors.BORDER, activeforeground=Colors.TEXT_MAIN,
            relief="flat", bd=0
        )
        file_menu = tk.Menu(
            menubar, tearoff=0,
            bg=Colors.BG_PANEL, fg=Colors.TEXT_MAIN,
            activebackground=Colors.BORDER, activeforeground=Colors.TEXT_MAIN
        )
        file_menu.add_command(label="Salir", accelerator="Alt+F4", command=self._on_close)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        self.root.config(menu=menubar)

    # ─── Construcción de la UI ────────────────────────────────────────────────

    def _build_ui(self):
        """Construye todos los elementos de la interfaz gráfica."""

        # ── Frame superior: título + estado de conexión ──
        top_frame = tk.Frame(self.root, bg=Colors.BG_DARK, pady=8)
        top_frame.pack(fill=tk.X, padx=12)

        tk.Label(
            top_frame,
            text="🤖  Wiki-Memory — Sala de Chat",
            font=("Segoe UI", 16, "bold"),
            bg=Colors.BG_DARK,
            fg=Colors.TEXT_MAIN
        ).pack(side=tk.LEFT)

        # Panel de estado de la conexión (derecha del título)
        self._status_frame = tk.Frame(top_frame, bg=Colors.BG_PANEL, padx=12, pady=4,
                                       relief="flat", bd=0)
        self._status_frame.pack(side=tk.RIGHT, padx=(0, 4))

        self._conn_dot = tk.Label(self._status_frame, text="●", font=("Segoe UI", 11),
                                   bg=Colors.BG_PANEL, fg=Colors.ACCENT_RED)
        self._conn_dot.pack(side=tk.LEFT, padx=(0, 4))

        self._conn_label = tk.Label(self._status_frame, text="Sin conexión",
                                     font=("Segoe UI", 9),
                                     bg=Colors.BG_PANEL, fg=Colors.TEXT_DIM)
        self._conn_label.pack(side=tk.LEFT)

        # ── Separador ──
        sep = tk.Frame(self.root, bg=Colors.BORDER, height=1)
        sep.pack(fill=tk.X, padx=0)

        # ── Frame principal: chat + info lateral ──
        main_frame = tk.Frame(self.root, bg=Colors.BG_DARK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # ── Panel lateral: información del servidor y agente ──
        side_panel = tk.Frame(main_frame, bg=Colors.BG_PANEL, width=220, padx=10, pady=10)
        side_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(1, 0))
        side_panel.pack_propagate(False)

        tk.Label(
            side_panel, text="Información del servidor",
            font=("Segoe UI", 9, "bold"),
            bg=Colors.BG_PANEL, fg=Colors.TEXT_DIM
        ).pack(anchor=tk.W, pady=(0, 6))

        # IPs de escucha
        ips = get_local_ip_addresses()
        ip_list = "\n".join(ips) if ips else "No disponible"
        tk.Label(
            side_panel, text="📡 Escuchando en:",
            font=("Segoe UI", 8, "bold"),
            bg=Colors.BG_PANEL, fg=Colors.TEXT_STATUS
        ).pack(anchor=tk.W)
        self._ip_text = tk.Text(
            side_panel, height=len(ips), width=22,
            font=("Consolas", 9),
            bg=Colors.BG_DARK, fg=Colors.ACCENT_CYAN,
            relief="flat", state="disabled", cursor="arrow", padx=4
        )
        self._ip_text.pack(anchor=tk.W, pady=(0, 4))
        self._set_readonly_text(self._ip_text, ip_list)

        tk.Label(
            side_panel, text=f"🔌 Puerto: {self.port}",
            font=("Segoe UI", 9, "bold"),
            bg=Colors.BG_PANEL, fg=Colors.TEXT_STATUS
        ).pack(anchor=tk.W, pady=(0, 8))

        # Separador en el panel lateral
        tk.Frame(side_panel, bg=Colors.BORDER, height=1).pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            side_panel, text="Agente conectado",
            font=("Segoe UI", 9, "bold"),
            bg=Colors.BG_PANEL, fg=Colors.TEXT_DIM
        ).pack(anchor=tk.W, pady=(0, 4))

        self._agent_name_label = tk.Label(
            side_panel, text="—",
            font=("Segoe UI", 9), wraplength=180,
            bg=Colors.BG_PANEL, fg=Colors.TEXT_DIM
        )
        self._agent_name_label.pack(anchor=tk.W)

        self._agent_model_label = tk.Label(
            side_panel, text="Modelo: —",
            font=("Segoe UI", 8), wraplength=180,
            bg=Colors.BG_PANEL, fg=Colors.TEXT_DIM
        )
        self._agent_model_label.pack(anchor=tk.W, pady=(2, 0))

        # Indicador visual del ESTADO del agente (LISTO / PROCESANDO / ERROR)
        tk.Label(
            side_panel, text="Estado del agente:",
            font=("Segoe UI", 8, "bold"),
            bg=Colors.BG_PANEL, fg=Colors.TEXT_DIM
        ).pack(anchor=tk.W, pady=(8, 2))

        self._agent_state_frame = tk.Frame(side_panel, bg=Colors.BG_DARK, padx=6, pady=4)
        self._agent_state_frame.pack(fill=tk.X, pady=(0, 4))

        self._agent_state_dot = tk.Label(
            self._agent_state_frame, text="●", font=("Segoe UI", 10),
            bg=Colors.BG_DARK, fg=Colors.TEXT_DIM
        )
        self._agent_state_dot.pack(side=tk.LEFT, padx=(0, 4))

        self._agent_state_label = tk.Label(
            self._agent_state_frame, text="DESCONECTADO",
            font=("Segoe UI", 8, "bold"),
            bg=Colors.BG_DARK, fg=Colors.TEXT_DIM
        )
        self._agent_state_label.pack(side=tk.LEFT)

        # Espaciador flexible
        tk.Frame(side_panel, bg=Colors.BG_PANEL).pack(fill=tk.BOTH, expand=True)

        # Botón para limpiar el historial de chat
        tk.Button(
            side_panel, text="Limpiar chat",
            font=("Segoe UI", 8),
            bg=Colors.BG_DARK, fg=Colors.TEXT_DIM,
            activebackground=Colors.BORDER, activeforeground=Colors.TEXT_MAIN,
            relief="flat", cursor="hand2",
            command=self._clear_chat
        ).pack(fill=tk.X, pady=(0, 4))

        # Botón para cerrar la aplicación
        tk.Button(
            side_panel, text="✕  Cerrar aplicación",
            font=("Segoe UI", 8),
            bg="#3D1A1A", fg=Colors.ACCENT_RED,
            activebackground="#5C2A2A", activeforeground=Colors.TEXT_MAIN,
            relief="flat", cursor="hand2",
            command=self._on_close
        ).pack(fill=tk.X, pady=(0, 0))

        # ── Área central: historial de chat ──
        chat_frame = tk.Frame(main_frame, bg=Colors.BG_DARK)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            state="disabled",
            font=("Segoe UI", 11),
            bg=Colors.BG_DARK,
            fg=Colors.TEXT_MAIN,
            insertbackground=Colors.TEXT_MAIN,
            relief="flat",
            padx=14,
            pady=10,
            cursor="arrow",
        )
        self._chat_display.pack(fill=tk.BOTH, expand=True)

        # Configurar etiquetas de color para diferentes tipos de mensajes
        self._chat_display.tag_configure("user",    foreground=Colors.TEXT_USER,   font=("Segoe UI", 11, "bold"))
        self._chat_display.tag_configure("ai",      foreground=Colors.TEXT_AI,     font=("Segoe UI", 11, "bold"))
        self._chat_display.tag_configure("status",  foreground=Colors.TEXT_STATUS, font=("Segoe UI", 9, "italic"))
        self._chat_display.tag_configure("meta",    foreground=Colors.TEXT_META,   font=("Segoe UI", 8))
        self._chat_display.tag_configure("system",  foreground=Colors.TEXT_DIM,    font=("Segoe UI", 9, "italic"))
        self._chat_display.tag_configure("body",    foreground=Colors.TEXT_MAIN)

        # ── Barra de estado de la IA (mini-panel entre chat e input) ──
        self._ai_status_bar = tk.Label(
            chat_frame, text="",
            font=("Segoe UI", 9, "italic"),
            bg=Colors.BG_PANEL, fg=Colors.TEXT_STATUS,
            anchor=tk.W, padx=14, pady=3
        )
        self._ai_status_bar.pack(fill=tk.X)

        # ── Área de entrada de texto ──
        input_frame = tk.Frame(self.root, bg=Colors.BG_INPUT, pady=10)
        input_frame.pack(fill=tk.X, padx=0, pady=0, side=tk.BOTTOM)

        self._input_box = tk.Text(
            input_frame,
            height=3,
            font=("Segoe UI", 11),
            bg=Colors.BG_INPUT,
            fg=Colors.TEXT_MAIN,
            insertbackground=Colors.TEXT_MAIN,
            relief="flat",
            padx=14, pady=6,
            wrap=tk.WORD,
        )
        self._input_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 6))
        self._input_box.bind("<Return>",        self._on_enter_key)
        self._input_box.bind("<Shift-Return>",  lambda e: None)  # Shift+Enter = nueva línea (default)
        self._input_box.focus_set()

        self._send_btn = tk.Button(
            input_frame,
            text="Enviar →",
            font=("Segoe UI", 10, "bold"),
            bg=Colors.BTN_SEND_BG,
            fg=Colors.BTN_SEND_FG,
            activebackground=Colors.ACCENT_CYAN,
            activeforeground=Colors.BG_DARK,
            relief="flat",
            cursor="hand2",
            padx=16, pady=8,
            command=self._send_message,
        )
        self._send_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # Etiqueta de ayuda de teclado
        tk.Label(
            input_frame, text="Enter: enviar · Shift+Enter: nueva línea",
            font=("Segoe UI", 7),
            bg=Colors.BG_INPUT, fg=Colors.TEXT_DIM
        ).pack(side=tk.RIGHT, padx=(0, 10))

    # ─── Lógica del servidor ──────────────────────────────────────────────────

    def _start_server(self):
        """Inicializa y arranca el servidor de la Sala de Chat."""
        self._server = ChatRoomServer(
            host="0.0.0.0",
            port=self.port,
            on_agent_connected=self._on_agent_connected,
            on_agent_disconnected=self._on_agent_disconnected,
            on_agent_response=self._on_agent_response,
            on_agent_status=self._on_agent_status,
        )
        try:
            self._server.start()
            self._append_system_message(
                f"Servidor iniciado. Esperando conexión del Agente IA en el puerto {self.port}…"
            )
        except Exception as e:
            self._append_system_message(
                f"⚠️  Error al iniciar el servidor: {e}"
            )

    # ─── Callbacks del servidor (ejecutados desde hilos de red) ──────────────

    def _on_agent_connected(self, info: dict):
        """Callback: el agente IA se ha conectado."""
        self._agent_connected = True
        name = info.get("client_name", "Agente desconocido")
        model = info.get("model_name", "—")
        self.root.after(0, self._update_connection_ui, True, name, model)

    def _on_agent_disconnected(self):
        """Callback: el agente IA se ha desconectado."""
        self._agent_connected = False
        self.root.after(0, self._update_connection_ui, False, "—", "—")

    def _on_agent_response(self, payload: dict):
        """Callback: respuesta final recibida del agente."""
        text = payload.get("text", "")
        metadata = payload.get("metadata", {})
        self.root.after(0, self._render_agent_response, text, metadata)

    def _on_agent_status(self, payload: dict):
        """Callback: notificación de estado del agente."""
        state = payload.get("state")
        status = payload.get("status", "")
        detail = payload.get("detail", "")
        # Actualizar tanto la barra de actividad como el indicador canónico de estado
        if state:
            self.root.after(0, self._set_agent_state_indicator, state)
            # Si el agente vuelve a estar LISTO o en ERROR, rehabilitar el input
            state_upper = str(state).upper()
            if state_upper in (AgentState.LISTO.value, AgentState.ERROR.value):
                self.root.after(0, self._set_input_enabled, True)
        self.root.after(0, self._update_ai_status_bar, status or state, detail)

    # ─── Actualización de UI (siempre en el hilo principal) ──────────────────

    def _set_agent_state_indicator(self, state: str):
        """Actualiza el indicador visual del estado formal del agente (LISTO / PROCESANDO / ERROR)."""
        state_upper = (state or "").upper()
        if state_upper == AgentState.LISTO.value:
            self._agent_state_dot.configure(fg=Colors.ACCENT_GREEN)
            self._agent_state_label.configure(text="LISTO", fg=Colors.ACCENT_GREEN)
        elif state_upper == AgentState.PROCESANDO.value:
            self._agent_state_dot.configure(fg=Colors.ACCENT_YELLOW)
            self._agent_state_label.configure(text="PROCESANDO", fg=Colors.ACCENT_YELLOW)
        elif state_upper == AgentState.ERROR.value:
            self._agent_state_dot.configure(fg=Colors.ACCENT_RED)
            self._agent_state_label.configure(text="ERROR", fg=Colors.ACCENT_RED)
        else:
            self._agent_state_dot.configure(fg=Colors.TEXT_DIM)
            self._agent_state_label.configure(text=state_upper or "DESCONOCIDO", fg=Colors.TEXT_DIM)

    def _update_connection_ui(self, connected: bool, name: str, model: str):
        if connected:
            self._conn_dot.configure(fg=Colors.ACCENT_GREEN)
            self._conn_label.configure(text="Agente conectado", fg=Colors.ACCENT_GREEN)
            self._agent_name_label.configure(text=name, fg=Colors.TEXT_MAIN)
            self._agent_model_label.configure(text=f"Modelo: {model}", fg=Colors.TEXT_MAIN)
            self._set_agent_state_indicator(AgentState.LISTO.value)
            self._set_input_enabled(True)
            self._append_system_message(f"✅  Agente '{name}' ({model}) conectado.")
        else:
            self._conn_dot.configure(fg=Colors.ACCENT_RED)
            self._conn_label.configure(text="Sin conexión", fg=Colors.TEXT_DIM)
            self._agent_name_label.configure(text="—", fg=Colors.TEXT_DIM)
            self._agent_model_label.configure(text="Modelo: —", fg=Colors.TEXT_DIM)
            self._agent_state_dot.configure(fg=Colors.TEXT_DIM)
            self._agent_state_label.configure(text="DESCONECTADO", fg=Colors.TEXT_DIM)
            self._set_input_enabled(False)
            self._append_system_message("⚠️  El Agente IA se ha desconectado.")

    def _render_agent_response(self, text: str, metadata: dict):
        """Renderiza en el chat la respuesta final del agente."""
        self._set_agent_state_indicator(AgentState.LISTO.value)
        self._update_ai_status_bar("", "")   # Limpiar barra de estado
        ts = datetime.now().strftime("%H:%M")
        self._append_to_chat("\n")
        self._append_to_chat(f"[{ts}] Agente IA\n", tag="ai")
        self._append_to_chat(text + "\n", tag="body")

        if metadata:
            meta_parts = []
            if "tok_s" in metadata:
                meta_parts.append(f"⚡ {metadata['tok_s']:.1f} tok/s")
            if "latency" in metadata:
                meta_parts.append(f"⏱ {metadata['latency']:.2f}s")
            if "wiki_count" in metadata:
                meta_parts.append(f"📚 Wiki: {metadata['wiki_count']} conceptos")
            if meta_parts:
                self._append_to_chat("  " + " · ".join(meta_parts) + "\n", tag="meta")

        self._set_input_enabled(True)

    def _update_ai_status_bar(self, status: str, detail: str = ""):
        """Actualiza la barra de estado intermedio de la IA."""
        if not status:
            self._ai_status_bar.configure(text="")
            return
        icons = {
            "thinking": "🧠",
            "searching": "🔍",
            "reading": "📖",
            "saving": "💾",
            "done": "✅",
            "queue": "📥",
        }
        icon = icons.get(status, "⏳")
        display = f"  {icon}  {detail or status.capitalize()}…"
        self._ai_status_bar.configure(text=display)

    def _periodic_ui_refresh(self):
        """Tarea periódica de actualización: sincroniza estado visual con estado real."""
        if self._server:
            connected = self._server.is_agent_connected
            dot_color = self._conn_dot.cget("fg")
            is_green = (dot_color == Colors.ACCENT_GREEN)
            if connected != is_green:
                if connected:
                    info = self._server.current_agent_info
                    self._update_connection_ui(True, info.get("client_name", "Agente"), info.get("model_name", "—"))
                else:
                    self._update_connection_ui(False, "—", "—")
            elif connected:
                # Si el agente está conectado y el estado formal reportado es LISTO,
                # asegurar que la caja de texto esté activa para evitar bloqueos residuales
                agent_state = (self._server.current_agent_state or "").upper()
                if agent_state == AgentState.LISTO.value:
                    if str(self._input_box.cget("state")) != "normal":
                        self._set_input_enabled(True)
        self.root.after(self.PING_INTERVAL_MS, self._periodic_ui_refresh)

    # ─── Acciones del usuario ─────────────────────────────────────────────────

    def _on_enter_key(self, event):
        """Enviar con Enter (Shift+Enter inserta línea nueva por defecto)."""
        self._send_message()
        return "break"     # Evitar que el Enter se inserte como '\n'

    def _send_message(self):
        """Obtiene el texto del input, lo muestra en pantalla y lo envía al agente."""
        text = self._input_box.get("1.0", tk.END).strip()
        if not text:
            return

        if not self._server or not self._server.is_agent_connected:
            messagebox.showwarning(
                "Sin conexión",
                "No hay ningún Agente IA conectado actualmente.\n\nEspera a que el agente se conecte."
            )
            return

        # Mostrar el mensaje del usuario en el chat
        ts = datetime.now().strftime("%H:%M")
        self._append_to_chat("\n")
        self._append_to_chat(f"[{ts}] Tú\n", tag="user")
        self._append_to_chat(text + "\n", tag="body")

        # Enviar al agente
        sent = self._server.send_user_message(text)

        # Limpiar el input siempre
        self._input_box.delete("1.0", tk.END)

        if sent:
            self._set_agent_state_indicator(AgentState.PROCESANDO.value)
            self._update_ai_status_bar("thinking", "Procesando mensaje (cola activa)")
            # La caja de texto NO se deshabilita: se permite enviar múltiples mensajes a la cola
            self._input_box.focus_set()
        else:
            self._append_system_message("❌  Error al enviar el mensaje al agente.")

    def _clear_chat(self):
        self._chat_display.configure(state="normal")
        self._chat_display.delete("1.0", tk.END)
        self._chat_display.configure(state="disabled")

    # ─── Helpers de UI ───────────────────────────────────────────────────────

    def _append_to_chat(self, text: str, tag: str = "body"):
        """Añade texto al historial de chat respetando el tag de color."""
        self._chat_display.configure(state="normal")
        self._chat_display.insert(tk.END, text, tag)
        self._chat_display.configure(state="disabled")
        self._chat_display.see(tk.END)

    def _append_system_message(self, msg: str):
        ts = datetime.now().strftime("%H:%M")
        self._append_to_chat(f"\n[{ts}] {msg}\n", tag="system")

    def _set_input_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self._input_box.configure(state=state)
        self._send_btn.configure(state=state)
        if enabled:
            self._input_box.focus_set()

    @staticmethod
    def _set_readonly_text(widget: tk.Text, content: str):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.configure(state="disabled")

    # ─── Cierre de la aplicación ──────────────────────────────────────────────

    def _on_close(self):
        """Cierra la aplicación de forma ordenada.

        Si hay un agente conectado, solicita confirmación antes de cerrar para
        evitar interrupciones accidentales de sesiones activas.
        """
        if self._agent_connected:
            if not messagebox.askyesno(
                "Cerrar Sala de Chat",
                "Hay un agente IA conectado actualmente.\n\n"
                "¿Deseas cerrar la sala de chat igualmente?\n"
                "El agente perderá la conexión.",
                icon="warning"
            ):
                return
        if self._server:
            self._server.stop()
        self.root.destroy()


def run_chat_room(port: int = ChatRoomApp.DEFAULT_PORT):
    """Punto de entrada para la Sala de Chat."""
    root = tk.Tk()
    app = ChatRoomApp(root, port=port)
    root.mainloop()


if __name__ == "__main__":
    run_chat_room()

