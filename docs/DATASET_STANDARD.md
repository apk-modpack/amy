# Estándar de Datasets para Fine-Tuning

## 1. Estrategia: Entrenamiento Acumulativo desde Base

El sistema **NO fusiona archivos GGUF** entre sí. En su lugar, cada versión del modelo se entrena desde cero a partir del **modelo base Llama 3.2** utilizando un **dataset acumulativo** que incluye todos los ámbitos de entrenamiento necesarios.

```
Llama 3.2 (Base) + dataset_cumulative_vN.jsonl → llama3.2-finetuning-*.gguf
```

### Ventajas
- **Coherencia total**: El modelo resultante aprende todo de forma unificada, sin artefactos de fusión.
- **Reproducibilidad**: Cualquier versión del modelo puede regenerarse con el dataset acumulativo correspondiente.
- **Extensibilidad**: Para añadir un nuevo ámbito, basta con crear un nuevo generador `generate_ftN_*.py` y ejecutar `build_cumulative_dataset.py`.

## 2. Estándar de Nombres de Archivos

### Datasets Parciales (un ámbito específico)
```
dataset_ft{N}_{nombre_descriptivo}.jsonl
```

| Archivo | Descripción | Generador |
|---------|-------------|-----------|
| `dataset_ft1_cli_standards.jsonl` | Estándares de comunicación CLI, micro-formato XML y auto-identificación (100 ej.) | `generate_ft1_dataset.py` |
| `dataset_ft2_agent_react.jsonl` | Razonamiento ReAct con `<thought>`, herramientas y conciencia de emisor (100 ej.) | `generate_agent_dataset.py` |
| `dataset_ft3_structured_saves.jsonl` | Patrones limpios de /save y /edit, cero frases de intención, recuperación tras rechazo (100 ej.) | `generate_ft3_dataset.py` |
| `dataset_ft4_multiagent.jsonl` | Protocolo inter-agente vs humano, sincronización y respeto al rol HUMAN (100 ej.) | `generate_ft4_multiagent_dataset.py` |
| `dataset_ft5_tasklist.jsonl` | Proceso cognitivo: respuesta directa vs planificación estructurada con `<tasks>` y `/task_*` (100 ej.) | `generate_ft5_tasklist_dataset.py` |
| `dataset_ft6_wiki_grounding.jsonl` | Wiki-Grounding: desconfianza de memoria paramétrica, offloading de contexto y navegación en grafo (100 ej.) | `generate_ft6_wiki_grounding_dataset.py` |

### Datasets Acumulativos (para entrenar)
```
dataset_cumulative_v{N}.jsonl
```

| Archivo | Contenido | Versión |
|---------|-----------|---------|
| `dataset_cumulative_v2.jsonl` | FT1 + FT2 fusionado y deduplicado | Histórico |
| `dataset_cumulative_v3.jsonl` | FT1 + FT2 + FT3 fusionado | Histórico |
| `dataset_cumulative_v4.jsonl` | FT1 + FT2 + FT3 + FT4 (400 ejemplos balanceados) | Histórico |
| `dataset_cumulative_v5.jsonl` | FT1 + FT2 + FT3 + FT4 + FT5 (500 ejemplos balanceados) | Anterior |
| `dataset_cumulative_v6.jsonl` | FT1 + FT2 + FT3 + FT4 + FT5 + FT6 (600 ejemplos balanceados) | **Actual** |

### Modelos Resultantes
```
llama3.2-{identificador}.gguf
```

| Archivo | Origen |
|---------|--------|
| `llama3.2-finetuning-unificado.gguf` | Entrenado con `dataset_cumulative_v2.jsonl` |
| `llama3.2-cumulative_v3.gguf` | Entrenado con `dataset_cumulative_v3.jsonl` |
| `llama3.2-cumulative_v4.gguf` | Entrenado con `dataset_cumulative_v4.jsonl` |
| `llama3.2-cumulative_v5.gguf` | Entrenado con `dataset_cumulative_v5.jsonl` |
| `llama3.2-cumulative_v6.gguf` | **Próxima versión** — entrenar con `dataset_cumulative_v6.jsonl` |

## 3. Formato Canónico: ShareGPT

Todos los datasets se normalizan al formato **ShareGPT** para compatibilidad con Unsloth y otros frameworks de fine-tuning:

```json
{
  "conversations": [
    {"from": "system", "value": "<MODO: AGENTE>"},
    {"from": "human", "value": "Pregunta del usuario"},
    {"from": "gpt", "value": "<thought>...</thought>\n<response>...</response>\n<commands>...</commands>"}
  ]
}
```

El módulo `CumulativeDatasetBuilder` (`src/wiki_agent/tools/dataset_manager.py`) también acepta y normaliza automáticamente desde:
- Formato OpenAI / Messages (`{"messages": [{"role": "...", "content": "..."}]}`)
- Formato Alpaca (`{"instruction": "...", "input": "...", "output": "..."}`)

## 4. Flujo de Generación

```bash
# Generar todo (parciales + acumulativo) de una sola vez
python build_cumulative_dataset.py

# Especificar nombre de salida y añadir datasets adicionales
python build_cumulative_dataset.py --output dataset_cumulative_v3.jsonl --add-file nuevo.jsonl
```

### Pasos internos del orquestador:
1. Ejecuta `generate_ft1_dataset.main()` → genera `dataset_ft1_cli_standards.jsonl`
2. Ejecuta `generate_agent_dataset.main()` → genera `dataset_ft2_agent_react.jsonl`
3. Ejecuta `generate_ft3_dataset.main()` → genera `dataset_ft3_structured_saves.jsonl`
4. Incorpora archivos adicionales (si se pasan con `--add-file`)
5. `CumulativeDatasetBuilder.merge_datasets()`:
   - Normaliza todos los formatos a ShareGPT
   - Deduplica por hash MD5 del contenido
   - Clasifica por categoría (ReAct vs CLI)
   - Genera el archivo acumulativo final

## 5. Entrenamiento en Google Colab

El entrenamiento se realiza en Google Colab con **Unsloth** (stack optimizado para fine-tuning eficiente):

1. Subir `dataset_cumulative_vN.jsonl` a Google Drive (`/finetuning/`)
2. Ejecutar el notebook de Colab con las celdas de Unsloth
3. El resultado es un `.gguf` cuantizado (Q4_K_M, ~2 GB)
4. Descargar y colocar en `models/`
5. Actualizar `config.yaml` → `llm.model_path` con la nueva ruta

## 6. Cómo Añadir un Nuevo Ámbito de Entrenamiento

1. Crear `generate_ft{N}_{nombre}.py` siguiendo la estructura de los generadores existentes.
2. Registrar su invocación en `build_cumulative_dataset.py`.
3. Ejecutar `python build_cumulative_dataset.py --output dataset_cumulative_v{N+1}.jsonl`.
4. Subir a Colab, entrenar y desplegar.
