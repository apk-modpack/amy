# Wiki-Memory AI Agent System

Sistema de Agente IA cuya **memoria a largo plazo**, grafo conceptual y base de conocimientos reside en una **Wiki estructurada y configurable** en formato XML.

---

## ¿Qué eres tú aquí? (Para el cliente de Antigravity)

Si estás leyendo esto como agente Antigravity, este README es tu **mapa de entrada** al sistema. Tu rol es actuar como interfaz inteligente sobre una base de conocimientos viva en formato wiki. Las instrucciones de comportamiento detalladas están en `docs/ANTIGRAVITY_SYSTEM_PROMPT.md` y la guía de integración en `docs/ANTIGRAVITY_INTEGRATION_GUIDE.md`.

**Documentación clave que debes conocer:**
| Archivo | Propósito |
|---|---|
| [`docs/ANTIGRAVITY_SYSTEM_PROMPT.md`](docs/ANTIGRAVITY_SYSTEM_PROMPT.md) | Reglas operativas: cuándo y cómo leer/escribir la wiki |
| [`docs/ANTIGRAVITY_INTEGRATION_GUIDE.md`](docs/ANTIGRAVITY_INTEGRATION_GUIDE.md) | Catálogo de herramientas MCP y protocolos de uso |
| [`docs/FINE_TUNING_GUIDE.md`](docs/FINE_TUNING_GUIDE.md) | Guía detallada de fine-tuning: propósitos de FT1, FT2 y FT3 y pipeline acumulativo |
| [`docs/ENVIRONMENTS_AND_SYNC.md`](docs/ENVIRONMENTS_AND_SYNC.md) | Guía de entornos duales (`SAUCE\IA` vs `E:\IA`) y sincronización de código |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Diagrama y descripción de todos los componentes |
| [`docs/VISION_AND_PHILOSOPHY.md`](docs/VISION_AND_PHILOSOPHY.md) | Por qué existe este sistema y qué lo diferencia |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Estado actual de desarrollo y fases completadas |
| [`docs/DATASET_STANDARD.md`](docs/DATASET_STANDARD.md) | Estándar de nombres y flujo de datasets acumulativos |
| [`config.yaml`](config.yaml) | Configuración activa del sistema (backend, LLM, búsqueda) |

---

## Arquitectura en Resumen

```
[Antigravity / CLI / SDK]
         │
         ▼
 WikiKnowledgeManager  ←→  Motor de Búsqueda Híbrida
         │                       │
         ▼                       ▼
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

El backend activo actualmente es **`local_xml`** (ficheros XML en `data/wiki/`). El LLM activo es **Llama 3.2 fine-tuned** cargado directamente vía **llama-cpp-python** (sin necesidad de Ollama), con el archivo `llama3.2-finetuning-v0.3.gguf`.

---

## Estrategia de Fine-Tuning: Dataset Acumulativo

El sistema sigue una estrategia de **datasets acumulativos** para entrenar el modelo:

1. **No se fusionan GGUFs**: Cada versión del modelo se genera desde cero a partir del **modelo base Llama 3.2**.
2. **Datasets parciales**: Cada área de entrenamiento tiene su propio dataset parcial independiente:
   - `dataset_ft1_cli_standards.jsonl` — Estándares de comunicación CLI y micro-formato XML
   - `dataset_ft2_agent_react.jsonl` — Razonamiento ReAct con `<thought>` y herramientas multi-ciclo
3. **Dataset acumulativo**: Se consolidan todos los parciales en un único dataset para entrenar:
   - `dataset_cumulative_v2.jsonl` — FT1 + FT2 fusionado y deduplicado
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
- **CLI Rica y Modular** — Capa de presentación desacoplada (`wiki_agent.ui`) con máquina de estados para streaming (`TokenStreamProcessor`), panel cian minimalista (`ConsoleRenderer`) e `InteractiveChatSession`.
- **Agente Autónomo POO** — Arquitectura orientada a objetos en `wiki_agent.agent` (`WikiAgent`, `AgentResponseParser`, `ConceptXmlExtractor`, `CommandDispatcher`) con bucle ReAct multi-ciclo, razonamiento tenue en vivo (`🧠 Razonando...`) y supresión de intermediarios en Deep Dive.
- **LLM Local (llama-cpp-python)** — Inferencia directa sobre GGUF sin dependencias externas (Ollama opcional)
- **Pipeline de Datasets Acumulativos** — Generación, fusión y versionado de datasets para fine-tuning
- **Fine-Tuning** — Modelo Llama 3.2 entrenado con datasets del sistema vía Unsloth en Google Colab

### ⚠️ Deprecado (No en uso activo)
- **Ingesta de Documentos** — `DocumentIngestor` (PDF, TXT, MD, URLs) — código presente pero no utilizado activamente
- **Cola de Ingesta Persistente** — `IngestionQueueManager` — deprecado
- **Recopilador Web** — `WebCollector` — deprecado

### 🔄 En Progreso / Parcialmente Implementado
- **Búsqueda semántica** — Infraestructura preparada; embeddings locales (ONNX/fastembed) pendientes de integrar

### 📋 Planificado (Futuro)
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

# Usar la CLI interactiva
python -m wiki_agent.cli --help

# Arranque rápido con el script de Windows
.\iniciar_wiki_agent.bat

# Generar dataset acumulativo para fine-tuning
python build_cumulative_dataset.py
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
├── iniciar_wiki_agent.bat           # Script de arranque rápido (Windows)
├── mcp_config.json                  # Configuración MCP para Antigravity
├── pyproject.toml                   # Metadatos del paquete Python
├── data/
│   ├── exports/                     # Datasets generados
│   │   ├── dataset_ft1_cli_standards.jsonl
│   │   ├── dataset_ft2_agent_react.jsonl
│   │   └── dataset_cumulative_v2.jsonl
│   ├── wiki/                        # Base de conocimientos (ficheros XML)
│   └── queue/                       # Cola de ingesta (deprecada)
├── models/
│   ├── llama3.2-finetuning-v0.3.gguf      # Modelo activo (más reciente)
│   └── Modelfile                           # Plantilla Ollama (alternativa)
├── src/wiki_agent/
│   ├── agent/loop.py                # Bucle autónomo ReAct del agente
│   ├── backends/                    # Adaptadores de almacenamiento (local_xml)
│   ├── core/                        # Motor conceptual, búsqueda, salud, indexador
│   ├── llm/                         # Proveedores LLM (llamacpp, ollama)
│   ├── tools/
│   │   ├── dataset_exporter.py      # Exportador wiki → JSONL
│   │   ├── dataset_manager.py       # Fusionador acumulativo de datasets
│   │   ├── autolinker.py            # Auto-enlazado de conceptos
│   │   ├── ingest.py                # Ingesta de documentos (deprecado)
│   │   ├── collector.py             # Scraper web (deprecado)
│   │   ├── queue.py                 # Cola de ingesta (deprecado)
│   │   └── verifier.py              # Verificador de fuentes
│   ├── cli.py                       # CLI interactiva con Rich
│   ├── mcp_server.py                # Servidor MCP
│   └── models.py                    # Modelos Pydantic del dominio
├── docs/                            # Documentación del proyecto
└── tests/                           # Tests del sistema
```