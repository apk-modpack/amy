# Iteración 8: Datasets Acumulativos y Agente ReAct

**Estado**: ✅ Completada

## Objetivos
- Adoptar una estrategia de **datasets acumulativos** para entrenar siempre desde el modelo base Llama 3.2 (en lugar de intentar fusionar GGUFs).
- Establecer un **estándar de nombres** claro para datasets parciales y acumulativos.
- Reconstruir el dataset FT1 (perdido) y consolidarlo con FT2 en un dataset acumulativo.
- Implementar el **agente autónomo con bucle ReAct** (razonamiento `<thought>`, ejecución multi-ciclo).
- Crear herramientas de fusión, deduplicación y versionado de datasets.

## Decisiones de Diseño Clave

### ¿Por qué datasets acumulativos y no fusión de GGUFs?
Se intentó fusionar modelos GGUF ya entrenados, pero la operación resultó técnicamente inviable:
- Los GGUFs cuantizados no se pueden fusionar directamente por tensor.
- La desquantización a FP16 para fusionar consumía más de 12 GB de RAM, superando los límites de Google Colab gratuito.
- La fusión producía artefactos y pérdida de calidad.

**Solución adoptada**: Mantener un dataset acumulativo que crece con cada nuevo ámbito de entrenamiento, y reentrenar siempre desde la base.

### Estándar de nombres
- Parciales: `dataset_ft{N}_{nombre_descriptivo}.jsonl`
- Acumulativos: `dataset_cumulative_v{N}.jsonl`
- Modelos: `llama3.2-{identificador}.gguf`

## Resultados
- **`generate_ft1_dataset.py`**: Reconstrucción del dataset FT1 con estándares CLI y micro-formato XML reactivo.
- **`generate_agent_dataset.py`**: Dataset FT2 con razonamiento ReAct, `<thought>` y herramientas multi-ciclo.
- **`build_cumulative_dataset.py`**: Orquestador que genera parciales y fusiona en acumulativo.
- **`CumulativeDatasetBuilder`** (`tools/dataset_manager.py`): Normalización ShareGPT, deduplicación MD5, métricas.
- **`dataset_cumulative_v2.jsonl`**: Dataset acumulativo actual (FT1 + FT2).
- **`llama3.2-finetuning-unificado.gguf`**: Modelo activo, entrenado con Unsloth en Colab.
- **Bucle ReAct** (`agent/loop.py`): Agente autónomo con `<thought>` → `<response>` → `<commands>`.

## Archivos Creados/Modificados
- `generate_ft1_dataset.py` (nuevo)
- `build_cumulative_dataset.py` (nuevo)
- `src/wiki_agent/tools/dataset_manager.py` (nuevo)
- `generate_agent_dataset.py` (actualizado)
- `src/wiki_agent/agent/loop.py` (actualizado con ReAct)
- `config.yaml` (actualizado: model_path → llama3.2-finetuning-unificado.gguf)
- `models/Modelfile` (actualizado: FROM llama3.2-finetuning-unificado.gguf)
- `data/exports/dataset_ft1_cli_standards.jsonl` (generado)
- `data/exports/dataset_ft2_agent_react.jsonl` (generado)
- `data/exports/dataset_cumulative_v2.jsonl` (generado)
- `docs/DATASET_STANDARD.md` (nuevo)

## Documentación
Ver [`docs/DATASET_STANDARD.md`](../DATASET_STANDARD.md) para el estándar completo de nombres y flujo de datasets.
