# Registro de Cambios (Changelog)

Todos los cambios notables en el proyecto **Wiki-Memory AI Agent System** se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

---

## [Iteración 14] - Cola Asíncrona de Mensajes Humanos y UX Concurrente (Completada)

Adaptación de la Sala de Chat gráfica y del receptor de red del agente para permitir el envío continuo de mensajes humanos en ráfaga, encolándolos en una cola FIFO para su procesamiento ordenado sin bloquear la interfaz.

### Añadido
- **Cola FIFO en Receptor del Agente (`src/wiki_agent/ui/chat_session.py`)**:
  - Desacoplamiento de la lectura de socket TCP y la ejecución del bucle ReAct mediante `queue.Queue`.
  - Hilo trabajador en segundo plano (`ChatSession-Worker`) que despacha secuencialmente cada mensaje sin saturar la inferencia del LLM.
  - Reporte de estado dinámico a la red: métrica de mensajes pendientes en cola inyectada en el detalle de `AgentState.PROCESANDO`.
- **Icono de Estado `queue` en GUI (`src/wiki_agent/chat_room.py`)**:
  - Incorporación del glifo `📥` para notificaciones de mensajes encolados.

### Modificado
- **Entrada Continua en Sala de Chat (`src/wiki_agent/chat_room.py`)**:
  - Supresión del bloqueo de la caja de texto (`disabled`) tras el envío de mensajes. La caja permanece siempre en estado `normal`, permitiendo que el usuario envíe múltiples mensajes consecutivos mientras el agente procesa turnos previos.
  - Auto-recuperación de estado en refresco periódico para evitar bloqueos por desconexión o comandos sin respuesta de texto.

---

## [Iteración 13] - Wiki-Grounding, Menor Dependencia de Contexto y Pipeline FT6 (Completada)

Entrenamiento y refuerzo de directivas de grounding en la memoria wiki: desconfianza de la memoria interna paramétrica (anti-alucinación), persistencia proactiva (context-to-wiki offloading), comprobación de hechos y navegación estructurada por enlaces en grafo (`[[Concepto]]`), dataset FT6 de 100 ejemplos y dataset acumulativo maestro v6 de 600 ejemplos.

### Añadido
- **Generador de Dataset FT6 (`generate_ft6_wiki_grounding_dataset.py`)**:
  - 100 ejemplos únicos estructurados en 4 bloques funcionales (25 ej. c/u):
    - Bloque 1: Anti-alucinación y verificación previa mediante `/search` o `/read`.
    - Bloque 2: Persistencia proactiva y descarga de contexto volátil a disco con `/save` o `/edit`.
    - Bloque 3: Reconciliación y comprobación de hechos contra la wiki persistida.
    - Bloque 4: Exploración guiada de enlaces de grafo mediante `/read "Concepto"`.
  - Estándar multi-fuente: 20 ejemplos originados por agentes compañeros (`[DE: <Agente>]`) y 80 por `HUMAN`.
- **Suite de Pruebas Unitarias (`tests/test_wiki_grounding.py`)**:
  - Tests para directivas de prompt, estructura/balance de FT6, despacho de `/read` y extracción de componentes por el parser.
- **Dataset Acumulativo Maestro v6 (`dataset_cumulative_v6.jsonl`)**:
  - Consolidación de 600 ejemplos únicos (100 ejemplos por cada fine-tuning FT1..FT6) sin duplicados.

### Modificado
- **System Prompt del Agente (`src/wiki_agent/agent/loop.py`)**:
  - Refuerzo de la sección `REGLAS DE IDENTIDAD Y MEMORIA WIKI` con directivas explícitas de Wiki-Grounding y desconfianza de memoria interna paramétrica.
  - Obligatoriedad de offloading proactivo a la wiki cuando se transmita información crítica en el chat.
- **Constructor de Datasets (`build_cumulative_dataset.py`)**:
  - Integración del paso FT6 y configuración de `dataset_cumulative_v6.jsonl` como salida por defecto.

---

## [Iteración 12] - Proceso Cognitivo (Task List), Loop Guard, Pipeline FT5 y Adaptación Multi-Fuente (Completada)

Introducción del sistema de tareas cognitivas para el agente: soporte para descomponer solicitudes complejas en un plan `<tasks>`, comandos internos `/task_add`, `/task_done`, `/task_list`, bucle multi-ciclo resiliente con protección contra bucles infinitos, dataset FT5 de 100 ejemplos, adaptación del estándar multi-fuente (`HUMAN` vs `[DE: <Agente>]`) en todos los datasets y dataset acumulativo maestro v5 de 500 ejemplos.

### Añadido
- **Gestor de Tareas Cognitivas (`src/wiki_agent/agent/task_list.py`)**:
  - Clases `TaskItem` y `AgentTaskManager` para modelar y seguir el estado de tareas durante turnos multi-ciclo.
  - Métodos `set_tasks`, `add_task`, `complete_task` (por índice, ID o texto), `complete_next`, `has_pending_tasks`, `render_summary` y `to_list`.
