# Arquitectura del Sistema Wiki-Memory Agent

```mermaid
graph TD
    subgraph UI ["Capa de Interfaz / Presentación (ui/)"]
        AG[Antigravity Chat / MCP]
        CLI[Terminal CLI Click - cli.py]
        ICS[InteractiveChatSession - REPL y comandos]
        CR[ConsoleRenderer - Paneles Rich y Árbol Wiki]
        TSP[TokenStreamProcessor - Streaming y Thoughts en Vivo]
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
        FT1[generate_ft1_dataset.py - CLI Standards]
        FT2[generate_agent_dataset.py - ReAct Agent]
        CDB[build_cumulative_dataset.py - Orquestador]
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
    CDB --> DSM
```

## Componentes del Código

### Motor Conceptual
- **`src/wiki_agent/models.py`**: Modelos tipados con Pydantic (`WikiPage`, `PageMetadata`, `SearchResult`, `ConceptRelation`).
- **`src/wiki_agent/backends/`**: 
  - `base.py`: Contrato `BaseWikiBackend`.
  - `local_xml.py`: Backend activo — Parser XML con Frontmatter YAML + extracción regex de `[[wikilinks]]` + backlinks.
  - `local_markdown.py`: Backend heredado (no activo).
- **`src/wiki_agent/core/manager.py`**: Lógica de alto nivel para gestión de conceptos, resolución de rutas y búsquedas ponderadas.
- **`src/wiki_agent/core/assistant.py`**: `WikiAssistantEngine` — Inyección de contexto enriquecido.
- **`src/wiki_agent/core/health.py`**: Motor de salud del grafo (stubs, huérfanos, enlaces rotos).
- **`src/wiki_agent/core/indexer.py`**: Generador de índices y mapas conceptuales (MOC).

### Agente Autónomo POO (`src/wiki_agent/agent/`)
- **`loop.py`**: `WikiAgent` — Orquestador del bucle ReAct autónomo multi-ciclo, recuperando contexto de memoria e interactuando con el LLM.
- **`parser.py`**: `AgentResponseParser` — Extracción estructurada de `<thought>`, `[PENSAMIENTO INTERNO]`, `<response>` y filtrado de comandos válidos con desduplicación y sanitizado de metatags.
- **`xml_extractor.py`**: `ConceptXmlExtractor` — Extracción y validación rigurosa de micro-etiquetas XML (`<definition>`, `<sections>`, `<relations>`) y filtro de anuncios transitorios ("Voy a...").
- **`commands.py`**: `AgentCommand` y `CommandDispatcher` — Implementación del patrón *Command* para la ejecución interna de `/search`, `/read`, `/save`, `/edit`, `/delete`.
- **`src/wiki_agent/llm/`**:
  - `base.py`: Interfaz abstracta `LLMBackend`.
  - `llamacpp.py`: Proveedor activo — carga directa de GGUF con `llama-cpp-python` (CPU o GPU).
  - `ollama.py`: Proveedor alternativo — requiere Ollama instalado.

### Capa de Interfaz y Presentación (`src/wiki_agent/ui/`)
- **`stream_processor.py`**: `TokenStreamProcessor` — Máquina de estados para streaming en vivo: visualización tenue de pensamientos (`🧠 Razonando...`) y supresión transparente de salidas intermedias en Deep Dive.
- **`renderer.py`**: `ConsoleRenderer` — Presentación Rich: panel cian único, árbol conceptual jerárquico consultado, tablas de ayuda y badges de métricas (`tok/s`, latencia, RAM).
- **`chat_session.py`**: `InteractiveChatSession` — Gestión del bucle interactivo REPL y despacho de comandos de terminal (`/stats`, `/tree`, `/save`, `/edit`, `/read`, `/delete`, `/clear`, `/exit`).
- **`src/wiki_agent/cli.py`**: Punto de entrada Click modular y delgado.
- **`src/wiki_agent/mcp_server.py`**: Servidor MCP con herramientas estándar para agentes IA.

## Flujo de Fine-Tuning

```mermaid
graph LR
    FT1[FT1: CLI Standards] --> MERGE[build_cumulative_dataset.py]
    FT2[FT2: Agent ReAct] --> MERGE
    FTN[FT-N: Futuros...] -.-> MERGE
    MERGE --> CUM[dataset_cumulative_vN.jsonl]
    CUM --> COLAB[Google Colab + Unsloth]
    BASE[Llama 3.2 Base] --> COLAB
    COLAB --> GGUF[llama3.2-finetuning-*.gguf]
    GGUF --> AGENT[Agente Local]
```