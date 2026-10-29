import tempfile
import shutil
from pathlib import Path
from wiki_agent.backends.local_markdown import LocalMarkdownBackend
from wiki_agent.models import WikiPage, PageMetadata
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.core.assistant import WikiAssistantEngine


def test_assistant_enriched_context_and_stub_resolution():
    temp_dir = tempfile.mkdtemp()
    try:
        backend = LocalMarkdownBackend(base_path=temp_dir)
        mgr = WikiKnowledgeManager()
        mgr.backend = backend
        assistant = WikiAssistantEngine(mgr)

        # 1. Crear concepto principal que enlace a un subconcepto
        meta = PageMetadata(title="Arquitectura de Microservicios", category="Software")
        page = WikiPage(metadata=meta, content="PatrÃ³n que divide sistemas en servicios independientes como [[API Gateway]].")
        backend.write_page(page)

        # 2. Obtener contexto enriquecido
        context = assistant.get_enriched_context("Microservicios")
        assert context["found"] is True
        assert "API Gateway" in context["outgoing_links"]
        assert "Contexto de Memoria Wiki: Arquitectura de Microservicios" in context["context_markdown"]

        # 3. Resolver el stub de API Gateway
        resolved = assistant.resolve_stub("API Gateway", "Punto de entrada Ãºnico para gestionar peticiones hacia microservicios.", category="Software")
        assert resolved.title == "API Gateway"

        # 4. Verificar que ahora ambos conceptos existen y estÃ¡n enlazados
        loaded_gateway = backend.read_page("API Gateway")
        assert loaded_gateway is not None
        backlinks = backend.get_backlinks("API Gateway")
        assert "Arquitectura de Microservicios" in backlinks
    finally:
        shutil.rmtree(temp_dir)