- **Comandos de Tareas en `CommandDispatcher` (`src/wiki_agent/agent/commands.py`)**:
  - `/task_add`: Añade una subtarea dinámica en tiempo de razonamiento.
  - `/task_done`: Marca una tarea como completada y reporta las restantes.
  - `/task_list`: Muestra la lista de tareas en texto estructurado.
- **Parser de Tareas (`src/wiki_agent/agent/parser.py`)**:
  - Extracción de bloques `<tasks>...</tasks>` y reconocimiento de prefijos de comando `/task_*`.
- **Generador de Dataset FT5 (`generate_ft5_tasklist_dataset.py`)**:
  - 100 ejemplos únicos (50 respuestas directas sin tareas + 50 tareas complejas con `<tasks>` y comandos de tarea).
- **Pruebas Automatizadas (`tests/test_task_manager.py`)**:
  - Cobertura completa del ciclo de vida de tareas, extracción por parser y despacho de comandos `/task_*`.

### Modificado
- **Conciencia Multi-Fuente en Datasets FT2, FT3 y FT5**:
  - `generate_agent_dataset.py` (FT2): 21 ejemplos adaptados con emisor agente (`[DE: <Agente>]`) y primer paso en `<thought>` reconociendo al par.
  - `generate_ft3_dataset.py` (FT3): 17 ejemplos de agentes delegando almacenamiento/edición estructurada de especificaciones técnicas.
  - `generate_ft5_tasklist_dataset.py` (FT5): 17 ejemplos de tareas cognitivas multi-etapa delegadas por agentes orquestadores.
  - Distribución total: FT1 (100H), FT2 (21A/79H), FT3 (17A/83H), FT4 (74A/26H), FT5 (17A/83H).
- **Bucle del Agente (`src/wiki_agent/agent/loop.py`)**:
  - Inicialización de `AgentTaskManager` por agente y limpieza de tareas al inicio de cada turno.
  - Aumento de ciclos máximos a 8 con guardián estricto para prevenir bucles infinitos.
  - Continuación autónoma del bucle si restan tareas pendientes (`has_pending_tasks`), inyectando el estado actualizado de la lista como observación.
- **Dataset Acumulativo Maestro (`build_cumulative_dataset.py`)**:
  - Incorporación del paso FT5 y generación de `dataset_cumulative_v5.jsonl` con exactamente 500 ejemplos únicos consolidados (100 ejemplos por cada uno de los 5 fine-tunings).

---

## [Iteración 11] - Identidad Persistente del Agente, Protocolo Multi-Agente y Pipeline FT4 (Completada)

Soporte integral para identidades persistentes en agentes, reserva inmutable del emisor humano (`HUMAN`), presencia multi-agente en sala de chat y reestructuración simétrica de fine-tunings a 100 ejemplos por dataset (400 ejemplos en dataset maestro).

### Añadido
- **Identidad del Agente (`src/wiki_agent/agent/identity.py`)**:
  - `AgentIdentityManager`: persistencia en `data/agent_identity.json` con `agent_id` UUID, `agent_name` autogenerado y timestamp de creación.
  - Generación automática de nombres técnicos aleatorios únicos (ej. `Kinetics-Seeker-18`).
  - Bloqueo y sanitización estricta de nombres reservados: `HUMAN`, `HUMANO` y `USER`.
- **Comandos de Consola y Red**:
  - Comando `/identify` integrado en `CommandDispatcher` y bucle interactivo de terminal.
  - Comando `/agents` para consultar en vivo la lista de presencia en la sala.
- **Protocolo de Red Multi-Agente (`src/wiki_agent/network/`)**:
  - Constante `HUMAN_SENDER = "HUMAN"` y tipo de mensaje `AGENT_LIST`.
  - Soporte para múltiples conexiones concurrentes en `ChatRoomServer` (`_connected_clients`).
  - Difusión automática de presencia a todos los agentes conectados (`_broadcast_agent_list`).
  - Modos de estado canónicos del agente: `LISTO`, `PROCESANDO`, `ERROR` y `DESCONECTADO`.
- **Generador de Dataset FT4 (`generate_ft4_multiagent_dataset.py`)**:
  - 100 ejemplos especializados en interacción inter-agente vs humano, sincronización y respeto al rol `HUMAN`.
- **Pruebas Automatizadas (`tests/test_identity_and_multiagent.py`)**:
  - Cobertura de persistencia, generación de nombres, regla `HUMAN`, comando `/identify` y protocolo `AGENT_LIST`.

