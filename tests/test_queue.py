import tempfile
import shutil
from pathlib import Path
from wiki_agent.backends.local_markdown import LocalMarkdownBackend
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.tools.queue import IngestionQueueManager


def test_queue_lifecycle_and_batch_processing():
    temp_dir = tempfile.mkdtemp()
    try:
        backend = LocalMarkdownBackend(base_path=temp_dir)
        mgr = WikiKnowledgeManager()
        mgr.backend = backend

        queue_file = Path(temp_dir) / "test_queue.json"
        q_mgr = IngestionQueueManager(mgr, queue_path=str(queue_file))

        # 1. AÃ±adir elementos a la cola (usando tipo texto para no depender de red externa en el test)
        q_mgr.add_item(
            title="TermodinÃ¡mica",
            source="La termodinÃ¡mica estudia la transferencia de calor.",
            source_type="text",
            category="FÃ­sica"
        )
        q_mgr.add_item(
            title="Electromagnetismo",
            source="El electromagnetismo describe las fuerzas elÃ©ctricas y magnÃ©ticas.",
            source_type="text",
            category="FÃ­sica"
        )

        status1 = q_mgr.get_status()
        assert status1["total"] == 2
        assert status1["pending"] == 2

        # 2. Procesar solo 1 elemento
        res1 = q_mgr.process_queue(count=1, delay_seconds=0.0)
        assert res1["processed"] == 1
        assert res1["remaining"] == 1

        # Verificar que la primera pÃ¡gina fue creada en la Wiki
        p1 = backend.read_page("TermodinÃ¡mica")
        assert p1 is not None
        assert p1.metadata.category == "FÃ­sica"

        # 3. Procesar el restante hasta vaciar
        res2 = q_mgr.process_queue(until_empty=True, delay_seconds=0.0)
        assert res2["processed"] == 1
        assert res2["remaining"] == 0
        assert res2["completed_all"] is True

        p2 = backend.read_page("Electromagnetismo")
        assert p2 is not None
    finally:
        shutil.rmtree(temp_dir)