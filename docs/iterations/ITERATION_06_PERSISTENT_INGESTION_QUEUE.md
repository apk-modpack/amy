# IteraciÃ³n 6: Cola de Ingesta Persistente y Procesamiento Gradual por Lotes

## 1. JustificaciÃ³n y Objetivos
- Cuando se solicitan ingestas masivas (ej: "todos los enlaces de fÃ­sica de Wikipedia"), procesar todo de golpe provoca rate-limiting, consumo desmedido de memoria y pÃ©rdida de control sobre errores.
- Se implementa el patrÃ³n **Cola FÃ­sica Persistente (`IngestionQueueManager`)** que guarda el estado de cada tarea en un archivo JSON en disco (`data/queue/ingest_queue.json`).
- Permite procesar de forma gradual: `X` elementos por tanda, hasta vaciar la cola, o con pausas configurables (`--delay`) entre peticiones.

## 2. Componentes Implementados
1. **`src/wiki_agent/tools/queue.py`**:
   - `IngestionQueueItem`: Modelo de datos con `item_id`, `source`, `category`, `status` (`pending`, `processing`, `completed`, `failed`), timestamps y mensajes de error.
   - `IngestionQueueManager`:
     - `add_item()`, `add_batch()`
     - `get_status()`, `list_items()`
     - `process_queue(count, until_empty, delay_seconds, auto_link)`: Ejecuta la ingesta paso a paso, actualizando el archivo fÃ­sico en cada paso.
2. **Comandos CLI**:
   - `wiki-agent queue add <url/fichero> --title <titulo> --category <cat>`
   - `wiki-agent queue status`
   - `wiki-agent queue list [--status pending]`
   - `wiki-agent queue run [--count 5] [--all] [--delay 1.5]`
   - `wiki-agent queue clear`
3. **Herramientas MCP**:
   - `wiki_queue_add_item`
   - `wiki_queue_get_status`
   - `wiki_queue_process_batch`

## 3. GarantÃ­as de Reparabilidad
- Si el proceso se detiene a mitad, el archivo `ingest_queue.json` conserva el estado exacto.
- Al volver a ejecutar `wiki-agent queue run`, continuarÃ¡ a partir del primer elemento pendiente.