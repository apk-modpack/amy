# Arquitectura del Sistema Wiki-Memory Agent

```mermaid
graph TD
    subgraph NetLayer ["Capa de Red (network/)"]
        CRS[ChatRoomServer - Servidor TCP]
        ANC[AgentNetworkClient - Cliente TCP]
        PROTO[Protocolo NDJSON v1]
        CRS <-->|TCP socket| ANC
        CRS --- PROTO
        ANC --- PROTO
    end

    subgraph ChatRoom ["Sala de Chat — Programa 1 (chat_room.py)"]
        GUI[GUI Tkinter — Ventana de Chat]
        GUI <-->|callbacks thread-safe| CRS
    end

    subgraph UI ["Capa de Interfaz / Presentación (ui/)"]
        AG[Antigravity Chat / MCP]
        CLI[Terminal CLI Click - cli.py]
        ICS[InteractiveChatSession - REPL · modo LOCAL y NETWORK]
        CR[ConsoleRenderer - Paneles Rich y Árbol Wiki]
        TSP[TokenStreamProcessor - Streaming y Thoughts en Vivo]
        ANC --> ICS
    end

    subgraph Core ["Motor Conceptual (core/)"]
        KM[WikiKnowledgeManager - Gestor de Conceptos]
        KG[Analizador de Grafo y Backlinks]
        SE[Motor de Búsqueda Híbrida]
        AST[WikiAssistantEngine - Enriquecimiento de Contexto]
    end

    subgraph Agent ["Agente Autónomo POO (agent/)"]
        WA[WikiAgent - Orquestador del Bucle ReAct]
        ARP[AgentResponseParser - Parseo y Sanitizado]
        CXE[ConceptXmlExtractor - Validación de Micro-XML]
        CD[CommandDispatcher - Patrón Command Interno]
        LLM[LLM Local - llama-cpp-python / GGUF]
    end

    subgraph Adapters ["Adaptadores de Wiki (backends/)"]
        LXA[LocalXMLBackend - Activo / Normalización Acentos]
        LMA[LocalMarkdownBackend - Heredado]
    end

    subgraph Storage ["Almacenamiento Físico"]
        FS[Archivos XML en data/wiki/]
    end

    subgraph DatasetPipeline ["Pipeline de Datasets para Fine-Tuning"]
        FT1[generate_ft1_dataset.py - CLI Standards / 100 ej.]
        FT2[generate_agent_dataset.py - ReAct Agent / 100 ej.]
        FT3[generate_ft3_dataset.py - Structured Saves / 100 ej.]
        FT4[generate_ft4_multiagent_dataset.py - Multiagent / 100 ej.]
        FT5[generate_ft5_tasklist_dataset.py - Cognitive Tasks / 100 ej.]
        FT6[generate_ft6_wiki_grounding_dataset.py - Wiki Grounding / 100 ej.]
        CDB[build_cumulative_dataset.py - Orquestador v6 / 600 ej.]
        DSM[CumulativeDatasetBuilder - Fusión y Dedup]
        EXP[DatasetExporter - Wiki a JSONL]
    end

    AG --> KM
    CLI --> ICS
    ICS --> CR
    ICS --> TSP
    ICS --> WA

    WA --> ARP
    WA --> CXE
    WA --> CD
    WA --> LLM
    WA --> KM
    WA --> AST

    KM --> KG
    KM --> SE
    KM --> Adapters

    LXA --> FS
    LMA -.-> FS

    KM --> EXP
    FT1 --> CDB
    FT2 --> CDB
    FT3 --> CDB
    FT4 --> CDB
    FT5 --> CDB
    FT6 --> CDB
    CDB --> DSM
```

## Modos de Operación del Sistema

El sistema puede operar en dos modos de entrada, seleccionables en el arranque:

### Modo LOCAL (teclado — comportamiento original)
```
Usuario → Terminal → InteractiveChatSession → WikiAgent → LLM → Respuesta en terminal
```

### Modo RED (Sala de Chat GUI)
```
Usuario → GUI Tkinter → ChatRoomServer ──TCP NDJSON──► AgentNetworkClient
                                                              │
                                                    InteractiveChatSession
                                                              │
                                                          WikiAgent → LLM
                                                              │
                                         AgentNetworkClient ◄── Respuesta + Metadatos
                                                    │
                                             ChatRoomServer
                                                    │
                                            GUI (muestra respuesta)
```

---

## Componentes del Código

### Capa de Red (`src/wiki_agent/network/`)
- **`protocol.py`**: Protocolo NDJSON v1. Tipos de mensajes (`MessageType`, incluyendo `AGENT_LIST`), modelo `NetworkMessage` con Pydantic, versionado explícito, constante `HUMAN_SENDER = "HUMAN"` y funciones constructoras (`make_handshake`, `make_chat_message`, `make_agent_list`, `make_agent_status`).
- **`connection.py`**: `RobustSocketConnection` — búfer acumulativo de líneas para resolver la fragmentación TCP, `send_lock` para seguridad multi-hilo, cierre ordenado.
- **`server.py`**: `ChatRoomServer` — acepta conexiones simultáneas de múltiples agentes (`_connected_clients`), gestiona handshake con `client_name` y `client_id`, difunde la lista de presencia (`_broadcast_agent_list`) y despacha callbacks event-driven.
- **`client.py`**: `AgentNetworkClient` — conecta con la Sala de Chat, completa el handshake con su identidad persistente, almacena la lista de presencia de agentes y envía respuestas/estados tipados.

