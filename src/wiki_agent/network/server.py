"""Servidor de socket para la Sala de Chat (Programa Servidor).

Maneja la recepción de conexiones del Agente IA, la negociación de handshake,
el despacho bidireccional de mensajes y la detección de estado de red.
"""

import socket
import threading
import logging
from typing import Optional, Callable, Dict, Any, List
from wiki_agent.network.protocol import (
    NetworkMessage,
    MessageType,
    AgentState,
    HUMAN_SENDER,
    make_handshake_ack,
    make_chat_message,
    make_agent_list,
    make_pong,
)
from wiki_agent.network.connection import RobustSocketConnection

logger = logging.getLogger(__name__)


def get_local_ip_addresses() -> List[str]:
    """Obtiene las direcciones IP locales disponibles para facilitar la conexión al usuario."""
    ips = []
    # 1. Intentar descubrir la IP de la interfaz por la que se saldría a la red
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # No se envía tráfico real, solo se resuelve la interfaz de ruta
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        if primary_ip and primary_ip not in ips and not primary_ip.startswith("127."):
            ips.append(primary_ip)
    except Exception:
        pass

    # 2. Obtener IPs asociadas al hostname
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass

    # Siempre incluir localhost como alternativa
    if "127.0.0.1" not in ips:
        ips.append("127.0.0.1")

    return ips


class ChatRoomServer:
    """Servidor TCP de la Sala de Chat que coordina la comunicación con el Agente IA."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        on_agent_connected: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_agent_disconnected: Optional[Callable[[], None]] = None,
        on_agent_response: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_agent_status: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.host = host
        self.port = port
        self.on_agent_connected = on_agent_connected
        self.on_agent_disconnected = on_agent_disconnected
        self.on_agent_response = on_agent_response
        self.on_agent_status = on_agent_status

        self._server_sock: Optional[socket.socket] = None
        self._current_client: Optional[RobustSocketConnection] = None
        self._current_agent_info: Dict[str, Any] = {}
        self._current_agent_state: Optional[str] = None
        self._connected_clients: Dict[RobustSocketConnection, Dict[str, Any]] = {}
        self._is_running = False
        self._accept_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def start(self):
        """Inicia el servidor y escucha conexiones en segundo plano."""
        if self._is_running:
            return

        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.host, self.port))
        self._server_sock.listen(2)
        self._is_running = True

        logger.info("Servidor de Sala de Chat iniciado en %s:%d", self.host, self.port)

        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True, name="ChatRoom-AcceptLoop")
        self._accept_thread.start()

    def _accept_loop(self):
        """Bucle para aceptar conexiones de agentes."""
        while self._is_running:
            try:
                client_sock, client_addr = self._server_sock.accept()
                logger.info("Nueva conexión entrante desde %s", client_addr)

                conn = RobustSocketConnection(client_sock, client_addr)

                with self._lock:
                    self._current_client = conn

                # Iniciar hilo de lectura para este cliente
                client_thread = threading.Thread(
                    target=self._client_read_loop,
                    args=(conn,),
                    daemon=True,
                    name=f"ChatRoom-ClientLoop-{client_addr[1]}"
                )
                client_thread.start()

            except (socket.error, OSError):
                if not self._is_running:
                    break

    def _client_read_loop(self, conn: RobustSocketConnection):
        """Maneja el flujo de mensajes recibidos de un cliente conectado."""
        try:
            while self._is_running and not conn.is_closed:
                msg = conn.receive_message()
                if msg is None:
                    break

                self._process_incoming_message(conn, msg)
        except Exception as e:
            logger.error("Error en bucle de lectura de cliente (%s): %s", conn.address, e)
        finally:
            with self._lock:
                if conn in self._connected_clients:
                    del self._connected_clients[conn]
                if self._current_client == conn:
                    # Si quedan otros clientes, asignar el último activo
                    if self._connected_clients:
                        self._current_client = list(self._connected_clients.keys())[-1]
                        self._current_agent_info = self._connected_clients[self._current_client]
                    else:
                        self._current_client = None
                        self._current_agent_info = {}
                        self._current_agent_state = None

            conn.close()
            logger.info("Cliente desconectado (%s).", conn.address)
            self._broadcast_agent_list()
            if self.on_agent_disconnected:
                try:
                    self.on_agent_disconnected()
                except Exception as e:
                    logger.error("Error en callback on_agent_disconnected: %s", e)

    def _process_incoming_message(self, conn: RobustSocketConnection, msg: NetworkMessage):
        """Procesa un mensaje recibido del agente."""
        if msg.type == MessageType.HANDSHAKE:
            info = msg.payload
            with self._lock:
                self._current_agent_info = info
                self._current_client = conn
                self._connected_clients[conn] = info
            logger.info("Handshake recibido del agente: %s", info)
            # Responder confirmación de handshake
            ack = make_handshake_ack()
            conn.send_message(ack)
            self._broadcast_agent_list()

            if self.on_agent_connected:
                try:
                    self.on_agent_connected(info)
                except Exception as e:
                    logger.error("Error en callback on_agent_connected: %s", e)

        elif msg.type == MessageType.AGENT_RESPONSE:
            logger.info("Respuesta final del agente recibida (%d caracteres).", len(msg.payload.get("text", "")))
            if self.on_agent_response:
                try:
                    self.on_agent_response(msg.payload)
                except Exception as e:
                    logger.error("Error en callback on_agent_response: %s", e)

        elif msg.type == MessageType.AGENT_STATUS:
            state = msg.payload.get("state") or msg.payload.get("status")
            if state:
                with self._lock:
                    self._current_agent_state = str(state)
            if self.on_agent_status:
                try:
                    self.on_agent_status(msg.payload)
                except Exception as e:
                    logger.error("Error en callback on_agent_status: %s", e)

        elif msg.type == MessageType.PING:
            conn.send_message(make_pong())

    def _broadcast_agent_list(self):
        """Difunde la lista de agentes conectados a todos los clientes."""
        with self._lock:
            agents = list(self._connected_clients.values())
            clients = list(self._connected_clients.keys())
        msg = make_agent_list(agents)
        for c in clients:
            try:
                c.send_message(msg)
            except Exception:
                pass

    def send_user_message(self, text: str) -> bool:
        """Envía un mensaje redactado por el usuario humano al agente de IA conectado."""
        with self._lock:
            client = self._current_client

        if not client or client.is_closed:
            logger.warning("Intento de envío de mensaje sin ningún agente conectado.")
            return False

        msg = make_chat_message(text=text, sender=HUMAN_SENDER)
        return client.send_message(msg)

    @property
    def is_agent_connected(self) -> bool:
        with self._lock:
            return self._current_client is not None and not self._current_client.is_closed

    @property
    def current_agent_info(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._current_agent_info)

    @property
    def current_agent_state(self) -> Optional[str]:
        with self._lock:
            return self._current_agent_state

    def stop(self):
        """Detiene el servidor y finaliza las conexiones."""
        self._is_running = False
        with self._lock:
            if self._current_client:
                self._current_client.close()
                self._current_client = None

        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
            self._server_sock = None
        logger.info("Servidor de Sala de Chat detenido.")

