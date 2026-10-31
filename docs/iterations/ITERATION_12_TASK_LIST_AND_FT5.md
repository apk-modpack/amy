# Iteración 12: Proceso Cognitivo (Task List), Loop Guard y Pipeline FT5

## Objetivos de la Iteración
1. Implementar la capacidad del agente para descomponer problemas complejos en listas de tareas explícitas (`<tasks>`).
2. Soportar ejecución autónoma paso a paso mediante ciclo cognitivo multi-vuelta guiado por tareas pendientes.
3. Proteger el bucle contra ciclado infinito o bloqueos (`MAX_CYCLES = 8`).
4. Añadir comandos internos de tareas (`/task_add`, `/task_done`, `/task_list`).
5. Generar dataset FT5 (100 ejemplos: 50 respuesta directa + 50 tareas complejas) y dataset maestro acumulativo v5 (500 ejemplos).
6. Implementar conciencia multi-fuente en FT2, FT3 y FT5 (~15-20% remitentes agentes compañeros `[DE: <Agente>]`).

## Componentes Desarrollados
- **`src/wiki_agent/agent/task_list.py`**:
  - `TaskItem`: Entidad que modela la descripción y estado de completitud de cada tarea.
  - `AgentTaskManager`: Gestor de lista de tareas local con métodos `set_tasks`, `add_task`, `complete_task`, `complete_next`, `has_pending_tasks`, `render_summary` y `to_list`.
- **`src/wiki_agent/agent/commands.py`**:
  - `TaskAddCommand`, `TaskDoneCommand`, `TaskListCommand` integrados en el `CommandDispatcher`.
- **`src/wiki_agent/agent/parser.py`**:
  - Extracción de bloques `<tasks>...</tasks>` y reconocimiento de comandos de tarea.
- **`src/wiki_agent/agent/loop.py`**:
  - Integración de `AgentTaskManager` en el agente, control de iteraciones hasta 8 ciclos, continuación mientras existan tareas pendientes y retroalimentación de tareas como observación interna.
- **`generate_ft5_tasklist_dataset.py`**:
  - Generador con 100 ejemplos únicos normalizados al estándar ShareGPT.
- **`tests/test_task_manager.py`**:
  - 4 tests unitarios dedicados al ciclo de vida y parsing de tareas (24 tests totales pasando).

## Datasets
- `dataset_ft5_tasklist.jsonl` (100 ejemplos).
- `dataset_cumulative_v5.jsonl` (500 ejemplos consolidados, FT1..FT5 x 100 ej.).

