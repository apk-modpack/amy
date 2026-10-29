import unittest
from unittest.mock import MagicMock
from wiki_agent.agent.loop import WikiAgent


class TestLoopSaveValidation(unittest.TestCase):
    def setUp(self):
        self.mock_mgr = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_llm.model_name = "test-model"
        self.agent = WikiAgent(manager=self.mock_mgr, llm=self.mock_llm)

    def test_reject_announcement_phrase(self):
        """Verifica que frases de anuncio tipo 'Voy a...' sean rechazadas y no guarden el concepto."""
        announcements = [
            "Voy a reorganizar la estructura de [[Scrum]] para reflejar la relación.",
            "Voy a crear el concepto [[Artifacts Scrum]] para definir sus elementos.",
            "Voy a corregir y completar el concepto [[Gestión de Proyectos]].",
            "Procedo a estructurar los conceptos principales de Scrum.",
            "Crearé el concepto de desarrollo ágil.",
            "Actualizaré la wiki con los nuevos roles.",
        ]
        for phrase in announcements:
            self.agent._last_response = phrase
            res = self.agent.save_last_response("TestConcept")
            self.assertTrue(res.startswith("Error:"), f"Se esperaba error para: {phrase}, pero se obtuvo: {res}")
            self.mock_mgr.save_concept.assert_not_called()

    def test_accept_valid_definition_xml(self):
        """Verifica que un contenido con <definition> se extraiga y guarde correctamente."""
        self.agent._last_response = """
        <definition>
        Scrum es un marco de trabajo ágil e iterativo para la gestión de proyectos complejos.
        </definition>
        <sections>
          <section name="Roles">Product Owner, Scrum Master, Equipo de Desarrollo.</section>
        </sections>
        <relations>
          <relation type="is_a" target="Metodología Ágil">Es una metodología ágil.</relation>
        </relations>
        """
        res = self.agent.save_last_response("Scrum")
        self.assertTrue(res.startswith("✓"), f"Se esperaba éxito, se obtuvo: {res}")
        self.mock_mgr.save_concept.assert_called_once()
        args, kwargs = self.mock_mgr.save_concept.call_args
        self.assertEqual(kwargs["title"], "Scrum")
        self.assertIn("marco de trabajo ágil", kwargs["content"])
        self.assertIn("Roles", kwargs["sections"])
        self.assertEqual(len(kwargs["relations"]), 1)
        self.assertEqual(kwargs["relations"][0].target, "Metodología Ágil")

    def test_reject_too_short(self):
        """Verifica que textos demasiado cortos (< 35 chars) sin <definition> sean rechazados."""
        self.agent._last_response = "Scrum es genial."
        res = self.agent.save_last_response("Scrum")
        self.assertTrue(res.startswith("Error:"))
        self.mock_mgr.save_concept.assert_not_called()

    def test_execute_command_error_propagation(self):
        """Verifica que _execute_command no anteponga 'Éxito:' si ocurrió un error."""
        self.agent._last_response = "Voy a crear el concepto de Scrum."
        res = self.agent._execute_command('/save "Scrum"')
        self.assertFalse(res.startswith("Éxito:"))
        self.assertTrue(res.startswith("Error:"))

    def test_edit_only_relations_preserves_definition(self):
        """Verifica que al enviar solo <relations>, se preserve la definición existente."""
        mock_existing = MagicMock()
        mock_existing.content = "Definición previa de Scrum que debe mantenerse intacta."
        self.mock_mgr.get_concept.return_value = mock_existing

        self.agent._last_response = """
        <relations>
          <relation type="relates_to" target="Kanban">Ambos son marcos ágiles.</relation>
        </relations>
        """
        res = self.agent._execute_command('/edit "Scrum"')
        self.assertTrue(res.startswith("Éxito: ✓"))
        self.mock_mgr.save_concept.assert_called_once()
        _, kwargs = self.mock_mgr.save_concept.call_args
        self.assertEqual(kwargs["content"], "Definición previa de Scrum que debe mantenerse intacta.")
        self.assertEqual(len(kwargs["relations"]), 1)
        self.assertEqual(kwargs["relations"][0].target, "Kanban")

    def test_edit_only_definition(self):
        """Verifica que al enviar solo <definition>, se actualice la definición."""
        self.agent._last_response = """
        <definition>
        Nueva definición actualizada de Scrum con más detalle técnico.
        </definition>
        """
        res = self.agent._execute_command('/edit "Scrum"')
        self.assertTrue(res.startswith("Éxito: ✓"))
        self.mock_mgr.save_concept.assert_called_once()
        _, kwargs = self.mock_mgr.save_concept.call_args
        self.assertIn("Nueva definición actualizada", kwargs["content"])
        self.assertIsNone(kwargs["relations"])

    def test_edit_both_definition_and_relations(self):
        """Verifica que al enviar <definition> y <relations> a la vez, se actualicen ambos."""
        self.agent._last_response = """
        <definition>
        Definición completa renovada de Scrum.
        </definition>
        <relations>
          <relation type="is_a" target="Metodología Ágil"/>
          <relation type="relates_to" target="Kanban"/>
        </relations>
        """
        res = self.agent._execute_command('/edit "Scrum"')
        self.assertTrue(res.startswith("Éxito: ✓"))
        self.mock_mgr.save_concept.assert_called_once()
        _, kwargs = self.mock_mgr.save_concept.call_args
        self.assertEqual(kwargs["content"], "Definición completa renovada de Scrum.")
        self.assertEqual(len(kwargs["relations"]), 2)

    def test_edit_with_announcement_rejected(self):
        """Verifica que /edit rechace anuncios transitorios como 'Voy a reorganizar...'."""
        self.agent._last_response = "Voy a reorganizar la estructura de [[Scrum]] para reflejar relaciones."
        res = self.agent._execute_command('/edit "Scrum"')
        self.assertTrue(res.startswith("Error:"))
        self.mock_mgr.save_concept.assert_not_called()


if __name__ == "__main__":
    unittest.main()
