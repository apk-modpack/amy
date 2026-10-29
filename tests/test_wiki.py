import tempfile
import shutil
from pathlib import Path
from wiki_agent.backends.local_markdown import LocalMarkdownBackend
from wiki_agent.models import WikiPage, PageMetadata
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.tools.dataset_exporter import DatasetExporter


def test_local_markdown_backend_crud():
    temp_dir = tempfile.mkdtemp()
    try:
        backend = LocalMarkdownBackend(base_path=temp_dir)
        
        # 1. Crear concepto
        meta = PageMetadata(title="Redes Neuronales", category="IA", tags=["deep-learning"])
        page = WikiPage(metadata=meta, content="Las [[Redes Neuronales]] son la base del [[Aprendizaje Profundo]].")
        backend.write_page(page)

        # 2. Leer concepto
        loaded = backend.read_page("Redes Neuronales")
        assert loaded is not None
        assert loaded.title == "Redes Neuronales"
        assert loaded.metadata.category == "IA"
        assert "Aprendizaje Profundo" in loaded.outgoing_links

        # 3. Crear segundo concepto que enlace al primero
        meta2 = PageMetadata(title="Aprendizaje Profundo", category="IA")
        page2 = WikiPage(metadata=meta2, content="EvoluciÃ³n de las [[Redes Neuronales]].")
        backend.write_page(page2)

        # 4. Verificar backlinks
        backlinks = backend.get_backlinks("Redes Neuronales")
        assert "Aprendizaje Profundo" in backlinks

        # 5. BÃºsqueda
        results = backend.search("Aprendizaje")
        assert len(results) >= 1
    finally:
        shutil.rmtree(temp_dir)


def test_dataset_export():
    temp_dir = tempfile.mkdtemp()
    try:
        backend = LocalMarkdownBackend(base_path=temp_dir)
        meta = PageMetadata(title="Concepto Test", category="Pruebas")
        page = WikiPage(metadata=meta, content="Contenido explicativo de prueba.")
        backend.write_page(page)

        mgr = WikiKnowledgeManager()
        mgr.backend = backend
        mgr.config["export"]["output_dir"] = temp_dir

        exporter = DatasetExporter(mgr)
        out_file = exporter.export_to_jsonl(format_type="sharegpt")
        assert Path(out_file).exists()
        content = Path(out_file).read_text(encoding="utf-8")
        assert "Concepto Test" in content
    finally:
        shutil.rmtree(temp_dir)