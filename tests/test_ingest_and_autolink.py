import tempfile
import shutil
from pathlib import Path
from wiki_agent.backends.local_markdown import LocalMarkdownBackend
from wiki_agent.models import WikiPage, PageMetadata
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.tools.autolinker import AutoLinker
from wiki_agent.tools.ingest import DocumentIngestor


def test_autolinker_logic():
    known_concepts = ["Redes Neuronales", "Aprendizaje Profundo", "Python"]
    linker = AutoLinker(known_concepts)

    raw_text = "El Aprendizaje Profundo usa Redes Neuronales programadas en Python. CÃ³digo: `import Python`."
    linked = linker.apply_links(raw_text)

    assert "[[Aprendizaje Profundo]]" in linked
    assert "[[Redes Neuronales]]" in linked
    assert "[[Python]]" in linked
    # Verificar que el cÃ³digo en backticks no fue modificado
    assert "`import Python`" in linked


def test_document_ingestor_with_autolinking():
    temp_dir = tempfile.mkdtemp()
    try:
        backend = LocalMarkdownBackend(base_path=temp_dir)
        mgr = WikiKnowledgeManager()
        mgr.backend = backend

        # Crear concepto previo
        meta = PageMetadata(title="Kubernetes", category="DevOps")
        backend.write_page(WikiPage(metadata=meta, content="Orquestador de contenedores."))

        # Ingestar texto nuevo mencionando Kubernetes
        ingestor = DocumentIngestor(mgr)
        res = ingestor.ingest_text(
            title="Despliegue Cloud",
            text="Vamos a desplegar los microservicios usando Kubernetes en producciÃ³n.",
            category="DevOps",
            auto_link=True
        )

        assert res["status"] == "success"
        page = backend.read_page("Despliegue Cloud")
        assert page is not None
        assert "[[Kubernetes]]" in page.content
        assert "Kubernetes" in page.outgoing_links
    finally:
        shutil.rmtree(temp_dir)