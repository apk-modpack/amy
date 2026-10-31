# Wiki-Memory AI Agent System

Sistema de Agente IA cuya **memoria a largo plazo**, grafo conceptual y base de conocimientos reside en una **Wiki estructurada y configurable** en formato XML. Incluye una **Sala de Chat GUI** como interfaz gráfica desacoplada del motor de IA, comunicados por red mediante un protocolo robusto propio.

---

## ¿Qué eres tú aquí? (Para el cliente de Antigravity)

Si estás leyendo esto como agente Antigravity, este README es tu **mapa de entrada** al sistema. Tu rol es actuar como interfaz inteligente sobre una base de conocimientos viva en formato wiki. Las instrucciones de comportamiento detalladas están en `docs/ANTIGRAVITY_SYSTEM_PROMPT.md` y la guía de integración en `docs/ANTIGRAVITY_INTEGRATION_GUIDE.md`.

**Documentación clave que debes conocer:**
| Archivo | Propósito |
|---|---|
| [`docs/ANTIGRAVITY_SYSTEM_PROMPT.md`](docs/ANTIGRAVITY_SYSTEM_PROMPT.md) | Reglas operativas: cuándo y cómo leer/escribir la wiki |
| [`docs/ANTIGRAVITY_INTEGRATION_GUIDE.md`](docs/ANTIGRAVITY_INTEGRATION_GUIDE.md) | Catálogo de herramientas MCP y protocolos de uso |
| [`docs/GIT_REPOSITORY_GUIDE.md`](docs/GIT_REPOSITORY_GUIDE.md) | Guía del repositorio Git, políticas de `.gitignore` y sincronización con GitHub |
| [`docs/FINE_TUNING_GUIDE.md`](docs/FINE_TUNING_GUIDE.md) | Guía detallada de fine-tuning: propósitos de FT1, FT2 y FT3 y pipeline acumulativo |
| [`docs/ENVIRONMENTS_AND_SYNC.md`](docs/ENVIRONMENTS_AND_SYNC.md) | Guía de entornos duales (`SAUCE\IA` vs `E:\IA`) y sincronización de código |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Diagrama y descripción de todos los componentes, incluida la capa de red |
| [`docs/VISION_AND_PHILOSOPHY.md`](docs/VISION_AND_PHILOSOPHY.md) | Por qué existe este sistema y qué lo diferencia |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Estado actual de desarrollo y fases completadas |
| [`docs/DATASET_STANDARD.md`](docs/DATASET_STANDARD.md) | Estándar de nombres y flujo de datasets acumulativos |
| [`CHANGELOG.md`](CHANGELOG.md) | Registro histórico de cambios e hitos por cada iteración del proyecto |
| [`config.yaml`](config.yaml) | Configuración activa del sistema (backend, LLM, búsqueda) |

---

## Arquitectura en Resumen

```
[Usuario]
    │
    ▼
[Sala de Chat GUI]  ──TCP NDJSON──►  [Wiki-Memory Agent]
(chat_room.py)                        │
(Tkinter · sin deps)                  ├── InteractiveChatSession (modo LOCAL o RED)
                                      ├── WikiAgent (bucle ReAct)
                                      │     ├── WikiKnowledgeManager  ←→  Motor Búsqueda Híbrida
                                      │     └── LLM Local (llama-cpp-python / GGUF)
                                      └── LocalXMLBackend (data/wiki/)

[Antigravity / CLI / SDK]
    │
    ▼
WikiKnowledgeManager  ←→  Motor de Búsqueda Híbrida
    │                           │
    ▼                           ▼
LocalXMLBackend         WikiAssistantEngine
(data/wiki/)            (contexto enriquecido + backlinks)
    │
    ▼
Pipelines de Herramientas:
├── DatasetExporter         (wiki → JSONL ShareGPT/Alpaca)
├── CumulativeDatasetBuilder (fusión acumulativa de datasets)
└── generate_ft1_dataset.py  (estándares CLI y micro-formato XML)
    generate_agent_dataset.py (razonamiento ReAct multi-ciclo)
    build_cumulative_dataset.py (orquestador de construcción acumulativa)
```

