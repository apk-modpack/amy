# IteraciÃ³n 2: Sistema de DiagnÃ³stico, Salud Conceptual y GeneraciÃ³n de Ãndices (MOC)

## 1. Objetivos de la IteraciÃ³n
- **Garantizar la estabilidad y reparabilidad del sistema**: Proporcionar herramientas automÃ¡ticas para detectar inconsistencias (enlaces rotos, pÃ¡ginas sin backlinks, errores de sintaxis).
- **EstructuraciÃ³n jerÃ¡rquica limpia**: Crear un generador de Ãndices MOC (Map of Content) que agrupe conceptos por categorÃ­a y mantenga un Ãndice Maestro sincronizado.

## 2. Nuevos MÃ³dulos y Capacidades Implementadas
1. **`src/wiki_agent/core/health.py`**:
   - `WikiHealthChecker` & `WikiHealthReport`:
     - Identifica "stubs" (conceptos enlazados con `[[...]]` pero que aÃºn no tienen pÃ¡gina fÃ­sica).
     - Identifica conceptos huÃ©rfanos (pÃ¡ginas a las que nadie referencia).
     - Valida el estado general de la base de conocimientos.
2. **`src/wiki_agent/core/indexer.py`**:
   - `WikiIndexer`:
     - Genera automÃ¡ticamente pÃ¡ginas `Ãndice_<Categoria>.md` con listas actualizadas de conceptos y etiquetas.
     - Genera `Ãndice_Maestro.md` con la taxonomÃ­a general de la Wiki.
3. **Comandos CLI**:
   - `wiki-agent doctor`: Ejecuta el diagnÃ³stico visual en la terminal.
   - `wiki-agent index`: Reconstruye todos los Ã­ndices MOCs.
4. **Nuevas herramientas MCP**:
   - `wiki_diagnose_health`: Para que Antigravity evalÃºe si faltan conceptos por definir.
   - `wiki_rebuild_indexes`: Para que Antigravity organice la base de datos tras ingestas masivas.

## 3. Protocolo de ReparaciÃ³n de Inconsistencias
Si `doctor` reporta enlaces pendientes:
1. El usuario o la IA pueden revisar la lista de stubs faltantes.
2. Crear las pÃ¡ginas faltantes mediante `wiki_save_concept`.
3. Ejecutar `wiki_rebuild_indexes` para consolidar el grafo.