### Modificado
- **Ampliación de Datasets de Fine-Tuning**:
  - `FT1` ampliado de 38 a 100 ejemplos únicos.
  - `FT2` ampliado de 51 a 100 ejemplos únicos.
  - `FT3` ampliado de 20 a 100 ejemplos únicos.
  - `build_cumulative_dataset.py` consolidado generando `dataset_cumulative_v4.jsonl` con exactamente 400 ejemplos balanceados.
- **`chat_room.py`**:
  - Limpieza inmediata del campo de entrada antes de deshabilitación.
  - Lanzadores silenciosos (`iniciar_sala_de_chat.bat` y `iniciar_sala_de_chat.vbs`) sin ventana CMD residual.
  - Menú de salida y botón de cierre explícito con confirmación si hay agentes conectados.

---

## [Iteración 10] - Arquitectura Cliente-Servidor: Sala de Chat GUI + Modo Red (Completada)

Separación del sistema en dos programas independientes comunicados por red, añadiendo una interfaz gráfica de ventana como sala de chat y modificando el agente para recibir sus inputs desde la red en lugar del teclado.

### Añadido

- **Módulo de Red (`src/wiki_agent/network/`)**:
  - `protocol.py`: Protocolo NDJSON v1 sobre TCP puro. Mensajes tipados con Pydantic, versionado explícito y funciones constructoras de conveniencia. Tipos: `handshake`, `handshake_ack`, `chat_message`, `agent_status`, `agent_response`, `ping/pong`, `disconnect`, `error`.
  - `connection.py`: `RobustSocketConnection` — envuelve un socket TCP con búfer acumulativo de líneas que resuelve la fragmentación TCP (packet sticking/splitting). Thread-safe en envíos con `send_lock`.
  - `server.py`: `ChatRoomServer` — servidor TCP con bucle de aceptación en segundo plano, negociación de handshake automática y callbacks event-driven: `on_agent_connected`, `on_agent_disconnected`, `on_agent_response`, `on_agent_status`. Incluye `get_local_ip_addresses()` para mostrar las IPs disponibles.
  - `client.py`: `AgentNetworkClient` — cliente TCP para el Agente IA; gestiona conexión, handshake, recepción de mensajes y envío de respuestas/estados.
  - `__init__.py`: Exportaciones unificadas del módulo.

- **Sala de Chat GUI (`src/wiki_agent/chat_room.py`)**:
  - Ventana Tkinter con tema oscuro (paleta Catppuccin Mocha).
  - Historial de chat con colores diferenciados por emisor (usuario, IA, sistema, metadatos).
  - Barra de estado en tiempo real de la IA: `🧠 Pensando…`, `🔍 Buscando…`, `💾 Guardando…`.
  - Panel lateral con IPs de escucha disponibles, puerto y datos del agente conectado.
  - Indicador de conexión (punto verde/rojo) sincronizado con el estado real de la red.
  - Entrada por `Enter` (enviar) / `Shift+Enter` (nueva línea).
  - Botón de limpieza del historial de chat.

- **Nuevos launchers**:
  - `iniciar_sala_de_chat.bat` — Inicia la Sala de Chat (debe ejecutarse primero).
  - `iniciar_agente_modo_red.bat` — Inicia el Agente IA en modo red (solicita IP al inicio).

- **Tests (`tests/test_network.py`)**: 4 tests unitarios que verifican:
  - Serialización/deserialización del protocolo NDJSON.
  - Metadatos en `agent_response`.
  - Manejo de fragmentación TCP en `RobustSocketConnection`.
  - Flujo completo handshake + chat_message + agent_response en servidor real.

### Modificado

- **`InteractiveChatSession` (`src/wiki_agent/ui/chat_session.py`)**:
  - Nuevo parámetro opcional `network_client=None`.
  - Dos modos de operación: `LOCAL` (teclado, comportamiento original 100% intacto) y `NETWORK` (inputs desde la Sala de Chat).
  - El agente envía notificaciones de estado (`agent_status`) a la Sala de Chat durante el procesamiento.
  - `/stats` ahora muestra el modo de entrada activo.

- **CLI (`src/wiki_agent/cli.py`)**:
  - Comando `chat` ampliado con opciones `--connect <IP>` y `--port <N>`.
  - Sin `--connect`: solicita la IP de forma interactiva al inicio (Enter vacío = modo local).
  - Nuevo comando `chat-room` que lanza la Sala de Chat GUI.

- **`iniciar_wiki_agent.bat`**: Actualizado con instrucciones de referencia a los nuevos launchers.

### Documentación

- Nuevo documento de iteración: [`docs/iterations/ITERATION_10_CHAT_ROOM_NETWORK_ARCHITECTURE.md`](docs/iterations/ITERATION_10_CHAT_ROOM_NETWORK_ARCHITECTURE.md).
- `docs/ARCHITECTURE.md` actualizado con el diagrama de la arquitectura de red.
- `docs/ROADMAP.md` actualizado: Iteración 10 completada, renumeradas las siguientes.
- `README.md` actualizado con la nueva sección de uso y estructura.