El backend activo actualmente es **`local_xml`** (ficheros XML en `data/wiki/`). El LLM activo es **Llama 3.2 fine-tuned** cargado directamente vía **llama-cpp-python** (sin necesidad de Ollama), con el archivo `llama3.2-finetuning-v0.4.gguf`.

---

## Modos de Operación

### Modo LOCAL — entrada por teclado (comportamiento original)
El agente funciona en una terminal interactiva. El usuario escribe directamente.

### Modo RED — Sala de Chat GUI
Dos programas separados comunicados por red:

```
[Sala de Chat GUI]  ──────────────────────────  [Agente IA — Terminal]
  Programa 1                TCP :8765              Programa 2
  iniciar_sala_de_chat.bat                         iniciar_agente_modo_red.bat
```

- La **Sala de Chat** (Programa 1) abre una ventana con interfaz gráfica donde el usuario escribe.
- El **Agente IA** (Programa 2) se conecta indicando la IP de la Sala de Chat. Una vez conectado, recibe los mensajes del usuario desde la red, los procesa con toda su lógica interna (wiki, ReAct, LLM) mostrando el progreso en su terminal, y devuelve la respuesta a la Sala de Chat.
- El protocolo de red es **NDJSON sobre TCP puro** (versionado, extensible, sin dependencias externas).

---

## Estrategia de Fine-Tuning: Dataset Acumulativo

El sistema sigue una estrategia de **datasets acumulativos** para entrenar el modelo:

1. **No se fusionan GGUFs**: Cada versión del modelo se genera desde cero a partir del **modelo base Llama 3.2**.
2. **Datasets parciales**: Cada área de entrenamiento tiene su propio dataset parcial independiente:
   - `dataset_ft1_cli_standards.jsonl` — Estándares de comunicación CLI y micro-formato XML
   - `dataset_ft2_agent_react.jsonl` — Razonamiento ReAct con `<thought>` y herramientas multi-ciclo
   - `dataset_ft3_structured_saves.jsonl` — Guardado limpio, validación y recuperación ante fallos
3. **Dataset acumulativo**: Se consolidan todos los parciales en un único dataset para entrenar:
   - `dataset_cumulative_v3.jsonl` — FT1 + FT2 + FT3 fusionado y deduplicado
4. **Entrenamiento en Google Colab** con **Unsloth** sobre el modelo base Llama 3.2.
5. **Exportación** a `.gguf` cuantizado (Q4_K_M, ~2 GB).

Para agregar un nuevo ámbito de entrenamiento: crear un nuevo script `generate_ftN_...py`, ejecutar `build_cumulative_dataset.py` e incrementar la versión acumulativa.

---

## Estado de Desarrollo Actual

El sistema está **completamente funcional** en sus capas core. A continuación el estado real de cada módulo:

### ✅ Implementado y Operativo
- **Motor de Wiki** — Creación, lectura, actualización y borrado de conceptos con Frontmatter YAML y `[[wikilinks]]`
- **Backend XML** — Almacenamiento en `local_xml` (ficheros XML en `data/wiki/`)
- **Grafo de Conocimiento** — Backlinks automáticos, detección de stubs, índices y mapas de contenido (MOC)
- **Servidor MCP** — Conexión nativa con Antigravity a través de `mcp_config.json`
- **Motor de Asistente** — `WikiAssistantEngine` inyecta contexto enriquecido (concepto + citas expandidas + backlinks)
- **Auto-enlazado** — Detección automática de conceptos conocidos en textos nuevos
- **CLI Rica y Modular** — Capa de presentación desacoplada (`wiki_agent.ui`) con streaming, panel cian minimalista e `InteractiveChatSession`
- **Agente Autónomo POO** — Arquitectura orientada a objetos en `wiki_agent.agent` (`WikiAgent`, `AgentResponseParser`, `ConceptXmlExtractor`, `CommandDispatcher`) con bucle ReAct multi-ciclo
- **LLM Local (llama-cpp-python)** — Inferencia directa sobre GGUF sin dependencias externas (Ollama opcional)
- **Pipeline de Datasets Acumulativos** — Generación, fusión y versionado de datasets para fine-tuning
- **Fine-Tuning** — Modelo Llama 3.2 entrenado con datasets del sistema vía Unsloth en Google Colab
- **Capa de Red** — Protocolo NDJSON v1 sobre TCP puro (`wiki_agent.network`): `RobustSocketConnection`, `ChatRoomServer` multi-agente, `AgentNetworkClient`
- **Sala de Chat GUI** — Ventana Tkinter (`chat_room.py`) con tema oscuro, estados de agente en tiempo real (`LISTO`, `PROCESANDO`, `ERROR`), historial coloreado y controles de salida
- **Modo RED en `InteractiveChatSession`** — recepción de inputs desde la Sala de Chat, envío de estados y respuestas de vuelta
- **Identidad Persistente y Multi-Agente** — Módulo `AgentIdentityManager`, generación aleatoria persistente, comando `/identify`, consulta de presencia con `/agents` y regla inmutable de reserva para el rol `HUMAN`
- **Pipeline de Datasets Acumulativos v4** — Generación simétrica de 4 datasets de 100 ejemplos (FT1, FT2, FT3, FT4) consolidados en `dataset_cumulative_v4.jsonl` (400 ejemplos)

### ⚠️ Deprecado (No en uso activo)
- **Ingesta de Documentos** — `DocumentIngestor` (PDF, TXT, MD, URLs) — código presente pero no utilizado activamente
- **Cola de Ingesta Persistente** — `IngestionQueueManager` — deprecado
- **Recopilador Web** — `WebCollector` — deprecado

### 🔄 En Progreso / Parcialmente Implementado
- **Búsqueda semántica** — Infraestructura preparada; embeddings locales (ONNX/fastembed) pendientes de integrar

### 📋 Planificado (Futuro)
- Búsqueda semántica híbrida con embeddings vectoriales locales (ONNX/fastembed)
- Adaptadores para wikis remotas (MediaWiki, Wiki.js, DokuWiki)
- Sincronización bidireccional con Git integrado

Consulta [`docs/ROADMAP.md`](docs/ROADMAP.md) para el detalle completo por fases.

---

## Herramientas MCP Disponibles

Estas son las herramientas que puedes invocar como agente Antigravity:

| Herramienta | Descripción |
|---|---|
| `wiki_search` | Buscar conceptos por texto o etiquetas |
| `wiki_get_context` | Obtener contexto enriquecido (concepto + red de relaciones) |
| `wiki_read_concept` | Leer el contenido completo de un artículo |
| `wiki_save_concept` | Crear o actualizar un artículo con wikilinks |
| `wiki_append_note` | Añadir una nota rápida a un concepto existente |
| `wiki_get_network` | Explorar el grafo de relaciones de un concepto |
| `wiki_list_concepts` | Listar conceptos por categoría |
| `wiki_diagnose_health` | Detectar stubs, enlaces rotos y conceptos huérfanos |
| `wiki_resolve_stub` | Crear esqueleto documentado para un concepto pendiente |
| `wiki_rebuild_indexes` | Regenerar el Índice_Maestro y mapas de contenido |
| `wiki_export_training_dataset` | Exportar la wiki como dataset de entrenamiento |

---

## Inicio Rápido

```bash
# Instalar dependencias (incluye llama-cpp-python para inferencia local)
pip install -e ".[local]"

# Iniciar servidor MCP para Antigravity
python -m wiki_agent.cli mcp

# Usar la CLI interactiva (modo local)
python -m wiki_agent.cli chat

# Modo red: iniciar primero la Sala de Chat, luego el agente
python -m wiki_agent.cli chat-room          # Terminal 1 (o doble-clic en .bat)
python -m wiki_agent.cli chat --connect 127.0.0.1   # Terminal 2
```

**Scripts de arranque rápido (Windows):**
```bat
iniciar_wiki_agent.bat          ← Modo local (teclado)
iniciar_sala_de_chat.bat        ← Sala de Chat GUI (ejecutar primero)
iniciar_agente_modo_red.bat     ← Agente en modo red (ejecutar después)
```

