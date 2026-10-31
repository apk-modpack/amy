# Iteración 13: Wiki-Grounding, Menor Dependencia de Contexto y Pipeline FT6

## Objetivos de la Iteración
1. Desacoplar al agente de la memoria interna paramétrica y de la alucinación, forzando la verificación previa en la wiki local.
2. Fomentar la persistencia proactiva (context-to-wiki offloading): cuando se comparte información nueva o reglas en el chat, descargarla a la wiki con `/save` o `/edit`.
3. Mejorar la comprobación y reconciliación de hechos dudosos o contradictorios contra la verdad almacenada en disco.
4. Estimular la navegación estructurada de enlaces en grafo (`[[Concepto]]`) mediante el comando `/read` en lugar de especular.
5. Crear el generador `generate_ft6_wiki_grounding_dataset.py` (100 ejemplos, 4 bloques x 25 ej., 20% agentes / 80% humanos).
6. Consolidar el dataset maestro acumulativo v6 (`dataset_cumulative_v6.jsonl`) con exactamente 600 ejemplos (FT1..FT6 x 100 ej.).
7. Desplegar y configurar el modelo activo cuantizado `llama3.2-finetuning-v0.4.gguf` en el sistema.

## Componentes Modificados y Desarrollados
- **`generate_ft6_wiki_grounding_dataset.py`**:
  - Bloque 1 (25 ej.): Anti-alucinación / verificación previa con `/search` o `/read`.
  - Bloque 2 (25 ej.): Persistencia proactiva (context offloading) mediante `/save` o `/edit`.
  - Bloque 3 (25 ej.): Reconciliación y contrastación de hechos con la base de conocimientos.
  - Bloque 4 (25 ej.): Exploración guiada de enlaces de grafo wiki (`[[Concepto]]` -> `/read`).
  - Distribución multi-fuente: 20 agentes compañeros (`[DE: <Agente>]`) / 80 humanos (`HUMAN`).
- **`src/wiki_agent/agent/loop.py`**:
  - `SYSTEM_PROMPT` enriquecido con directivas estrictas de wiki-grounding, desconfianza de memoria interna paramétrica, persistencia obligatoria de acuerdos en el chat y seguimiento de enlaces con `/read`.
- **`build_cumulative_dataset.py`**:
  - Incorporación de FT6 y generación automática de `dataset_cumulative_v6.jsonl` (600 ejemplos únicos, 0 duplicados).
- **`config.yaml` y `src/wiki_agent/llm/__init__.py`**:
  - Modelo activo fijado en `./models/llama3.2-finetuning-v0.4.gguf`.
- **`tests/test_wiki_grounding.py`**:
  - 4 nuevos tests unitarios para verificar directivas de prompt, estructura/unicidad de FT6, despacho de `/read` y parsing de comandos de grounding (28 tests totales pasando al 100%).

## Estado de Datasets
- `dataset_ft6_wiki_grounding.jsonl` (100 ejemplos).
- `dataset_cumulative_v6.jsonl` (600 ejemplos consolidados, FT1..FT6 x 100 ej. cada uno).
- Modelo activo: `llama3.2-finetuning-v0.4.gguf`.

