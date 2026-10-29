"""Parser y sanitizador de salidas generadas por el LLM.

Responsable de extraer pensamientos (<thought>, [PENSAMIENTO INTERNO]), respuestas humanas,
y comandos de acción interna (<commands>), filtrando artefactos de finetuning y duplicados.
"""

from typing import List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)


class AgentResponseParser:
    """Parsea respuestas del modelo y sanea el texto para el usuario final."""

    VALID_COMMAND_PREFIXES = ("/save ", "/edit ", "/search ", "/read ", "/delete ")

    RE_THOUGHT = re.compile(
        r'(?:<thought>|\[PENSAMIENTO INTERNO\])(.*?)(?:</thought>|\[/PENSAMIENTO INTERNO\])',
        re.DOTALL | re.IGNORECASE
    )

    RE_COMMANDS = re.compile(
        r'(?:<commands>|\[COMANDOS\]|\[COMMANDS\])(.*?)(?:</commands>|\[/COMANDOS\]|\[/COMMANDS\])',
        re.DOTALL | re.IGNORECASE
    )

    RE_RESPONSE = re.compile(
        r'(?:<response>|\[RESPONSE\]|\[RESPUESTA AUTÓNOMA\])(.*?)(?:</response>|\[COMANDOS\]|\[COMMANDS\]|<commands>|$)',
        re.DOTALL | re.IGNORECASE
    )

    def extract_components(self, raw_response: str) -> Tuple[str, str, List[str]]:
        """Extrae (thought_text, human_response, commands_list) de la respuesta cruda del LLM.

        Args:
            raw_response: Cadena devuelta por el LLM.

        Returns:
            Tupla conteniendo:
              - thought_text: Razonamiento interno (o vacío)
              - human_response: Respuesta o borrador extraído
              - commands_list: Lista limpia de comandos a ejecutar
        """
        # 1. Thought
        thought_match = self.RE_THOUGHT.search(raw_response)
        thought_text = thought_match.group(1).strip() if thought_match else ""

        # 2. Commands
        commands_match = self.RE_COMMANDS.search(raw_response)
        commands_text = commands_match.group(1).strip() if commands_match else ""
        raw_commands = [cmd.strip() for cmd in commands_text.split('\n') if cmd.strip()]

        # Filtrar comandos estrictamente válidos
        clean_commands = [
            cmd for cmd in raw_commands
            if any(cmd.startswith(prefix) for prefix in self.VALID_COMMAND_PREFIXES)
        ]

        # Desduplicar /save o /edit repetidos sobre el mismo concepto en el mismo ciclo
        commands_list = self._deduplicate_save_edit(clean_commands)

        # 3. Human response
        response_match = self.RE_RESPONSE.search(raw_response)
        if response_match:
            human_response = response_match.group(1).strip()
        else:
            human_response = "" if commands_match else raw_response.strip()

        return thought_text, human_response, commands_list

    def _deduplicate_save_edit(self, commands: List[str]) -> List[str]:
        """Conserva solo la última ocurrencia de /save o /edit para el mismo título."""
        seen_titles = {}
        for i, cmd in enumerate(commands):
            if cmd.startswith("/save ") or cmd.startswith("/edit "):
                parts = cmd.split(maxsplit=1)
                if len(parts) > 1:
                    t = parts[1].strip().strip('"').strip("'")
                    seen_titles[t] = i

        result = []
        for i, cmd in enumerate(commands):
            if cmd.startswith("/save ") or cmd.startswith("/edit "):
                parts = cmd.split(maxsplit=1)
                if len(parts) > 1:
                    t = parts[1].strip().strip('"').strip("'")
                    if seen_titles.get(t) != i:
                        continue
            result.append(cmd)
        return result

    def sanitize_final_response(self, text: str) -> str:
        """Limpia el texto final para el usuario eliminando etiquetas de entrenamiento, XML residual y slash commands."""
        if not text:
            return ""

        # Eliminar etiquetas de bloques internos de entrenamiento y metatags en corchetes
        cleaned = re.sub(
            r'\[/?(?:RESPUESTA AUTÓNOMA|RESPUESTA|RESPONSENDIDO[^\]]*|PENSAMIENTO INTERNO|COMANDOS? INICIAL|COMANDOS?|COMMANDS?)[^\]]*\]',
            '',
            text,
            flags=re.IGNORECASE
        )
        # Eliminar comandos /save, /edit, /search o /delete si quedaron impresos como texto
        cleaned = re.sub(r'/(?:save|edit|search|read|delete)\s+["\'][^"\']+["\']', '', cleaned)
        cleaned = re.sub(r'/(?:save|edit|search|read|delete)\s+\S+', '', cleaned)

        # Si el texto contiene estructura de micro-formato XML de base de datos,
        # formatear limpiamente la definición y secciones, y descartar el bloque completo de <relations>
        if "<relations>" in cleaned or "</relations>" in cleaned:
            cleaned = re.sub(r'<relations>.*?</relations>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Formatear secciones si existen con títulos legibles
        def _replace_section(m):
            name = m.group(1).strip()
            content = m.group(2).strip()
            return f"\n\n**{name}:**\n{content}"

        cleaned = re.sub(
            r'<section\s+name=["\']([^"\']+)["\']>(.*?)</section>',
            _replace_section,
            cleaned,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Eliminar cualquier etiqueta XML restante (<definition>, <sections>, etc.)
        cleaned = re.sub(
            r'</?(?:definition|sections?|section|relations?|relation|response|thought|commands?)[^>]*>',
            '',
            cleaned,
            flags=re.IGNORECASE
        )

        # Normalizar saltos de línea repetidos
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
        return cleaned
