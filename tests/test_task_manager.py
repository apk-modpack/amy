import unittest
from wiki_agent.agent.task_list import AgentTaskManager, TaskItem
from wiki_agent.agent.parser import AgentResponseParser
from wiki_agent.agent.commands import CommandDispatcher, TaskAddCommand, TaskDoneCommand, TaskListCommand


class DummyAgent:
    def __init__(self):
        self.task_manager = AgentTaskManager()


class TestTaskManagerAndCommands(unittest.TestCase):

    def test_task_item_toggle(self):
        item = TaskItem("Buscar concepto A", completed=False)
        self.assertFalse(item.completed)
        item.mark_completed()
        self.assertTrue(item.completed)

    def test_task_manager_lifecycle(self):
        tm = AgentTaskManager()
        self.assertFalse(tm.has_pending_tasks)
        self.assertEqual(tm.total_count, 0)

        tm.set_tasks(["Paso 1: Analizar", "Paso 2: Sintetizar"])
        self.assertEqual(tm.total_count, 2)
        self.assertEqual(tm.pending_count, 2)
        self.assertTrue(tm.has_pending_tasks)

        # Completar primera tarea (1-based index)
        ok = tm.complete_task(1)
        self.assertTrue(ok)
        self.assertEqual(tm.pending_count, 1)

        # Completar siguiente por complete_next
        t = tm.complete_next()
        self.assertIsNotNone(t)
        self.assertEqual(tm.pending_count, 0)
        self.assertFalse(tm.has_pending_tasks)

    def test_parser_tasks_block_extraction(self):
        parser = AgentResponseParser()
        raw = """<thought>
Planeando tareas...
</thought>
<tasks>
- [ ] 1. Buscar en la wiki sobre Arquitectura Hexagonal
- [ ] 2. Contrastar con Arquitectura Limpia
- [x] 3. Tarea previa hecha
</tasks>
<response>
Iniciando análisis.
</response>"""
        tasks = parser.extract_tasks_block(raw)
        self.assertEqual(len(tasks), 3)
        self.assertIn("1. Buscar en la wiki sobre Arquitectura Hexagonal", tasks[0])
        self.assertIn("2. Contrastar con Arquitectura Limpia", tasks[1])
        self.assertIn("3. Tarea previa hecha", tasks[2])

    def test_task_commands_dispatch(self):
        agent = DummyAgent()
        dispatcher = CommandDispatcher(agent)

        res_add = dispatcher.dispatch('/task_add "Paso 1: Validar datos"')
        self.assertIn("Tarea añadida", res_add)
        self.assertEqual(agent.task_manager.total_count, 1)

        res_list = dispatcher.dispatch("/task_list")
        self.assertIn("Paso 1: Validar datos", res_list)
        self.assertIn("[ ]", res_list)

        res_done = dispatcher.dispatch('/task_done "1"')
        self.assertIn("marcada como completada", res_done)
        self.assertEqual(agent.task_manager.pending_count, 0)


if __name__ == "__main__":
    unittest.main()