### Identidad Persistente del Agente (`src/wiki_agent/agent/identity.py`)
- **`AgentIdentityManager`**: Administra la persistencia en `data/agent_identity.json` (`agent_id` UUID, `agent_name`, `created_at`).
- Generación automática de nombres técnicos aleatorios únicos si no existe el archivo.
- Regla inmutable: Los nombres `HUMAN`, `HUMANO` y `USER` están reservados y estrictamente bloqueados para cualquier agente artificial.

### Sala de Chat GUI (`src/wiki_agent/chat_room.py`)
- Ventana Tkinter con tema oscuro (paleta Catppuccin Mocha).
- Historial de mensajes con etiquetas de color por tipo (usuario, IA, sistema, metadatos).
- Barra de estado en tiempo real (🧠 Pensando, 🔍 Buscando, 💾 Guardando…).
- Panel lateral con IPs disponibles, datos del agente e indicador de conexión verde/rojo.
- Sin dependencias externas — tkinter es estándar en todas las instalaciones de Python.

### Motor Conceptual
- **`src/wiki_agent/models.py`**: Modelos tipados con Pydantic (`WikiPage`, `PageMetadata`, `SearchResult`, `ConceptRelation`).
- **`src/wiki_agent/backends/`**:
  - `base.py`: Contrato `BaseWikiBackend`.
  - `local_xml.py`: Backend activo — Parser XML con Frontmatter YAML + extracción regex de `[[wikilinks]]` + backlinks + búsqueda insensible a acentos.
  - `local_markdown.py`: Backend heredado (no activo).
- **`src/wiki_agent/core/manager.py`**: Lógica de alto nivel para gestión de conceptos, resolución de rutas y búsquedas ponderadas.
- **`src/wiki_agent/core/assistant.py`**: `WikiAssistantEngine` — Inyección de contexto enriquecido.
- **`src/wiki_agent/core/health.py`**: Motor de salud del grafo (stubs, huérfanos, enlaces rotos).
- **`src/wiki_agent/core/indexer.py`**: Generador de índices y mapas conceptuales (MOC).

### Agente Autónomo POO (`src/wiki_agent/agent/`)
- **`loop.py`**: `WikiAgent` — Orquestador del bucle ReAct autónomo multi-ciclo (`MAX_CYCLES = 8`) con integración de lista de tareas y directivas de wiki-grounding.
- **`parser.py`**: `AgentResponseParser` — Extracción estructurada de `<thought>`, `<tasks>`, `<response>` y comandos válidos (`/search`, `/read`, `/save`, `/edit`, `/delete`, `/identify`, `/task_*`).
- **`task_list.py`**: `AgentTaskManager` y `TaskItem` — Modelado y seguimiento dinámico de tareas cognitivas paso a paso.
- **`identity.py`**: `AgentIdentityManager` — Identidad persistente del agente (`agent_id`, `agent_name`) y protección de la palabra clave `HUMAN`.
- **`xml_extractor.py`**: `ConceptXmlExtractor` — Validación rigurosa de micro-etiquetas XML y filtro de anuncios transitorios.
- **`commands.py`**: `AgentCommand` y `CommandDispatcher` — Patrón *Command* para `/search`, `/read`, `/save`, `/edit`, `/delete`, `/identify`, `/task_add`, `/task_done` y `/task_list`.
- **`src/wiki_agent/llm/`**:
  - `base.py`: Interfaz abstracta `LLMBackend`.
  - `llamacpp.py`: Proveedor activo — carga directa de GGUF con `llama-cpp-python` (`llama3.2-finetuning-v0.4.gguf`).
  - `ollama.py`: Proveedor alternativo.

### Capa de Interfaz y Presentación (`src/wiki_agent/ui/`)
- **`stream_processor.py`**: `TokenStreamProcessor` — Streaming en vivo de pensamientos en tenue y supresión en Deep Dive.
- **`renderer.py`**: `ConsoleRenderer` — Panel cian único, árbol conceptual, métricas de rendimiento.
- **`chat_session.py`**: `InteractiveChatSession` — Bucle REPL con soporte dual LOCAL/NETWORK, comandos interactivos (`/identify`, `/agents`, `/stats`) y arquitectura de cola de mensajes FIFO asíncrona (`queue.Queue` + worker thread) para admitir ráfagas de mensajes del usuario sin saturar la inferencia.
- **`src/wiki_agent/chat_room.py`**: Sala de Chat GUI (Tkinter) con caja de texto continua (sin bloqueo tras envío), feedback de cola de mensajes en tiempo real e indicador de estado del agente (`LISTO`, `PROCESANDO`, `ERROR`).
- **`src/wiki_agent/cli.py`**: Punto de entrada Click modular con comandos `chat`, `chat-room`, `mcp`, etc.
- **`src/wiki_agent/mcp_server.py`**: Servidor MCP con herramientas estándar para agentes IA.

---

## Flujo de Fine-Tuning

```mermaid
graph LR
    FT1[FT1: CLI Standards / 100 ej.] --> MERGE[build_cumulative_dataset.py]
    FT2[FT2: Agent ReAct / 100 ej.] --> MERGE
    FT3[FT3: Structured Saves / 100 ej.] --> MERGE
    FT4[FT4: Multiagent / 100 ej.] --> MERGE
    FT5[FT5: Cognitive Tasks / 100 ej.] --> MERGE
    FT6[FT6: Wiki Grounding / 100 ej.] --> MERGE
    MERGE --> CUM[dataset_cumulative_v6.jsonl / 600 ej.]
    CUM --> COLAB[Google Colab + Unsloth]
    BASE[Llama 3.2 Base] --> COLAB
    COLAB --> GGUF[llama3.2-finetuning-v0.4.gguf]
```
    COLAB --> GGUF[llama3.2-finetuning-*.gguf]
    AGENT[Agente Local]
    GGUF --> AGENT
```
