import tempfile
import shutil
from pathlib import Path
from wiki_agent.backends.local_markdown import LocalMarkdownBackend
from wiki_agent.models import WikiPage, PageMetadata
from wiki_agent.core.health import WikiHealthChecker
from wiki_agent.core.indexer import WikiIndexer


def test_health_check_detects_stubs_and_orphans():
    temp_dir = tempfile.mkdtemp()
    try:
        backend = LocalMarkdownBackend(base_path=temp_dir)
        
        # Pagina que enlaza a un concepto inexistente 'Algoritmo Genetico'
        meta = PageMetadata(title="Computacion Evolutiva", category="IA")
        page = WikiPage(metadata=meta, content="Basado en [[Algoritmo Genetico]].")
        backend.write_page(page)

        checker = WikiHealthChecker(backend)
        report = checker.run_diagnostics()

        assert report.total_pages == 1
        assert "Computacion Evolutiva" in report.orphan_pages
        assert len(report.missing_stubs) == 1
        assert report.missing_stubs[0]["missing_concept"] == "Algoritmo Genetico"
    finally:
        shutil.rmtree(temp_dir)


def test_indexer_generates_mocs():
    temp_dir = tempfile.mkdtemp()
    try:
        backend = LocalMarkdownBackend(base_path=temp_dir)
        
        meta = PageMetadata(title="Backpropagation", category="IA", tags=["optimizacion"])
        page = WikiPage(metadata=meta, content="Algoritmo de entrenamiento.")
        backend.write_page(page)

        indexer = WikiIndexer(backend)
        cat_index = indexer.generate_category_index("IA")
        assert cat_index.title == "Índice_IA"
        assert "[[Backpropagation]]" in cat_index.content

        master_index = indexer.generate_global_index()
        assert master_index.title == "Índice_Maestro"
        assert "Índice_IA" in master_index.content
    finally:
        shutil.rmtree(temp_dir)
