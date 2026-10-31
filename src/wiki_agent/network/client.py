"""Cliente de socket para el Agente IA (Programa Cliente).

Conecta el Agente IA con la Sala de Chat remota, gestiona el handshake inicial,
recibe las peticiones de usuario y transmite las respuestas y estados generados.
"""

import socket
import logging
from typing import Optional, Dict, Any
from wiki_agent.network.protocol import (
    NetworkMessage,
    MessageType,
    AgentState,
    make_handshake,
    make_agent_response,
    make_agent_status,
)
from wiki_agent.network.connection import RobustSocketConnection

logger = logging.getLogger(__name__)


class AgentNetworkClient:
    """Cliente de red para el Agente IA que interactúa con la Sala de Chat."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        model_name: str = "Llama 3.2",
        client_name: Optional[str] = None,
        client_id: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.model_name = model_name
        self.client_name = client_name or "Wiki-Memory Agent"
        self.client_id = client_id or ""
        self.timeout = timeout
        self._conn: Optional[RobustSocketConnection] = None
        self._server_info: Dict[str, Any] = {}
        self.connected_agents: list = []

    def connect(self) -> bool:
        """Establece conexión TCP con la Sala de Chat y completa el handshake."""
        try:
            logger.info("Conectando con la Sala de Chat en %s:%d...", self.host, self.port)
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_sock.settimeout(self.timeout)
            raw_sock.connect((self.host, self.port))
            # Quitar timeout de conexión para usar el modo de streaming o timeouts específicos
            raw_sock.settimeout(None)

            self._conn = RobustSocketConnection(raw_sock, (self.host, self.port))

            # Enviar mensaje de Handshake inicial
            handshake = make_handshake(
                client_name=self.client_name,
                model_name=self.model_name,
                client_id=self.client_id,
            )
            if not self._conn.send_message(handshake):
                raise ConnectionError("Fallo al enviar mensaje de Handshake.")

            # Esperar confirmación de Handshake
            ack = self._conn.receive_message(timeout=5.0)
            if not ack or ack.type != MessageType.HANDSHAKE_ACK:
                raise ConnectionError(f"Handshake no confirmado por el servidor. Recibido: {ack}")

            self._server_info = ack.payload
            logger.info("Conexión y Handshake establecidos exitosamente con la Sala de Chat.")
            return True

        except Exception as e:
            logger.error("Error al conectar con la Sala de Chat (%s:%d): %s", self.host, self.port, e)
            if self._conn:
                self._conn.close()
                self._conn = None
            raise

    def receive_message(self, timeout: Optional[float] = None) -> Optional[NetworkMessage]:
        """Espera y retorna el siguiente mensaje proveniente de la Sala de Chat."""
        if not self._conn or self._conn.is_closed:
            return None
        return self._conn.receive_message(timeout=timeout)

    def send_response(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Transmite la respuesta final generada por la IA hacia la Sala de Chat."""
        if not self._conn or self._conn.is_closed:
            return False
        msg = make_agent_response(text=text, metadata=metadata)
        return self._conn.send_message(msg)

    def send_status(self, status: str, detail: str = "") -> bool:
        """Transmite una actualización de estado de la IA a la Sala de Chat."""
        if not self._conn or self._conn.is_closed:
            return False
        msg = make_agent_status(state=status, detail=detail)
        return self._conn.send_message(msg)

    def send_state(self, state: AgentState, detail: str = "") -> bool:
        """Transmite el estado formal del agente (LISTO / PROCESANDO / ERROR) a la Sala de Chat.

        Usar este método en lugar de send_status cuando se quiere comunicar uno de los
        tres estados canónicos que la Sala de Chat puede mostrar en su indicador de estado.

        Args:
            state: Estado del agente (AgentState enum).
            detail: Contexto adicional opcional mostrado como subtítulo.
        """
        if not self._conn or self._conn.is_closed:
            return False
        msg = make_agent_status(state=state, detail=detail)
        return self._conn.send_message(msg)

    def disconnect(self):
        """Cierra la conexión con la Sala de Chat."""
        if self._conn:
            self._conn.close()
            self._conn = None
        logger.info("Desconectado de la Sala de Chat.")

    @property
    def is_connected(self) -> bool:
        return self._conn is not None and not self._conn.is_closed

