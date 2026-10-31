# Roadmap de Desarrollo Iterativo

Este proyecto se desarrolla de forma incremental mediante iteraciones bien delimitadas:

```
[ Iteración 1: Bases y Especificación ]                                    ✅ COMPLETADA
               │
               ▼
[ Iteración 2: Motor de Wiki y Grafo Local ]                               ✅ COMPLETADA
               │
               ▼
[ Iteración 3: Servidor MCP e Integración Antigravity ]                    ✅ COMPLETADA
               │
               ▼
[ Iteración 4: Ingesta de Documentos y Recopilación Web ]                  ✅ COMPLETADA (⚠️ Deprecado)
               │
               ▼
[ Iteración 5: Exportador de Fine-Tuning y Modelos Locales ]               ✅ COMPLETADA
               │
               ▼
[ Iteración 6: Cola de Ingesta Persistente ]                               ✅ COMPLETADA (⚠️ Deprecado)
               │
               ▼
[ Iteración 7: Fine-Tuning y Despliegue del Modelo ]                       ✅ COMPLETADA
               │
               ▼
[ Iteración 8: Datasets Acumulativos y Agente ReAct ]                      ✅ COMPLETADA
               │
               ▼
[ Iteración 9: Refactorización POO del Agente y UX Limpia ]                ✅ COMPLETADA
               │
               ▼
[ Iteración 10: Arquitectura Red — Sala de Chat GUI + Modo Red ]           ✅ COMPLETADA
               │
               ▼
[ Iteración 11: Identidad Persistente, Multi-Agente y Pipeline FT4 ]       ✅ COMPLETADA
               │
               ▼
[ Iteración 12: Proceso Cognitivo (Task List), Loop Guard y Pipeline FT5 ]   ✅ COMPLETADA
               │
               ▼
[ Iteración 13: Wiki-Grounding, Menor Dependencia de Contexto y FT6 ]        ✅ COMPLETADA  (GGUF v0.4)
               │
               ▼
[ Iteración 14: Cola Asíncrona de Mensajes Humanos y UX Concurrente ]        ✅ COMPLETADA  ← Estado Actual
               │
               ▼
[ Iteración 15: Búsqueda Semántica con Embeddings ]                        📋 PLANIFICADA
               │
               ▼
[ Iteración 16: Adaptadores de Wiki Remota y Automatización ]
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
- [ ] Búsqueda semántica complementaria con embeddings locales (ONNX/fastembed) — *pendiente Fase 11*

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

### Fase 8: Datasets Acumulativos y Agente ReAct ✅
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

### Fase 9: Refactorización POO del Agente, Desacoplamiento de UI y UX Limpia ✅
- [x] **Arquitectura Orientada a Objetos en `wiki_agent.agent`**:
  - `ConceptXmlExtractor`, `AgentResponseParser`, `AgentCommand` y `CommandDispatcher`.
  - `WikiAgent` en `loop.py` transformado en orquestador limpio.
- [x] **Capa de Presentación Modular en `wiki_agent.ui`**:
  - `TokenStreamProcessor`, `ConsoleRenderer`, `InteractiveChatSession`.
- [x] **Mejora del Backend de Memoria XML**: Búsqueda insensible a acentos/diacríticos.
- [x] **Validación y Pruebas**: 8 tests unitarios pasando.
- [x] Sincronización transparente y verificada con el entorno de pruebas `E:\IA`.

### Fase 10: Arquitectura Red — Sala de Chat GUI + Modo Red ✅
- [x] **Módulo de red `src/wiki_agent/network/`** — protocolo NDJSON v1 sobre TCP puro:
  - `protocol.py`: tipos de mensajes versionados con Pydantic.
  - `connection.py`: `RobustSocketConnection` con búfer anti-fragmentación TCP.
  - `server.py`: `ChatRoomServer` con callbacks event-driven y aceptación en segundo plano.
  - `client.py`: `AgentNetworkClient` para el lado del agente.
- [x] **Sala de Chat GUI** (`src/wiki_agent/chat_room.py`):
  - Ventana Tkinter con tema oscuro, historial coloreado, barra de estado en tiempo real (`LISTO`, `PROCESANDO`, `ERROR`).
  - Panel lateral con IPs disponibles y datos del agente conectado.
  - Controles explícitos de salida y limpieza de entrada al enviar.
- [x] **`InteractiveChatSession` extendida** — soporte de modo red, 100% retrocompatible con modo local.
- [x] **Launchers**: `iniciar_sala_de_chat.bat` / `.vbs`, `iniciar_agente_modo_red.bat`.

### Fase 11: Identidad Persistente, Multi-Agente y Pipeline FT4 (400 Ejemplos) ✅
- [x] **Identidad del agente**: Módulo `agent/identity.py` (`AgentIdentityManager`), almacenamiento en `data/agent_identity.json` con UUID persistente y nombres autogenerados.
- [x] **Regla de emisor reservado `HUMAN`**: Prohibición de uso por agentes y marcado estricto en mensajes de la GUI (`sender: "HUMAN"`).
- [x] **Comando `/identify`**: Consulta o creación de credenciales del agente en tiempo de ejecución.
- [x] **Presencia en red multi-agente**: Difusión periódica de `AGENT_LIST` y soporte para múltiples agentes en la sala de chat.
- [x] **Comando `/agents`**: Inspección interactiva de participantes en la sala.
- [x] **Ampliación simétrica de Fine-Tuning (400 ejemplos en total)**:
  - `FT1` (100 ejemplos): micro-formato XML y comandos CLI con `/identify`.
  - `FT2` (100 ejemplos): ReAct con `<thought>` y discriminación de emisor (`HUMAN` vs otros agentes).
  - `FT3` (100 ejemplos): guardados limpios sin frases de anuncio y recuperación de rechazos.
  - `FT4` (100 ejemplos): protocolo inter-agente vs humano, intercambio conceptual y respeto a `HUMAN`.
- [x] **Dataset maestro**: `build_cumulative_dataset.py` consolidado generando `dataset_cumulative_v4.jsonl` (400 ejemplos exactos).
- [x] **Suite de pruebas**: 20 tests unitarios pasando en ambos entornos (`SAUCE\IA` y `E:\IA`).

### Fase 12: Proceso Cognitivo (Task List), Loop Guard y Pipeline FT5 (500 Ejemplos) ✅
- [x] **Gestor de tareas del agente**: Módulo `agent/task_list.py` (`AgentTaskManager`, `TaskItem`).
- [x] **Comandos de tareas**: `/task_add`, `/task_done`, `/task_list` integrados en `CommandDispatcher`.
- [x] **Parser de tareas**: Extracción de `<tasks>...</tasks>` y reconocimiento de comandos en `AgentResponseParser`.
- [x] **Bucle cognitivo multi-ciclo resiliente**: Ciclos de razonamiento continuos guiados por tareas pendientes (`MAX_CYCLES = 8`) con protección contra bucles infinitos en `loop.py`.
- [x] **Dataset FT5**: 100 ejemplos únicos (50 respuestas directas + 50 tareas complejas con `<tasks>`).
- [x] **Dataset maestro v5**: 500 ejemplos únicos consolidados en `dataset_cumulative_v5.jsonl`.
- [x] **Adaptación multi-fuente**: Integración de remitentes agentes compañeros en FT2 (21 ej.), FT3 (17 ej.) y FT5 (17 ej.).
- [x] **Suite de pruebas**: 24 tests unitarios pasando (cobertura completa de ciclo de vida de tareas).

### Fase 13: Wiki-Grounding, Menor Dependencia de Contexto y Pipeline FT6 (600 Ejemplos) ✅
- [x] **Generador FT6 (`generate_ft6_wiki_grounding_dataset.py`)**: 100 ejemplos en 4 bloques de 25 ej. (anti-alucinación, persistencia proactiva, reconciliación de hechos y exploración de enlaces de grafo; 20 agentes / 80 humanos).
- [x] **Refuerzo del System Prompt (`loop.py`)**: Directivas explícitas de desconfianza de memoria interna paramétrica, verificación obligatoria previa en wiki y offloading proactivo a disco.
- [x] **Dataset maestro v6**: `dataset_cumulative_v6.jsonl` consolidado con exactamente 600 ejemplos únicos (FT1..FT6 x 100 ej.) sin duplicados.
- [x] **Despliegue del Modelo GGUF v0.4**: `llama3.2-finetuning-v0.4.gguf` configurado como modelo activo en `config.yaml` y `src/wiki_agent/llm/__init__.py`.
- [x] **Suite de pruebas ampliada**: 28 tests unitarios pasando al 100% en `SAUCE\IA` y `E:\IA`.

### Fase 14: Cola Asíncrona de Mensajes Humanos y UX Concurrente ✅ ← ESTADO ACTUAL
- [x] **Caja de texto siempre activa**: En `chat_room.py`, supresión del bloqueo `disabled` tras el envío para permitir ráfagas de mensajes continuos del usuario.
- [x] **Cola FIFO en agente**: En `chat_session.py`, implementación de `queue.Queue` y worker thread que desacopla la recepción del socket del tiempo de inferencia del LLM.
- [x] **Feedback visual de encolado**: Notificación dinámica del número de mensajes en espera en la barra de estado de la GUI.
- [x] **Auto-recuperación de interfaz**: Comprobación periódica para restaurar el estado editable en caso de reconexiones o respuestas asíncronas.
- [x] **Validación y Pruebas**: 28 tests unitarios pasando en ambos entornos (`SAUCE\IA` y `E:\IA`).
