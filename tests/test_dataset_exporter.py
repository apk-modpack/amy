import json
import tempfile
import shutil
from pathlib import Path
from wiki_agent.backends.local_markdown import LocalMarkdownBackend
from wiki_agent.models import WikiPage, PageMetadata
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.tools.dataset_exporter import DatasetExporter


def test_export_multiple_formats_and_relational_qa():
    temp_dir = tempfile.mkdtemp()
    try:
        backend = LocalMarkdownBackend(base_path=temp_dir)
        
        # Crear 2 conceptos vinculados
        meta1 = PageMetadata(title="Atencion Multi-Cabeza", category="Modelos_IA", tags=["transformers"])
        page1 = WikiPage(metadata=meta1, content="Mecanismo central de los [[Transformers]].")
        backend.write_page(page1)

        meta2 = PageMetadata(title="Transformers", category="Modelos_IA")
        page2 = WikiPage(metadata=meta2, content="Arquitectura basada en [[Atencion Multi-Cabeza]].")
        backend.write_page(page2)

        mgr = WikiKnowledgeManager()
        mgr.backend = backend
        mgr.config["export"]["output_dir"] = temp_dir
        exporter = DatasetExporter(mgr)

        # 1. Test ShareGPT
        sharegpt_file = exporter.export_to_jsonl(format_type="sharegpt")
        assert Path(sharegpt_file).exists()
        lines = Path(sharegpt_file).read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) >= 2  # Debe haber ejemplos directos y relacionales
        ex1 = json.loads(lines[0])
        assert "conversations" in ex1

        # 2. Test ChatML
        chatml_file = exporter.export_to_jsonl(format_type="chatml")
        lines_chatml = Path(chatml_file).read_text(encoding="utf-8").strip().split("\n")
        ex_chatml = json.loads(lines_chatml[0])
        assert "messages" in ex_chatml

        # 3. Test Ollama Modelfile
        modelfile_path = exporter.generate_ollama_modelfile(base_model="mistral")
        assert Path(modelfile_path).exists()
        modelfile_content = Path(modelfile_path).read_text(encoding="utf-8")
        assert "FROM mistral" in modelfile_content
        assert "[[Transformers]]" in modelfile_content
    finally:
        shutil.rmtree(temp_dir)