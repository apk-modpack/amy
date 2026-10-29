import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.models import WikiPage


class DatasetExporter:
    """Generador de datasets de fine-tuning y perfiles de modelos locales a partir de la Wiki."""

    def __init__(self, manager: WikiKnowledgeManager):
        self.manager = manager

    def export_to_jsonl(
        self,
        output_path: Optional[str] = None,
        format_type: str = "sharegpt",
        include_relational_qa: bool = True
    ) -> str:
        """Exporta el conocimiento de la wiki a un dataset estructurado en formato JSONL."""
        pages = self.manager.backend.get_all_pages()
        out_dir = Path(self.manager.config.get("export", {}).get("output_dir", "./data/exports"))
        out_dir.mkdir(parents=True, exist_ok=True)
        
        target_file = Path(output_path) if output_path else out_dir / f"wiki_dataset_{format_type}.jsonl"

        examples: List[Dict[str, Any]] = []

        for page in pages:
            if page.title.startswith("Ãndice_") or page.title == "Ãndice_Maestro":
                continue

            # 1. Ejemplo de definiciÃ³n y contenido
            ex_def = self._format_definition_example(page, format_type)
            if ex_def:
                examples.append(ex_def)

            # 2. Ejemplo relacional si tiene enlaces o backlinks
            if include_relational_qa and (page.outgoing_links or page.backlinks):
                ex_rel = self._format_relational_example(page, format_type)
                if ex_rel:
                    examples.append(ex_rel)

        with open(target_file, "w", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")

        return str(target_file)

    def _format_definition_example(self, page: WikiPage, format_type: str) -> Optional[Dict[str, Any]]:
        title = page.title
        category = page.metadata.category
        tags = ", ".join(page.metadata.tags)
        content = page.content.strip()
        outgoing = ", ".join([f"[[{link}]]" for link in page.outgoing_links]) if page.outgoing_links else "Ninguno directo"

        system_msg = "Eres un asistente de IA con acceso a una base de conocimientos estructurada en Wiki. Responde de forma precisa citando conceptos relacionados."

        if format_type == "sharegpt":
            return {
                "conversations": [
                    {
                        "from": "human",
                        "value": f"Â¿QuÃ© es y quÃ© informaciÃ³n contiene el concepto '{title}' en la categorÃ­a '{category}'?"
                    },
                    {
                        "from": "gpt",
                        "value": f"**{title}** (CategorÃ­a: {category}, Etiquetas: {tags})\n\n{content}\n\n**Conceptos relacionados:** {outgoing}"
                    }
                ]
            }
        elif format_type == "chatml" or format_type == "openai":
            return {
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Explica el concepto '{title}' registrado en la categorÃ­a '{category}'."},
                    {"role": "assistant", "content": f"**{title}**\n\n{content}\n\n**Conceptos vinculados:** {outgoing}"}
                ]
            }
        elif format_type == "alpaca":
            return {
                "instruction": f"Proporciona una explicaciÃ³n detallada del concepto '{title}'.",
                "input": f"CategorÃ­a: {category}. Etiquetas: {tags}.",
                "output": f"{content}\n\nConceptos relacionados: {outgoing}"
            }
        return None

    def _format_relational_example(self, page: WikiPage, format_type: str) -> Optional[Dict[str, Any]]:
        title = page.title
        outgoing = ", ".join([f"[[{l}]]" for l in page.outgoing_links]) if page.outgoing_links else "Sin enlaces salientes"
        backlinks = ", ".join([f"[[{b}]]" for b in page.backlinks]) if page.backlinks else "Sin menciones previas"

        system_msg = "Eres un asistente de IA experto en anÃ¡lisis de grafos y relaciones conceptuales."

        answer = (
            f"El concepto **{title}** tiene las siguientes conexiones en la base de conocimientos:\n"
            f"- **Referencias salientes (temas que aborda):** {outgoing}\n"
            f"- **Referencias entrantes (temas que citan a {title}):** {backlinks}"
        )

        if format_type == "sharegpt":
            return {
                "conversations": [
                    {
                        "from": "human",
                        "value": f"Â¿Con quÃ© otros temas y conceptos estÃ¡ conectado '{title}' en la memoria conceptual?"
                    },
                    {
                        "from": "gpt",
                        "value": answer
                    }
                ]
            }
        elif format_type == "chatml" or format_type == "openai":
            return {
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Â¿QuÃ© relaciones y dependencias tiene el concepto '{title}'?"},
                    {"role": "assistant", "content": answer}
                ]
            }
        elif format_type == "alpaca":
            return {
                "instruction": f"Analiza las dependencias y conexiones del concepto '{title}'.",
                "input": f"Concepto: {title}",
                "output": answer
            }
        return None

    def generate_ollama_modelfile(
        self,
        base_model: str = "llama3.2",
        output_file: Optional[str] = None
    ) -> str:
        """Genera un Modelfile de Ollama con un System Prompt que contiene el resumen del grafo de conocimiento."""
        out_dir = Path(self.manager.config.get("export", {}).get("output_dir", "./data/exports"))
        out_dir.mkdir(parents=True, exist_ok=True)
        target = Path(output_file) if output_file else out_dir / "Modelfile"

        all_pages = self.manager.backend.get_all_pages()
        concepts_summary = []
        for p in all_pages:
            if p.title.startswith("Ãndice_"):
                continue
            first_line = p.content.strip().split("\n")[0][:100]
            concepts_summary.append(f"- [[{p.title}]] ({p.metadata.category}): {first_line}")

        summary_text = "\n".join(concepts_summary)

        modelfile_content = f'''FROM {base_model}

# ParÃ¡metros del modelo
PARAMETER temperature 0.3
PARAMETER top_p 0.9

# System Prompt con base de conocimiento inyectada
SYSTEM """Eres un agente IA especializado dotado de memoria conceptual persistente.
Tienes conocimiento de los siguientes conceptos clave estructurados en Wiki:

{summary_text}

Cuando respondas al usuario, utiliza y referencia estos conceptos y sus relaciones con la sintaxis [[Concepto]]."""
'''
        target.write_text(modelfile_content, encoding="utf-8")
        return str(target)