**Configuración del MCP** (ya lista en `mcp_config.json`):
```json
{
  "mcpServers": {
    "wiki-memory": {
      "command": "python",
      "args": ["-m", "wiki_agent.mcp_server"],
      "cwd": "C:/Users/ENEKO/Desktop/SAUCE/IA"
    }
  }
}
```

---

## Estructura del Proyecto

```
IA/
├── config.yaml                      # Configuración del sistema (backend, LLM, búsqueda)
├── build_cumulative_dataset.py      # Orquestador de dataset acumulativo
├── generate_ft1_dataset.py          # Generador de FT1: estándares CLI
├── generate_agent_dataset.py        # Generador de FT2: razonamiento ReAct
├── generate_ft3_dataset.py          # Generador de FT3: guardado estructurado
├── iniciar_wiki_agent.bat           # Script de arranque modo local (Windows)
├── iniciar_sala_de_chat.bat         # Script de arranque Sala de Chat GUI (Windows)
├── iniciar_agente_modo_red.bat      # Script de arranque Agente modo red (Windows)
├── mcp_config.json                  # Configuración MCP para Antigravity
├── pyproject.toml                   # Metadatos del paquete Python
├── data/
│   ├── exports/                     # Datasets generados
│   │   ├── dataset_ft1_cli_standards.jsonl
│   │   ├── dataset_ft2_agent_react.jsonl
│   │   ├── dataset_ft3_structured_saves.jsonl
│   │   └── dataset_cumulative_v3.jsonl
│   ├── wiki/                        # Base de conocimientos (ficheros XML)
│   └── queue/                       # Cola de ingesta (deprecada)
├── models/
│   ├── llama3.2-finetuning-v0.4.gguf      # Modelo activo (más reciente)
│   └── Modelfile                           # Plantilla Ollama (alternativa)
├── src/wiki_agent/
│   ├── agent/loop.py                # Bucle autónomo ReAct del agente
│   ├── backends/                    # Adaptadores de almacenamiento (local_xml)
│   ├── core/                        # Motor conceptual, búsqueda, salud, indexador
│   ├── llm/                         # Proveedores LLM (llamacpp, ollama)
│   ├── network/                     # ← NUEVO: capa de red cliente-servidor
│   │   ├── protocol.py              # Protocolo NDJSON v1 (tipos, versión, constructores)
│   │   ├── connection.py            # RobustSocketConnection (búfer anti-fragmentación TCP)
│   │   ├── server.py                # ChatRoomServer (servidor TCP con callbacks)
│   │   └── client.py                # AgentNetworkClient (cliente TCP para el agente)
│   ├── tools/
│   │   ├── dataset_exporter.py      # Exportador wiki → JSONL
│   │   ├── dataset_manager.py       # Fusionador acumulativo de datasets
│   │   ├── autolinker.py            # Auto-enlazado de conceptos
│   │   ├── ingest.py                # Ingesta de documentos (deprecado)
│   │   ├── collector.py             # Scraper web (deprecado)
│   │   ├── queue.py                 # Cola de ingesta (deprecado)
│   │   └── verifier.py              # Verificador de fuentes
│   ├── ui/
│   │   ├── chat_session.py          # InteractiveChatSession (modo LOCAL y NETWORK)
│   │   ├── renderer.py              # ConsoleRenderer
│   │   └── stream_processor.py      # TokenStreamProcessor
│   ├── chat_room.py                 # ← NUEVO: Sala de Chat GUI (Tkinter)
│   ├── cli.py                       # CLI interactiva con Rich
│   ├── mcp_server.py                # Servidor MCP
│   └── models.py                    # Modelos Pydantic del dominio
├── docs/                            # Documentación del proyecto
│   ├── iterations/                  # Documentos de iteración por fase
│   └── ...
└── tests/                           # Tests del sistema
    ├── test_network.py              # ← NUEVO: tests de red (4 tests)
    └── ...
```
