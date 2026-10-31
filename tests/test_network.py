import unittest
import socket
import time
import threading
from wiki_agent.network.protocol import (
    NetworkMessage,
    MessageType,
    AgentState,
    make_handshake,
    make_handshake_ack,
    make_chat_message,
    make_agent_response,
    make_agent_status,
)
from wiki_agent.network.connection import RobustSocketConnection
from wiki_agent.network.server import ChatRoomServer
from wiki_agent.network.client import AgentNetworkClient


class TestNetworkProtocol(unittest.TestCase):
    def test_protocol_serialization_deserialization(self):
        msg = make_chat_message("Hola Agente", sender="user")
        line_bytes = msg.to_json_line()
        self.assertTrue(line_bytes.endswith(b"\n"))

        deserialized = NetworkMessage.from_json_line(line_bytes.decode("utf-8"))
        self.assertEqual(deserialized.type, MessageType.CHAT_MESSAGE)
        self.assertEqual(deserialized.payload["text"], "Hola Agente")
        self.assertEqual(deserialized.payload["sender"], "user")

    def test_agent_response_metadata(self):
        meta = {"tok_s": 42.5, "concepts": ["Scrum"]}
        msg = make_agent_response("Respuesta de prueba", metadata=meta)
        line = msg.to_json_line().decode("utf-8")
        parsed = NetworkMessage.from_json_line(line)
        self.assertEqual(parsed.type, MessageType.AGENT_RESPONSE)
        self.assertEqual(parsed.payload["text"], "Respuesta de prueba")
        self.assertEqual(parsed.payload["metadata"]["tok_s"], 42.5)

    def test_connection_packet_fragmentation(self):
        """Prueba que el buffer de RobustSocketConnection maneja mensajes partidos o pegados."""
        # Crear par de sockets conectados
        s1, s2 = socket.socketpair()
        try:
            conn1 = RobustSocketConnection(s1)
            conn2 = RobustSocketConnection(s2)

            msg1 = make_chat_message("Mensaje Uno")
            msg2 = make_chat_message("Mensaje Dos")

            # Enviar los dos mensajes juntos en un único send (packet sticking)
            chunk = msg1.to_json_line() + msg2.to_json_line()
            s1.sendall(chunk)

            # Leer del otro extremo: debe devolverlos uno por uno
            r1 = conn2.receive_message(timeout=1.0)
            self.assertIsNotNone(r1)
            self.assertEqual(r1.payload["text"], "Mensaje Uno")

            r2 = conn2.receive_message(timeout=1.0)
            self.assertIsNotNone(r2)
            self.assertEqual(r2.payload["text"], "Mensaje Dos")
        finally:
            s1.close()
            s2.close()


class TestServerClientInteraction(unittest.TestCase):
    def test_agent_state_protocol(self):
        """Verifica la serialización y deserialización de los estados formales del agente."""
        for state in [AgentState.LISTO, AgentState.PROCESANDO, AgentState.ERROR]:
            msg = make_agent_status(state=state, detail=f"Estado {state.value}")
            line = msg.to_json_line().decode("utf-8")
            parsed = NetworkMessage.from_json_line(line)
            self.assertEqual(parsed.type, MessageType.AGENT_STATUS)
            self.assertEqual(parsed.payload["state"], state.value)
            self.assertEqual(parsed.payload["detail"], f"Estado {state.value}")

    def test_server_client_state_propagation(self):
        """Verifica que el estado formal del cliente se propague y actualice en el servidor."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]

        received_statuses = []
        server = ChatRoomServer(
            host="127.0.0.1",
            port=port,
            on_agent_status=lambda st: received_statuses.append(st),
        )
        server.start()

        try:
            client = AgentNetworkClient(host="127.0.0.1", port=port, model_name="Test-Model", timeout=3.0)
            client.connect()
            time.sleep(0.1)

            # Enviar estado LISTO
            client.send_state(AgentState.LISTO, "Esperando input")
            time.sleep(0.1)
            self.assertEqual(server.current_agent_state, AgentState.LISTO.value)

            # Enviar estado PROCESANDO
            client.send_state(AgentState.PROCESANDO, "Pensando")
            time.sleep(0.1)
            self.assertEqual(server.current_agent_state, AgentState.PROCESANDO.value)

            # Enviar estado ERROR
            client.send_state(AgentState.ERROR, "Fallo simulado")
            time.sleep(0.1)
            self.assertEqual(server.current_agent_state, AgentState.ERROR.value)

            self.assertEqual(len(received_statuses), 3)

            client.disconnect()
            time.sleep(0.1)
            self.assertIsNone(server.current_agent_state)
        finally:
            server.stop()

    def test_server_client_handshake_and_chat(self):
        # Encontrar puerto libre
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]

        received_responses = []
        agent_connected_events = []

        server = ChatRoomServer(
            host="127.0.0.1",
            port=port,
            on_agent_connected=lambda info: agent_connected_events.append(info),
            on_agent_response=lambda resp: received_responses.append(resp),
        )
        server.start()

        try:
            client = AgentNetworkClient(
                host="127.0.0.1",
                port=port,
                model_name="Llama-3.2-Test",
                timeout=3.0,
            )
            connected = client.connect()
            self.assertTrue(connected)
            time.sleep(0.1)

            self.assertEqual(len(agent_connected_events), 1)
            self.assertEqual(agent_connected_events[0]["model_name"], "Llama-3.2-Test")
            self.assertTrue(server.is_agent_connected)

            # El servidor envía mensaje de usuario al cliente
            sent = server.send_user_message("¿Qué es la wiki?")
            self.assertTrue(sent)

            # El cliente puede recibir primero AGENT_LIST del broadcast inicial y luego CHAT_MESSAGE
            incoming = client.receive_message(timeout=2.0)
            if incoming and incoming.type == MessageType.AGENT_LIST:
                incoming = client.receive_message(timeout=2.0)

            self.assertIsNotNone(incoming)
            self.assertEqual(incoming.type, MessageType.CHAT_MESSAGE)
            self.assertEqual(incoming.payload["text"], "¿Qué es la wiki?")

            # El cliente responde
            client.send_response("La wiki es la memoria a largo plazo.", metadata={"latency": 0.5})
            time.sleep(0.1)

            self.assertEqual(len(received_responses), 1)
            self.assertEqual(received_responses[0]["text"], "La wiki es la memoria a largo plazo.")
            self.assertEqual(received_responses[0]["metadata"]["latency"], 0.5)

            # Desconectar
            client.disconnect()
            time.sleep(0.1)
            self.assertFalse(server.is_agent_connected)

        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()

