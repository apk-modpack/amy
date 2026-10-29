# Guía de Integración para Antigravity (Wiki-Memory)

Esta guía describe cómo Antigravity debe interactuar con el sistema de memoria en Wiki cuando actúa como asistente o agente principal.

## 1. Protocolo de Consulta de Conocimientos
Cuando el usuario haga preguntas sobre temas técnicos, proyectos o conceptos:
1. **Buscar primero en la Wiki**: Invocar `wiki_search(query)` para identificar si existe información previa almacenada.
2. **Leer el concepto principal**: Invocar `wiki_read_concept(title)` para obtener la definición, contexto, metadatos y notas previas.
3. **Explorar enlaces y contexto**: Consultar `outgoing_links` o `backlinks` para comprender el contexto holístico del concepto.
4. **Responder enriquecido**: Responder al usuario citando la fuente y manteniendo la coherencia con el conocimiento registrado.

## 2. Protocolo de Guardado y Actualización de Conocimiento
Cuando el usuario explique un concepto nuevo, comparta decisiones de diseño o pida memorizar información:
1. **Estructuración**: No guardar texto plano desorganizado. Formatear con títulos, listas claras y enlaces `[[Concepto Relacionado]]`.
2. **Categorización**: Asignar una categoría clara (ej. `Arquitectura`, `Frontend`, `Backend`, `Modelos_IA`, `Ideas`).
3. **Etiquetado**: Incluir tags temáticas relevantes en `tags`.
4. **Actualización vs Creación**:
   - Si el concepto **no existe**: Usar `wiki_save_concept(title, content, category, tags)`.
   - Si el concepto **ya existe**: Usar `wiki_append_note(title, note)` o `wiki_save_concept` para refinar la definición.

## 3. Herramientas Disponibles (Activas)

| Herramienta | Cuándo Usarla |
|-------------|---------------|
| `wiki_search` | Para buscar si existe información sobre un término o pregunta. |
| `wiki_read_concept` | Para leer todo el contenido y relaciones de un artículo concreto. |
| `wiki_get_context` | Para obtener contexto enriquecido con citas expandidas y backlinks. |
| `wiki_save_concept` | Para crear o actualizar un artículo completo con `[[wikilinks]]`. |
| `wiki_append_note` | Para añadir un apunte rápido a un concepto existente. |
| `wiki_get_network` | Para inspeccionar con qué otros conceptos se relaciona un tema. |
| `wiki_list_concepts` | Para explorar qué conceptos existen en una categoría. |
| `wiki_diagnose_health` | Para detectar stubs, enlaces rotos y conceptos huérfanos. |
| `wiki_resolve_stub` | Para crear esqueleto documentado para un concepto pendiente. |
| `wiki_rebuild_indexes` | Para regenerar el Índice_Maestro y mapas de contenido. |
| `wiki_export_training_dataset` | Para volcar la base de conocimientos a un dataset JSONL. |

### Herramientas Deprecadas (presentes pero no en uso activo)
| Herramienta | Estado |
|-------------|--------|
| `wiki_ingest_text` | ⚠️ Deprecada — No utilizar salvo instrucción explícita. |
| `wiki_queue_add_item` | ⚠️ Deprecada — Cola de ingesta no activa. |
| `wiki_queue_get_status` | ⚠️ Deprecada — Cola de ingesta no activa. |
| `wiki_queue_process_batch` | ⚠️ Deprecada — Cola de ingesta no activa. |

## 4. Convenciones de Enlaces
- Usar siempre doble corchete: `[[Nombre Del Concepto]]`.
- Mantener nombres de conceptos en formato legible (ej. `[[Redes Neuronales]]`, `[[Servidor MCP]]`).
- Si un concepto enlazado aún no tiene página propia, se considera un nodo pendiente ("stub") que podrá crearse en el futuro.

## 5. Backend de Almacenamiento
El sistema utiliza el backend `local_xml` como formato principal. Los conceptos se almacenan como ficheros XML con Frontmatter YAML en `data/wiki/<Categoria>/<Titulo>.xml`.