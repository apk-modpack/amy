import unittest
import tempfile
import json
from pathlib import Path
from wiki_agent.agent.identity import AgentIdentityManager, RESERVED_NAMES, generate_random_agent_name
from wiki_agent.agent.commands import IdentifyCommand
from wiki_agent.network.protocol import (
    NetworkMessage,
    MessageType,
    HUMAN_SENDER,
    make_agent_list,
    make_handshake,
    make_chat_message,
)


class DummyAgent:
    def __init__(self, identity_mgr):
        self.identity_manager = identity_mgr

    def get_or_create_identity(self):
        return self.identity_manager.load_or_create()


class TestAgentIdentityAndMultiagentProtocol(unittest.TestCase):
    def test_random_name_generation_not_reserved(self):
        for _ in range(50):
            name = generate_random_agent_name()
            self.assertNotIn(name.upper(), RESERVED_NAMES)
            self.assertTrue(len(name) > 3)

    def test_identity_persistence_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_identity.json"
            mgr1 = AgentIdentityManager(file_path=file_path)
            id1 = mgr1.agent_id
            name1 = mgr1.agent_name

            self.assertTrue(file_path.exists())
            self.assertTrue(bool(id1))
            self.assertTrue(bool(name1))

            # Recargar con otra instancia: debe mantener la misma identidad
            mgr2 = AgentIdentityManager(file_path=file_path)
            self.assertEqual(mgr2.agent_id, id1)
            self.assertEqual(mgr2.agent_name, name1)

    def test_reserved_name_human_is_sanitized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_identity.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"agent_id": "test-id", "agent_name": "HUMAN"}, f)

            mgr = AgentIdentityManager(file_path=file_path)
            self.assertNotEqual(mgr.agent_name.upper(), "HUMAN")
            self.assertNotIn(mgr.agent_name.upper(), RESERVED_NAMES)

    def test_identify_command_execution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_identity.json"
            mgr = AgentIdentityManager(file_path=file_path)
            agent = DummyAgent(mgr)
            cmd = IdentifyCommand(agent)
            res = cmd.execute("")
            self.assertIn(mgr.agent_name, res)
            self.assertIn(mgr.agent_id, res)
            self.assertIn("Identificación del Agente", res)

    def test_agent_list_protocol_serialization(self):
        agents = [
            {"client_name": "Atlas-Pilot-01", "model_name": "Llama 3.2", "client_id": "id-1"},
            {"client_name": "Nova-Core-02", "model_name": "Llama 3.2", "client_id": "id-2"},
        ]
        msg = make_agent_list(agents)
        line = msg.to_json_line().decode("utf-8")
        parsed = NetworkMessage.from_json_line(line)
        self.assertEqual(parsed.type, MessageType.AGENT_LIST)
        self.assertEqual(len(parsed.payload["agents"]), 2)
        self.assertEqual(parsed.payload["agents"][0]["client_name"], "Atlas-Pilot-01")

    def test_default_chat_message_sender_is_human(self):
        msg = make_chat_message("Hola mundo")
        self.assertEqual(msg.payload["sender"], HUMAN_SENDER)
        self.assertEqual(msg.payload["sender"], "HUMAN")


if __name__ == "__main__":
    unittest.main()

