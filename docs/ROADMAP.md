# Roadmap de Desarrollo Iterativo

Este proyecto se desarrolla de forma incremental mediante iteraciones bien delimitadas:

```
[ Iteración 1: Bases y Especificación ]                          ✅ COMPLETADA
               │
               ▼
[ Iteración 2: Motor de Wiki y Grafo Local ]                     ✅ COMPLETADA
               │
               ▼
[ Iteración 3: Servidor MCP e Integración Antigravity ]          ✅ COMPLETADA
               │
               ▼
[ Iteración 4: Ingesta de Documentos y Recopilación Web ]        ✅ COMPLETADA (⚠️ Deprecado)
               │
               ▼
[ Iteración 5: Exportador de Fine-Tuning y Modelos Locales ]     ✅ COMPLETADA
               │
               ▼
[ Iteración 6: Cola de Ingesta Persistente ]                     ✅ COMPLETADA (⚠️ Deprecado)
               │
               ▼
[ Iteración 7: Fine-Tuning y Despliegue del Modelo ]             ✅ COMPLETADA
               │
               ▼
[ Iteración 8: Datasets Acumulativos y Agente ReAct ]            ✅ COMPLETADA  <-- Estado Actual
               │
               ▼
[ Iteración 9: Búsqueda Semántica con Embeddings ]               📋 PLANIFICADA
               │
               ▼
[ Iteración 10: Adaptadores de Wiki Remota y Automatización ]
```

---

## Detalle de las Fases

### Fase 1: Fundaciones, Especificación y Documentación ✅
- [x] Estructura base del proyecto en `C:\Users\ENEKO\Desktop\SAUCE\IA`.
- [x] Modelos de datos del dominio en Pydantic (`WikiPage`, `PageMetadata`, `SearchResult`, `ConceptRelation`).
- [x] Implementación inicial de backend local en Markdown.
- [x] Documentación exhaustiva para Antigravity y guías de arquitectura.

### Fase 2: Robustez del Motor Conceptual y Búsqueda ✅
- [x] Backend XML (`local_xml`) como formato principal de almacenamiento.
- [x] Detección automática de conceptos huérfanos y enlaces rotos (`wiki_diagnose_health`).
- [x] Generación automática de índices y mapas conceptuales (`wiki_rebuild_indexes`).
- [x] Motor de salud del grafo (`core/health.py`) e indexador (`core/indexer.py`).
- [ ] Búsqueda semántica complementaria con embeddings locales (ONNX/fastembed) — *pendiente Fase 9*

### Fase 3: Integración con Antigravity (MCP) ✅
- [x] Servidor MCP operativo (`src/wiki_agent/mcp_server.py`).
- [x] Configuración lista en `mcp_config.json` para conectar con Antigravity.
- [x] `WikiAssistantEngine` con contexto enriquecido (concepto + citas expandidas + backlinks).
- [x] Resolución activa de stubs (`wiki_resolve_stub`).
- [x] Instrucciones de comportamiento definidas en `docs/ANTIGRAVITY_SYSTEM_PROMPT.md`.
- [x] Flujo interactivo: consulta, guardado, actualización y enlazado de conceptos vía MCP.

### Fase 4: Pipeline de Ingesta Inteligente y Recopilación Web ✅ ⚠️ DEPRECADO
> **Nota:** Esta fase fue implementada pero el sistema de ingesta no se usa activamente.
> El código permanece en el repositorio pero está marcado como deprecado.

- [x] Procesador multi-formato: PDF, TXT, Markdown y URLs (`tools/ingest.py`).
- [x] Fragmentación por secciones temáticas.
- [x] Auto-enlazado de conceptos conocidos (`tools/autolinker.py`) — *este módulo sí sigue activo*.
- [x] WebCollector con limpieza de DOM para scraping (`tools/collector.py`) — *deprecado*.
- [x] Verificador de fuentes (`tools/verifier.py`).

### Fase 5: Pipeline de Entrenamiento y Fine-Tuning de IA Local ✅
- [x] Generador de pares Instrucción-Respuesta a partir de la estructura wiki.
- [x] Soporte de formatos estándar: `ShareGPT`, `Alpaca`, `JSONL QA`.
- [x] Script `generate_agent_dataset.py` para volcado de la wiki.
- [x] Herramienta MCP `wiki_export_training_dataset`.

### Fase 6: Cola de Ingesta Persistente ✅ ⚠️ DEPRECADO
> **Nota:** Implementada pero el sistema de cola de ingesta no se utiliza activamente.