---

## [Iteración 9] - Refactorización POO del Agente, Desacoplamiento de UI y UX Limpia (Completada)

### Añadido
- **Arquitectura Orientada a Objetos en `wiki_agent.agent`**:
  - `ConceptXmlExtractor` — Extracción y validación robusta de micro-etiquetas XML (`<definition>`, `<sections>`, `<relations>`) y filtro de anuncios transitorios ("Voy a...").
  - `AgentResponseParser` — Parseo y sanitizado de respuestas del LLM con desduplicación.
  - `AgentCommand` y `CommandDispatcher` — Patrón *Command* desacoplando `/search`, `/read`, `/save`, `/edit` y `/delete`.
  - `WikiAgent` en `loop.py` transformado en orquestador limpio.
- **Capa de Presentación Modular en `wiki_agent.ui`**:
  - `TokenStreamProcessor` — Streaming en vivo de pensamientos en tenue, soporte dual `<thought>` y `[PENSAMIENTO INTERNO]`, supresión en ciclos Deep Dive.
  - `ConsoleRenderer` — Cabecera cian única, árbol conceptual jerárquico e insignias de métricas.
  - `InteractiveChatSession` — Bucle REPL desacoplado de `cli.py`.
- **Backend XML**: Búsqueda insensible a acentos/diacríticos.
- **Tests**: 8 tests unitarios pasando.

---

## [Iteración 8] - Datasets Acumulativos y Agente ReAct (Completada)

### Añadido
- Estrategia de datasets acumulativos (sin fusión de GGUFs).
- Scripts `generate_ft1_dataset.py`, `generate_agent_dataset.py`, `generate_ft3_dataset.py`.
- `build_cumulative_dataset.py` — orquestador de generación acumulativa.
- `CumulativeDatasetBuilder` (`tools/dataset_manager.py`) — normalización ShareGPT, deduplicación MD5.
- Agente autónomo con bucle ReAct (`agent/loop.py`) — `<thought>`, `<response>`, `<commands>`.
- Fine-tuning FT2 con Unsloth en Google Colab.

---

## [Iteración 5] - Pipeline de Datasets de Entrenamiento para Fine-Tuning (Completada)

### Añadido
- **Módulo `DatasetExporter` (`src/wiki_agent/tools/dataset_exporter.py`)**:
  - Exportación de pares instrucción-respuesta basados en conceptos y relaciones semánticas.
  - Soporte multiformato: **ShareGPT**, **Alpaca**, **ChatML/OpenAI** y `jsonl_qa`.
  - Generador automático de **Modelfile para Ollama**.
- **Comandos CLI**: `wiki-agent export`, `wiki-agent modelfile`.
- **Herramientas MCP**: `wiki_export_training_dataset`, `wiki_generate_ollama_modelfile`.

---

## [Iteración 4] - Ingesta Inteligente y Auto-enlazado Conceptual (Completada)

### Añadido
- **`AutoLinker` (`src/wiki_agent/tools/autolinker.py`)** — activo y operativo.
- **`DocumentIngestor`** (`tools/ingest.py`) — ⚠️ Deprecado.
- **`WebCollector`** (`tools/collector.py`) — ⚠️ Deprecado.
- **`SourceVerifier`** (`tools/verifier.py`).

---

## [Iteración 3] - Servidor MCP e Integración con Antigravity (Completada)

### Añadido
- **Servidor MCP** (`src/wiki_agent/mcp_server.py`).
- **`WikiAssistantEngine`** con contexto enriquecido.
- Configuración `mcp_config.json` y documentación de instrucciones para Antigravity.

---

## [Iteración 2] - Motor de Salud Conceptual e Indexación MOC (Completada)

### Añadido
- `WikiHealthChecker` (`core/health.py`).
- `WikiIndexer` (`core/indexer.py`).
- Backend XML `local_xml` (`backends/local_xml.py`).
- Comandos CLI: `wiki-agent doctor`, `wiki-agent index`.
- Herramientas MCP: `wiki_diagnose_health`, `wiki_rebuild_indexes`.

---

## [Iteración 1] - Fundaciones, Arquitectura y Contratos de Dominio (Completada)

### Añadido
- Modelos Pydantic: `WikiPage`, `PageMetadata`, `SearchResult`, `ConceptRelation`.
- Contrato abstracto `BaseWikiBackend`.
- `LocalMarkdownBackend` inicial.
- Documentación de visión y arquitectura.

---

## [Próximas Iteraciones]

- **Iteración 11**: Búsqueda semántica híbrida con embeddings vectoriales locales (ONNX/fastembed).
- **Iteración 12**: Adaptadores remotos (MediaWiki, Wiki.js) y sincronización Git integrada.
