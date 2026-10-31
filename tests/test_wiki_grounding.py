"""
Tests unitarios para la funcionalidad de Wiki-Grounding, desconfianza de memoria
paramétrica y exploración guiada de enlaces en la memoria conceptual.
"""
import unittest
from wiki_agent.agent.loop import SYSTEM_PROMPT
from wiki_agent.agent.parser import AgentResponseParser
from wiki_agent.agent.commands import CommandDispatcher
import generate_ft6_wiki_grounding_dataset


class TestWikiGrounding(unittest.TestCase):

    def test_system_prompt_includes_grounding_directives(self):
        """Verifica que el SYSTEM_PROMPT del agente incorpore formalmente las directivas de wiki-grounding."""
        self.assertIn("WIKI-GROUNDING", SYSTEM_PROMPT)
        self.assertIn("DESCONFIANZA DE MEMORIA PARAMÉTRICA", SYSTEM_PROMPT)
        self.assertIn("PERSISTENCIA PROACTIVA (CONTEXT OFFLOADING)", SYSTEM_PROMPT)
        self.assertIn("/read", SYSTEM_PROMPT)
        self.assertIn("/search", SYSTEM_PROMPT)

    def test_ft6_dataset_structure_and_balance(self):
        """Verifica que el generador FT6 produzca 100 ejemplos válidos con 4 bloques y balance multi-fuente."""
        examples = generate_ft6_wiki_grounding_dataset.create_examples()
        self.assertEqual(len(examples), 100)

        # Verificar unicidad
        human_inputs = [e["conversations"][1]["value"] for e in examples]
        self.assertEqual(len(set(human_inputs)), 100, "Todos los inputs deben ser únicos")

        # Verificar presencia de etiquetas obligatorias en gpt
        for ex in examples:
            gpt_val = ex["conversations"][2]["value"]
            self.assertIn("<thought>", gpt_val)
            self.assertIn("</thought>", gpt_val)
            self.assertIn("<response>", gpt_val)
            self.assertIn("</response>", gpt_val)
            self.assertIn("<commands>", gpt_val)
            self.assertIn("</commands>", gpt_val)

        # Verificar ratio multi-fuente: 20 agentes, 80 humanos
        agent_senders = sum(1 for h in human_inputs if "[DE:" in h)
        self.assertEqual(agent_senders, 20)

    def test_read_command_grounding_dispatch(self):
        """Verifica que el comando /read pueda ser despachado por CommandDispatcher para navegación en grafo."""
        class MockAssistant:
            def get_concept_full_context(self, title):
                return f"<concept name='{title}'><definition>Mock definition</definition></concept>"

        class MockAgent:
            def __init__(self):
                self.assistant = MockAssistant()

        agent = MockAgent()
        dispatcher = CommandDispatcher(agent)
        res = dispatcher.dispatch('/read "API Gateway"')
        self.assertIn("<concept name='API Gateway'>", res)

    def test_parser_extracts_grounding_commands(self):
        """Verifica que el parser extraiga correctamente comandos /search y /read para grounding."""
        parser = AgentResponseParser()
        raw = """<thought>
1. No debo usar memoria interna no verificada.
2. Compruebo en la wiki mediante /read.
</thought>
<commands>
/read "Istio Service Mesh"
</commands>"""
        thought, response, commands = parser.extract_components(raw)
        self.assertIn("No debo usar memoria interna", thought)
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0], '/read "Istio Service Mesh"')


if __name__ == "__main__":
    unittest.main()
