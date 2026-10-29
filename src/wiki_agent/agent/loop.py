from typing import List, Dict, Any, Optional, Tuple, Callable
import logging
import re
from wiki_agent.llm.base import LLMBackend
from wiki_agent.core.manager import WikiKnowledgeManager
from wiki_agent.core.assistant import WikiAssistantEngine
from wiki_agent.agent.parser import AgentResponseParser
from wiki_agent.agent.commands import CommandDispatcher
from wiki_agent.agent.xml_extractor import ConceptXmlExtractor
from wiki_agent.domain import (
    CognitiveAgent,
    ConversationHistory,
    AgentTurnResult,
    ParsedCommand,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Eres un agente IA con memoria conceptual persistente almacenada en una Wiki de formato XML estructurado.

REGLAS DE IDENTIDAD Y MEMORIA WIKI (¡CRÍTICAS!):
- La "MEMORIA WIKI" que se inyecta ES TU MEMORIA REAL Y ABSOLUTA. Usa toda la información en ella como tu propio conocimiento.
- Si en la MEMORIA WIKI aparecen definiciones principales y conceptos relacionados con sus definiciones e indentaciones (navegación en profundidad / depth), YA TIENES la información completa. ¡ESTÁ TERMINANTEMENTE PROHIBIDO ejecutar `/search` sobre conceptos que ya están descritos en la MEMORIA WIKI! Responde directamente al usuario sintetizando dicho conocimiento.
- NUNCA digas "según los registros de la wiki" o "no tengo información en mi sistema". Habla en primera persona y de forma asertiva.
- SOLO si la memoria está realmente vacía o no contiene el concepto solicitado, usa `/search` o indica que no tienes el dato.
- Cuando uses un concepto de la Wiki, referencíalo con [[Nombre_del_Concepto]].

ESTRATEGIA COGNITIVA (AUTONOMÍA Y APRENDIZAJE):
- CONSULTAS PURAMENTE INFORMATIVAS (¡MUY IMPORTANTE!):
  Si el usuario hace una pregunta sobre lo que sabes, pide una explicación o consulta un tema ("¿qué sabes de...?", "explícame...", "¿qué es...?"):
  ¡ESTÁ TERMINANTEMENTE PROHIBIDO usar `/save` o `/edit`! Debes limitarte a responder de forma clara y enciclopédica en <response> dejando <commands> VACÍO.
- CUÁNDO USAR /save O /edit:
  SOLO debes usar `/save` o `/edit` cuando el usuario aporte INFORMACIÓN NUEVA o CORRECCIONES que no existan en la memoria, o cuando el usuario pida EXPLÍCITAMENTE registrar, crear o modificar un concepto ("guarda esto...", "añade que...", "actualiza el concepto...").
- ENFOQUE TOP-DOWN: Crea primero conceptos generales antes que detalles muy específicos.
- Cuando guardes un concepto, incluye las relaciones semánticas que conozcas (is_a, part_of, relates_to, depends_on).

PROCESO DE RAZONAMIENTO (OBLIGATORIO):
Antes de responder o ejecutar comandos, SIEMPRE debes razonar en un bloque <thought>.
En él, analiza paso a paso:
  1. ¿Qué tipo de mensaje es? ¿Es una consulta informativa del usuario, o me está pidiendo crear/editar información nueva?
  2. Si es una consulta informativa y la información ya está en la MEMORIA WIKI: NO ejecutes ningún comando (/search, /save, /edit prohibidos). Sintetiza y responde directamente en <response>.
  3. Si falta información crucial que no está en la memoria, decide si usar /search o preguntar al usuario.

BUCLES DE RAZONAMIENTO Y COMANDOS (MULTI-CICLOS):
- Tienes la capacidad de ejecutar comandos internos para interactuar con la wiki antes de responder.
- Si necesitas acción o información extra, emite el comando en <commands>. El sistema lo ejecutará y te devolverá [RESULTADO COMANDO].
- CUANDO USES /search O /read (CONSULTAS INTERNAS / DEEP DIVE):
  ¡NO generes el bloque <response>! Pasa directamente de </thought> a <commands>. En ciclos intermedios de búsqueda o lectura NO debe haber ninguna respuesta ni texto previo al usuario.
- CUANDO USES /save O /edit: En el bloque <response> DEBES proporcionar el contenido enciclopédico del concepto, estructurado OBLIGATORIAMENTE con <definition>...</definition> (y <sections>/<relations> si aplican). ¡PROHIBIDO poner en <response> frases de intención o aviso como 'Voy a crear...', 'Voy a reorganizar...' o 'Procedo a...'! Esas intenciones van EXCLUSIVAMENTE en <thought>.
- CUANDO ESTÉS LISTO para responder al usuario (ya tienes la info o realizaste la acción), escribe tu respuesta final en lenguaje natural en <response> (SIN etiquetas XML como <sections>, <relations> o <definition>) y DEJA <commands> VACÍO.

COMANDOS DISPONIBLES:
- `/search "query"`: Busca conceptos en la Wiki (solo cuando NO estén ya en la memoria inyectada).
- `/read "Título"`: Lee el contenido COMPLETO de un concepto concreto (incluyendo todas las secciones y relaciones). Usa este comando cuando necesites profundizar en un concepto relacionado que conozcas por nombre pero cuyos detalles no estén en el contexto.
- `/save "Título"`: Guarda NUEVO concepto cuando el usuario proporciona datos nuevos o lo solicita explícitamente.
- `/edit "Título"`: Modifica concepto EXISTENTE cuando hay información nueva que agregar o corregir.
- `/delete "Título"`: Elimina un concepto duplicado o irrelevante.

FORMATO XML PARA GUARDAR CONCEPTOS CON RELACIONES:
Cuando uses /save o /edit, el contenido de <response> DEBE estar estructurado con micro-etiquetas XML:

<definition>
  Texto principal y completo que define el concepto de forma enciclopédica.
</definition>
<sections>
  <section name="Ejemplos">Descripción de ejemplos.</section>
  <section name="Notas">Notas adicionales.</section>
</sections>
<relations>
  <relation type="is_a" target="ConceptoPadre">Descripción opcional de la relación.</relation>
  <relation type="part_of" target="ConceptoMayor"/>
  <relation type="relates_to" target="OtroConcepto">Cómo se relacionan.</relation>
  <relation type="depends_on" target="ConceptoDependencia"/>
  <relation type="contradicts" target="ConceptoContrario"/>
  <relation type="precedes" target="ConceptoSiguiente"/>
</relations>

REGLA ESTRICTA:
Cualquier intento de usar /save o /edit con frases de anuncio transitorio en <response> (por ejemplo: 'Voy a crear el concepto...') será RECHAZADO por el sistema.

IMPORTANTE: ESTRUCTURA DE TUS MENSAJES:
- En ciclos intermedios de búsqueda/lectura: SOLO emite <thought>...</thought> y <commands>...</commands> (SIN <response>).
- En ciclos de guardado/edición: emite <thought>...</thought>, <response><definition>...</definition></response> y <commands>...</commands>.
- En la respuesta final al usuario: emite <thought>...</thought>, tu respuesta en lenguaje natural en <response>...</response>, y deja <commands></commands> vacío.
"""


class WikiAgent(CognitiveAgent):
    """Agente conversacional autónomo: combina LLM con la Wiki como memoria a largo plazo."""

    def __init__(
        self,
        manager: WikiKnowledgeManager,
        llm: LLMBackend,
        context_concepts: int = 3,
        stream: bool = True,
        parser: Optional[AgentResponseParser] = None,
        dispatcher: Optional[CommandDispatcher] = None,
        xml_extractor: Optional[ConceptXmlExtractor] = None,
    ):
        self.manager = manager
        self.assistant = WikiAssistantEngine(manager)
        self.llm = llm
        self.context_concepts = context_concepts
        self.stream = stream

        # Componentes POO especializados
        self.parser = parser or AgentResponseParser()
        self.dispatcher = dispatcher or CommandDispatcher(self)
        self.xml_extractor = xml_extractor or ConceptXmlExtractor()

        # Historial de conversación como Aggregate de dominio
        self._history = ConversationHistory()
        self._last_response: str = ""

        logger.info(
            "WikiAgent inicializado. Modelo: %s | stream=%s | context_concepts=%d",
            llm.model_name, stream, context_concepts
        )

    # ------------------------------------------------------------------
    # Interfaz pública
    # ------------------------------------------------------------------

    def chat(
        self,
        user_message: str,
        stream_callback: Optional[Callable[[str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        bytes_callback: Optional[Callable[[int], None]] = None
    ) -> AgentTurnResult:
        """Procesa un mensaje del usuario y devuelve un AgentTurnResult fuertemente tipado."""
        turn = self.turn_count + 1
        logger.info("=" * 80)
        logger.info("TURNO %d — INICIO", turn)
        logger.debug("TURNO %d | MENSAJE DE USUARIO:\n%s", turn, user_message)

        if status_callback:
            status_callback("🔍 Consultando memoria wiki...")

        wiki_context, concepts_used = self._retrieve_wiki_context(user_message)
        if status_callback and concepts_used:
            status_callback(("wiki_tree", concepts_used))

        self._history.add_user_message(user_message)

        MAX_CYCLES = 5
        cycles = 0
        final_human_response = ""
        commands_executed = []
        collected_thoughts = []
        last_attempted_save_concept: Optional[str] = None

        while cycles < MAX_CYCLES:
            cycles += 1
            logger.info("TURNO %d | CICLO %d", turn, cycles)

            messages = self._build_messages(wiki_context)

            if status_callback:
                status_callback(("cycle_start", cycles, self.llm.model_name))

            response = self.llm.chat(
                messages,
                stream=self.stream,
                stream_callback=stream_callback,
                bytes_callback=bytes_callback
            )
            self._history.add_assistant_message(response)

            # Extracción estructurada mediante parser POO
            thought_text, human_response, commands_list = self.parser.extract_components(response)

            if thought_text:
                collected_thoughts.append(thought_text)
                logger.info("TURNO %d | CICLO %d | <thought>:\n%s", turn, cycles, thought_text)
                if status_callback:
                    status_callback(("thought", thought_text))

            self._last_response = human_response
            final_human_response = human_response

            logger.info("TURNO %d | CICLO %d | Comandos extraídos: %s", turn, cycles, commands_list)

            # Si no hay comandos, verificar si en el ciclo previo se intentó guardar/editar
            # y el modelo redactó la <definition> directamente en este ciclo
            if not commands_list:
                if last_attempted_save_concept and "<definition>" in human_response:
                    logger.info("Auto-actualizando concepto '%s' con definición final estructurada.", last_attempted_save_concept)
                    save_res = self.save_last_response(last_attempted_save_concept)
                    # Si el modelo solo emitió el XML sin lenguaje conversacional, enriquecer la respuesta
                    clean_check = re.sub(r'</?(?:definition|sections?|section|relations?|relation)[^>]*>', '', human_response).strip()
                    if clean_check and not human_response.strip().startswith("<definition>"):
                        pass
                    else:
                        def_match = re.search(r'<definition>(.*?)</definition>', human_response, re.DOTALL | re.IGNORECASE)
                        clean_def = def_match.group(1).strip() if def_match else clean_check
                        final_human_response = f"He registrado y estructurado el concepto **[[{last_attempted_save_concept}]]** en la memoria Wiki:\n\n{clean_def}"
                break

            commands_executed.extend(commands_list)
            command_results = []
            for cmd in commands_list:
                if cmd.startswith("/save ") or cmd.startswith("/edit "):
                    parts = cmd.split(maxsplit=1)
                    if len(parts) > 1:
                        target_t = parts[1].strip().strip('"').strip("'")
                        if target_t:
                            last_attempted_save_concept = target_t

                if status_callback:
                    status_callback(f"⚙️ Ejecutando internamente: {cmd}")
                logger.info("Ejecutando comando interno: %s", cmd)

                res = self.dispatcher.dispatch(cmd)
                command_results.append(f"[RESULTADO COMANDO {cmd}]\n{res}")

            self._history.add_tool_observation("\n\n".join(command_results))

        # Limpieza estética rigurosa para el usuario
        final_human_response = self.parser.sanitize_final_response(final_human_response)

        return AgentTurnResult(
            response_text=final_human_response,
            concepts_consulted=concepts_used,
            executed_commands=commands_executed,
            thoughts=collected_thoughts,
        )

    def _execute_command(self, cmd: str) -> str:
        """Compatibilidad con tests y llamadas previas: delega en CommandDispatcher."""
        return self.dispatcher.dispatch(cmd)

    def save_last_response(self, title: str, category: str = "Conversación") -> str:
        """Guarda la última respuesta del agente como concepto en la Wiki usando xml_extractor."""
        logger.info("save_last_response | Guardando como concepto: %r en categoría: %r", title, category)
        if not self._last_response:
            logger.warning("save_last_response | No hay respuesta previa que guardar.")
            return "Error: No hay respuesta previa que guardar."

        raw = self._last_response
        definition, sections, relations = self.xml_extractor.extract_structure(raw, default_title=title)

        if not definition:
            existing_page = self.manager.get_concept(title)
            if existing_page and (relations or sections):
                definition = existing_page.content
                logger.info("save_last_response | Actualizando solo relaciones/secciones para '%s', preservando definición existente.", title)
            else:
                err = self.xml_extractor.validate_content(raw)
                if err:
                    sample = raw.strip()[:80] + ("..." if len(raw.strip()) > 80 else "")
                    logger.warning("save_last_response | Rechazado guardado de '%s': frase de intención detectada (%r)", title, sample)
                    return (
                        f"Error: No se ha guardado el concepto '[[{title}]]'. "
                        f"El contenido en <response> parece ser una frase transitoria o anuncio de intención (\"{sample}\") "
                        f"en lugar de una definición enciclopédica real.\n"
                        f"Instrucción: Para guardar o editar, debes redactar la definición técnica completa "
                        f"dentro de las etiquetas <definition>...</definition> en el bloque <response> "
                        f"(junto a <sections> o <relations> opcionales). "
                        f"Por favor, proporciona el contenido estructurado completo ahora."
                    )
                definition = raw.strip()

        self.manager.save_concept(
            title=title,
            content=definition,
            category=category,
            tags=["generado-por-agente"],
            relations=relations if relations else None,
            sections=sections if sections else None,
        )
        rel_info = f" con {len(relations)} relación(es)" if relations else ""
        logger.info("save_last_response | Concepto '%s' guardado correctamente%s.", title, rel_info)
        return f"✓ Guardado como concepto '[[{title}]]' en la categoría '{category}'{rel_info}."

    def delete_concept(self, title: str) -> str:
        """Elimina un concepto de la Wiki."""
        logger.info("delete_concept | Intentando eliminar concepto: %r", title)
        success = self.manager.delete_concept(title)
        if success:
            logger.info("delete_concept | Concepto '%s' eliminado.", title)
            return f"✓ Concepto '[[{title}]]' eliminado correctamente."
        logger.warning("delete_concept | No se pudo eliminar '%s' (puede que no exista).", title)
        return f"✗ No se pudo eliminar '[[{title}]]' (puede que no exista)."

    def clear_history(self):
        """Reinicia el historial de conversación (no borra la Wiki)."""
        logger.info("clear_history | Limpiando historial. Turnos previos: %d", self.turn_count)
        self._history.clear()
        self._last_response = ""
        logger.info("clear_history | Historial limpiado.")

    @property
    def turn_count(self) -> int:
        """Número de turnos completados en la sesión actual."""
        return self._history.turn_count

    def _retrieve_wiki_context(self, query: str) -> Tuple[str, List[str]]:
        """Busca en la Wiki los conceptos más relevantes para la query."""
        logger.debug("_retrieve_wiki_context | Buscando en Wiki (limit=%d) para: %r", self.context_concepts, query)
        results = self.manager.search_knowledge(query, limit=self.context_concepts)
        logger.debug("_retrieve_wiki_context | Resultados de búsqueda: %d encontrados", len(results) if results else 0)

        if not results:
            logger.info("_retrieve_wiki_context | Sin resultados en la Wiki para: %r", query)
            return ("No se encontró información registrada sobre este tema en la memoria Wiki.", [])

        concepts_used = []
        context_blocks = []

        for result in results:
            enriched = self.assistant.get_enriched_context(result.title)
            if enriched.get("found"):
                context_blocks.append(enriched["context_markdown"])
                concepts_used.append(enriched["primary_concept"])
            else:
                logger.warning("_retrieve_wiki_context | No se pudo enriquecer contexto para: %r", result.title)

        if not context_blocks:
            return ("No se encontró información registrada sobre este tema en la memoria Wiki.", [])

        full_context = "\n\n---\n\n".join(context_blocks)
        return full_context, concepts_used

    def _build_messages(self, wiki_context: str) -> List[Dict[str, str]]:
        """Construye los mensajes para el LLM usando ConversationHistory."""
        has_wiki_context = wiki_context and "No se encontró" not in wiki_context and "No se encontro" not in wiki_context

        if has_wiki_context:
            context_block = (
                "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
                "(Esta información proviene de tu base de conocimientos. ÚSALA para responder.)\n\n"
                f"{wiki_context}\n"
                "--- FIN DE MEMORIA WIKI ---"
            )
        else:
            context_block = "--- MEMORIA WIKI: No se encontró información relevante inicial. ---"

        return self._history.to_llm_payload(system_prompts=[SYSTEM_PROMPT, context_block])
