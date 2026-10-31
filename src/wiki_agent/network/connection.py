"""Manejador de conexión de socket robusto con búfer de líneas.

Resuelve la fragmentación de tramas TCP (TCP stream sticking/splitting)
asegurando que los mensajes delimitados por '\\n' se extraigan de forma
atómica e íntegra.
"""

import socket
import threading
import logging
from typing import Optional
from wiki_agent.network.protocol import NetworkMessage

logger = logging.getLogger(__name__)


class RobustSocketConnection:
    """Envuelve un socket TCP proporcionando lectura y escritura atómica de NetworkMessages."""

    def __init__(self, sock: socket.socket, address: Optional[tuple] = None):
        self.sock = sock
        self.address = address
        self._send_lock = threading.Lock()
        self._recv_buffer = ""
        self._is_closed = False

    def send_message(self, message: NetworkMessage) -> bool:
        """Serializa y envía un mensaje por el socket de forma atómica y segura entre hilos."""
        if self._is_closed:
            return False

        data = message.to_json_line()
        try:
            with self._send_lock:
                self.sock.sendall(data)
            return True
        except (socket.error, OSError) as e:
            logger.warning("Fallo al enviar mensaje al socket (%s): %s", self.address, e)
            self.close()
            return False

    def receive_message(self, timeout: Optional[float] = None) -> Optional[NetworkMessage]:
        """Lee del socket hasta obtener una línea completa '\\n' y la deserializa como NetworkMessage.
        
        Retorna:
            NetworkMessage si se leyó un mensaje válido.
            None si la conexión fue cerrada por el extremo o si ocurrió un error fatal.
        
        Lanza:
            socket.timeout si transcurrió el timeout especificado sin recibir datos.
        """
        if self._is_closed:
            return None

        # Si ya tenemos al menos una línea completa en el búfer acumulado
        if "\n" in self._recv_buffer:
            line, self._recv_buffer = self._recv_buffer.split("\n", 1)
            line = line.strip()
            if line:
                try:
                    return NetworkMessage.from_json_line(line)
                except Exception as e:
                    logger.error("Error al deserializar mensaje desde búfer: %s", e)

        # Configurar timeout si se solicitó
        original_timeout = self.sock.gettimeout()
        if timeout is not None:
            self.sock.settimeout(timeout)

        try:
            while not self._is_closed:
                chunk = self.sock.recv(4096)
                if not chunk:
                    # Conexión cerrada limpiamente por el otro extremo
                    logger.info("El socket remoto (%s) cerró la conexión.", self.address)
                    self.close()
                    return None

                self._recv_buffer += chunk.decode("utf-8", errors="replace")

                if "\n" in self._recv_buffer:
                    line, self._recv_buffer = self._recv_buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        try:
                            return NetworkMessage.from_json_line(line)
                        except Exception as e:
                            logger.error("Error al deserializar mensaje de red: %s | Línea: %r", e, line)
                            continue
        except socket.timeout:
            raise
        except (socket.error, OSError) as e:
            if not self._is_closed:
                logger.warning("Error de lectura en socket (%s): %s", self.address, e)
                self.close()
            return None
        finally:
            if timeout is not None and not self._is_closed:
                try:
                    self.sock.settimeout(original_timeout)
                except Exception:
                    pass

        return None

    def close(self):
        """Cierra el socket de forma ordenada."""
        if self._is_closed:
            return
        self._is_closed = True
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass
        logger.debug("Socket cerrado correctamente (%s).", self.address)

    @property
    def is_closed(self) -> bool:
        return self._is_closed

