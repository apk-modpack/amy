# Registro de Cambios (Changelog)

Todos los cambios notables en el proyecto **Wiki-Memory AI Agent System** se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

---

## [Iteración 5] - Pipeline de Datasets de Entrenamiento para Fine-Tuning (Completada)

Esta iteración cierra el ciclo de auto-mejora del sistema, permitiendo transformar la base de conocimiento estructurada de la Wiki en material de entrenamiento para modelos de lenguaje locales.

### Añadido
- **Módulo `DatasetExporter` (`src/wiki_agent/tools/dataset_exporter.py`)**:
  - Exportación de pares instrucción-respuesta basados en conceptos y relaciones semánticas.
  - Soporte multiformato: **ShareGPT** (`sharegpt`), **Alpaca** (`alpaca`), **ChatML/OpenAI** (`chatml`/`openai`) y `jsonl_qa`.
  - Generador automático de **Modelfile para Ollama** con el grafo conceptual inyectado en el system prompt.
- **Comandos CLI**:
  - `wiki-agent export --format [sharegpt|alpaca|chatml|openai] [--output-dir]`: Exporta el dataset de entrenamiento.
  - `wiki-agent modelfile --model llama3.2 [--output]`: Genera plantilla Modelfile lista para Ollama.
- **Herramientas MCP**:
  - `wiki_export_training_dataset`: Exporta la base de conocimientos viva como dataset JSONL.
  - `wiki_generate_ollama_modelfile`: Crea el archivo Modelfile para compilación local en Ollama.
- **Documentación**: Documento de iteración en [`docs/iterations/ITERATION_05_FINE_TUNING_DATASET_PIPELINE.md`](docs/iterations/ITERATION_05_FINE_TUNING_DATASET_PIPELINE.md).

---

## [Iteración 4] - Ingesta Inteligente y Auto-enlazado Conceptual (Completada)

Capacidades para alimentar y enriquecer la base de conocimiento desde fuentes de texto externas y páginas web.

### Añadido
- **Módulo `AutoLinker` (`src/wiki_agent/tools/autolinker.py`)**:
  - Detección y enlazado automático de conceptos conocidos con `[[Wikilinks]]`.
  - Protección de bloques de código y enlaces preexistentes.
  - Ordenación de conceptos por longitud descendente para evitar colisiones de prefijo.
- **Módulo `DocumentIngestor` (`src/wiki_agent/tools/ingest.py`)**:
  - Procesador multi-formato (`.txt`, `.md`, `.pdf`) con segmentación por encabezados temáticos (`##`).
- **Módulo `WebCollector` (`src/wiki_agent/tools/collector.py`)**:
  - Recopilador web con limpieza de DOM (stripping de tags `<script>`, `<style>`, navegación) e integración con `AutoLinker`.
- **Módulo `SourceVerifier` (`src/wiki_agent/tools/verifier.py`)**:
  - Verificación de metadatos y trazabilidad de fuentes ingeridas.
- **Comandos CLI**:
  - `wiki-agent ingest <ruta>` y `wiki-agent collect-url <url>`.
- **Herramientas MCP**:
  - `wiki_ingest_text` y `wiki_collect_url`.

### Nota de Estado
> ⚠️ Los módulos de ingesta masiva y scraping web (`DocumentIngestor` y `WebCollector`) se encuentran actualmente deprecados en favor de la memoria conversacional directa y edición estructurada. `AutoLinker` permanece activo y operativo.

---

## [Iteración 3] - Servidor MCP e Integración con Antigravity (Completada)

Canal nativo de comunicación bidireccional entre la Wiki de memoria estructurada y agentes externos (Antigravity).

### Añadido
- **Servidor MCP (`src/wiki_agent/mcp_server.py`)**:
  - Implementación del protocolo Model Context Protocol vía stdin/stdout JSON-RPC.
  - Exposición de catálogo de herramientas de lectura, búsqueda, guardado y mantenimiento.
- **Motor de Asistencia (`src/wiki_agent/core/assistant.py`)**:
  - `WikiAssistantEngine.get_enriched_context()`: Inyección de contexto estructurado (definición + citas expandidas + relaciones + backlinks).
  - `WikiAssistantEngine.resolve_stub()`: Resolución asistida de conceptos pendientes.
- **Configuración e Instrucciones**:
  - Archivo de conexión [`mcp_config.json`](mcp_config.json).
  - Reglas operativas en [`docs/ANTIGRAVITY_SYSTEM_PROMPT.md`](docs/ANTIGRAVITY_SYSTEM_PROMPT.md) y [`docs/ANTIGRAVITY_INTEGRATION_GUIDE.md`](docs/ANTIGRAVITY_INTEGRATION_GUIDE.md).

---

## [Iteración 2] - Motor de Salud Conceptual e Indexación MOC (Completada)

Herramientas para garantizar la consistencia relacional del grafo, detectar inconsistencias y generar mapas de contenido.

### Añadido
- **Diagnóstico de Salud (`src/wiki_agent/core/health.py`)**:
  - `WikiHealthChecker`: Identificación de conceptos stubs (enlazados pero no definidos), páginas huérfanas y enlaces rotos.
- **Generación de Índices (`src/wiki_agent/core/indexer.py`)**:
  - `WikiIndexer`: Generación automática de Mapas de Contenido (`MOC_<Categoría>.xml`) e `Índice_Maestro.xml`.
- **Backend XML (`src/wiki_agent/backends/local_xml.py`)**:
  - Almacenamiento conceptual enriquecido en ficheros XML (`data/wiki/`).
- **Comandos CLI**:
  - `wiki-agent doctor`: Reporte de salud del grafo en terminal.
  - `wiki-agent index`: Regeneración de índices y taxonomías.
- **Herramientas MCP**:
  - `wiki_diagnose_health` y `wiki_rebuild_indexes`.

---

## [Iteración 1] - Fundaciones, Arquitectura y Contratos de Dominio (Completada)

Establecimiento de las bases del sistema, contratos de tipos y arquitectura desacoplada.

### Añadido
- **Modelos de Dominio (`src/wiki_agent/models.py`)**:
  - Modelos Pydantic tipados: `WikiPage`, `PageMetadata`, `SearchResult`, `ConceptRelation`.
- **Backend Base (`src/wiki_agent/backends/base.py`)**:
  - Contrato abstracto `BaseWikiBackend` para almacenamiento de páginas, metadatos y búsqueda.
- **Implementación Inicial de Backend**:
  - `LocalMarkdownBackend` para almacenamiento plano en Markdown con frontmatter YAML.
- **Documentación de Visión y Arquitectura**:
  - [`docs/VISION_AND_PHILOSOPHY.md`](docs/VISION_AND_PHILOSOPHY.md) y [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## [Próximas Iteraciones]

- **Iteración 6**: Cola de ingesta persistente por lotes (`IngestionQueueManager`). *(Deprecada / opcional)*.
- **Iteración 7**: Inferencia local y despliegue del modelo cuantizado con Llama 3.2 vía `llama-cpp-python`.
- **Iteración 8**: Estrategia de datasets acumulativos (FT1 + FT2 + FT3) y agente autónomo con bucle ReAct (`<thought>`).
- **Iteración 9**: Búsqueda semántica híbrida con embeddings vectoriales locales (ONNX/fastembed).
- **Iteración 10**: Adaptadores remotos (MediaWiki, Wiki.js) y sincronización Git integrada.
