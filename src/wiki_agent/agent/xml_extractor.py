"""Extracción y validación de micro-formato XML en respuestas del modelo.

Responsable de extraer <definition>, <sections> y <relations> desde las respuestas
producidas por el LLM y validarlas antes de persistirlas en la Wiki.
"""

from typing import Dict, List, Optional, Tuple
import re
import logging
import xml.etree.ElementTree as ET
from wiki_agent.models import ConceptRelation

logger = logging.getLogger(__name__)


class ConceptXmlExtractor:
    """Extrae y valida estructuras semánticas XML de conceptos."""

    RE_ANNOUNCEMENT_START = re.compile(
        r'^\s*(?:voy a|procedo a|procederé a|crearé|actualizaré|modificaré|añadiré|reescribiré|organizaré|reorganizaré)\b',
        re.IGNORECASE
    )

    def extract_structure(self, raw_text: str, default_title: str) -> Tuple[str, Dict[str, str], List[ConceptRelation]]:
        """Extrae (definition, sections, relations) a partir del texto generado por el LLM.

        Args:
            raw_text: Texto crudo de la respuesta del LLM.
            default_title: Título del concepto a usar como fuente para las relaciones.

        Returns:
            Tupla (definition, sections, relations).
        """
        definition = ""
        sections: Dict[str, str] = {}
        relations: List[ConceptRelation] = []

        if not raw_text:
            return definition, sections, relations

        # 1. <definition>
        def_match = re.search(r"<definition>(.*?)</definition>", raw_text, re.DOTALL | re.IGNORECASE)
        if def_match:
            definition = def_match.group(1).strip()

        # 2. <sections>
        sec_match = re.search(r"<sections>(.*?)</sections>", raw_text, re.DOTALL | re.IGNORECASE)
        if sec_match:
            sec_xml = f"<sections>{sec_match.group(1)}</sections>"
            try:
                sec_el = ET.fromstring(sec_xml)
                for sec in sec_el.findall("section"):
                    sec_name = sec.get("name", "").strip()
                    sec_text = (sec.text or "").strip()
                    if sec_name and sec_text:
                        sections[sec_name] = sec_text
            except Exception as e:
                logger.warning("ConceptXmlExtractor | Error parseando <sections>: %s", e)

        # 3. <relations>
        rel_match = re.search(r"<relations>(.*?)</relations>", raw_text, re.DOTALL | re.IGNORECASE)
        if rel_match:
            rel_xml = f"<relations>{rel_match.group(1)}</relations>"
            try:
                rel_el = ET.fromstring(rel_xml)
                for rel in rel_el.findall("relation"):
                    rel_type = rel.get("type", "relates_to")
                    rel_target = rel.get("target", "").strip()
                    rel_desc = (rel.text or "").strip() or None
                    if rel_target:
                        relations.append(ConceptRelation(
                            source=default_title,
                            target=rel_target,
                            relation_type=rel_type,
                            description=rel_desc,
                        ))
            except Exception as e:
                logger.warning("ConceptXmlExtractor | Error parseando <relations>: %s", e)

        return definition, sections, relations

    def validate_content(self, text: str) -> Optional[str]:
        """Valida si un texto plano es apto para guardarse como definición sin <definition>.

        Returns:
            None si es válido, o un mensaje de error explicativo si no es válido.
        """
        stripped = text.strip()
        if len(stripped) < 35:
            return f"Error: La definición es demasiado corta ({len(stripped)} caracteres). Debe ser un concepto enciclopédico detallado."

        if self.RE_ANNOUNCEMENT_START.match(stripped):
            return "Error: La respuesta parece una frase de anuncio o intención ('Voy a...', 'Procedo a...'), no una definición enciclopédica válida."

        return None