- [x] `IngestionQueueManager` con estado persistente en `data/queue/ingest_queue.json`.
- [x] Procesamiento por lotes configurable (`--count`, `--all`, `--delay`).
- [x] Comandos CLI: `queue add`, `queue status`, `queue list`, `queue run`, `queue clear`.
- [x] Herramientas MCP: `wiki_queue_add_item`, `wiki_queue_get_status`, `wiki_queue_process_batch`.

### Fase 7: Fine-Tuning y Despliegue del Modelo Local ✅
- [x] Primer fine-tuning (FT1) de Llama 3.2 con estándares CLI y micro-formato XML.
- [x] Modelo exportado en formato `.gguf` (cuantizado Q4_K_M, ~2 GB).
- [x] Proveedor `llamacpp` implementado — carga directa de GGUF sin dependencias externas.
- [x] Proveedor `ollama` disponible como alternativa.
- [x] `config.yaml` actualizado para usar el modelo fine-tuned como LLM activo.

### Fase 8: Datasets Acumulativos y Agente ReAct ✅ ← COMPLETADA
- [x] **Estrategia de datasets acumulativos** adoptada: cada versión del modelo se entrena desde el modelo base Llama 3.2 con un dataset acumulativo (no fusión de GGUFs).
- [x] **Estándar de nombres de datasets** implementado:
  - Parciales: `dataset_ft1_cli_standards.jsonl`, `dataset_ft2_agent_react.jsonl`
  - Acumulativos: `dataset_cumulative_v2.jsonl` (v1, v2, v3...)
- [x] Script `generate_ft1_dataset.py` — Reconstrucción del dataset FT1 (comunicación CLI reactiva directa).
- [x] Script `generate_agent_dataset.py` — Dataset FT2 (razonamiento ReAct con `<thought>` y herramientas multi-ciclo).
- [x] Script `build_cumulative_dataset.py` — Orquestador que genera parciales y fusiona en acumulativo.
- [x] Módulo `CumulativeDatasetBuilder` (`tools/dataset_manager.py`) — Normalización ShareGPT, deduplicación por hash MD5, métricas por categoría.
- [x] Agente autónomo con bucle ReAct (`agent/loop.py`) — `<thought>`, `<response>`, `<commands>`.
- [x] Segundo fine-tuning (FT2) ejecutado en Google Colab con **Unsloth**.
- [x] Modelo unificado `llama3.2-finetuning-unificado.gguf` activo en producción.

### Fase 9: Refactorización POO del Agente, Desacoplamiento de UI y UX Limpia ✅ ← COMPLETADA
- [x] **Arquitectura Orientada a Objetos en `wiki_agent.agent`**:
  - `ConceptXmlExtractor`: Extracción y validación robusta de micro-etiquetas XML (`<definition>`, `<sections>`, `<relations>`) y filtro de anuncios transitorios ("Voy a...").
  - `AgentResponseParser`: Parseo y sanitizado de respuestas del LLM, extracción limpia de pensamientos y comandos con desduplicación.
  - `AgentCommand` y `CommandDispatcher`: Patrón *Command* desacoplando `/search`, `/read`, `/save`, `/edit` y `/delete`.
  - `WikiAgent` en `loop.py` transformado en orquestador limpio.
- [x] **Capa de Presentación Modular en `wiki_agent.ui`**:
  - `TokenStreamProcessor`: Procesamiento de streaming en vivo mostrando pensamientos en tenue (`🧠 Razonando...`), soporte dual `<thought>` y `[PENSAMIENTO INTERNO]`, y supresión de fragmentos en ciclos intermedios de Deep Dive.
  - `ConsoleRenderer`: Renderizado de cabecera cian única, árbol conceptual jerárquico consultado e insignias de métricas de rendimiento.
  - `InteractiveChatSession`: Bucle interactivo REPL desacoplado de `cli.py`.
- [x] **Mejora del Backend de Memoria XML**:
  - Búsqueda y resolución de títulos insensible a acentos/diacríticos (`local_xml.py`).
- [x] **Validación y Pruebas**:
  - Tests unitarios completos pasando (`Ran 8 tests: OK`).
  - Sincronización transparente y verificada con el entorno de pruebas `E:\IA`.

### Fase 10: Búsqueda Semántica con Embeddings Locales 📋 PLANIFICADA
- [ ] Embeddings locales rápidos mediante ONNX/fastembed (opcional, sin GPU).
- [ ] Índice vectorial persistente para búsqueda semántica complementaria.
- [ ] Integración transparente: búsqueda híbrida (texto + semántica) con re-ranking.

### Fase 11: Adaptadores Remotos y Sincronización
- [ ] Adaptador para MediaWiki API.
- [ ] Adaptador para Wiki.js / DokuWiki.
- [ ] Sincronización bidireccional y control de versiones Git integrado.