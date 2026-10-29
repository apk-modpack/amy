import re
from typing import List, Set


class AutoLinker:
    """Detecta menciones a conceptos existentes en textos sin procesar y genera [[wikilinks]] automÃ¡ticamente."""

    def __init__(self, existing_concepts: List[str]):
        # Ordenar por longitud descendente para priorizar conceptos compuestos ("Redes Neuronales Convolucionales" antes que "Redes")
        self.concepts = sorted([c.strip() for c in existing_concepts if len(c.strip()) > 2], key=len, reverse=True)

    def apply_links(self, text: str, max_links_per_concept: int = 1) -> str:
        """Sustituye menciones exactas por [[Concepto]], respetando enlaces existentes o bloques de cÃ³digo."""
        if not self.concepts or not text:
            return text

        # Proteger bloques de cÃ³digo ```...``` y enlaces existentes [[...]]
        protected_blocks: List[str] = []
        
        def protect(match):
            protected_blocks.append(match.group(0))
            return f"__PROTECTED_BLOCK_{len(protected_blocks) - 1}__"

        # Proteger cÃ³digo
        text_protected = re.sub(r"```[\s\S]*?```|`[^`]+`", protect, text)
        # Proteger enlaces ya existentes
        text_protected = re.sub(r"\[\[[^\]]+\]\]", protect, text_protected)

        # Aplicar reemplazo para cada concepto
        for concept in self.concepts:
            pattern = re.compile(rf"\b({re.escape(concept)})\b", re.IGNORECASE)
            matches = list(pattern.finditer(text_protected))
            if matches:
                # Reemplazar solo la primera ocurrencia por defecto
                count = 0
                def replace_func(m):
                    nonlocal count
                    if count < max_links_per_concept:
                        count += 1
                        return f"[[{concept}]]"
                    return m.group(0)

                text_protected = pattern.sub(replace_func, text_protected, count=max_links_per_concept)

        # Restaurar bloques protegidos
        for idx, original in enumerate(protected_blocks):
            text_protected = text_protected.replace(f"__PROTECTED_BLOCK_{idx}__", original)

        return text_protected