# Guía Integral de Fine-Tuning y Datasets Acumulativos

Este documento detalla la arquitectura de entrenamiento, la estrategia de especialización por capas (FT1, FT2, FT3) y el pipeline de consolidación en datasets maestros para el **Wiki-Memory AI Agent**.

---

## 1. Filosofía de Entrenamiento: Datasets Acumulativos

En lugar de realizar fusiones de adaptadores LoRA sobre modelos ya cuantizados (GGUF merge), el sistema utiliza una estrategia de **entrenamiento acumulativo desde el modelo base Llama 3.2**:

```
Llama 3.2 (Base) + dataset_cumulative_vN.jsonl (ShareGPT) ──[Unsloth en Colab]──► GGUF Q4_K_M
```

### Principios Fundamentales
1. **Sin degradación por fusión**: Entrenar un único dataset acumulativo preserva la atención y evita colisiones o distorsiones habituales de los merges GGUF.
2. **Modularidad en origen**: Cada habilidad del modelo se aísla y refina en un generador de datos parcial independiente (`generate_ft*.py`).
3. **Reproducibilidad y versionado**: Cada versión del modelo (`v0.1`, `v0.2`, `v0.3`, etc.) se corresponde de manera exacta con una versión del dataset acumulativo (`dataset_cumulative_vN.jsonl`).

---

## 2. Desglose de los Módulos de Fine-Tuning

### FT1: Estándares de Comunicación CLI y Micro-Formato XML
* **Generador:** [`generate_ft1_dataset.py`](file:///C:/Users/ENEKO/Desktop/SAUCE/IA/generate_ft1_dataset.py)
* **Dataset generado:** `data/exports/dataset_ft1_cli_standards.jsonl`
* **Objetivo:** Forzar la estructura de salida y sintaxis base de la memoria.

#### Habilidades entrenadas:
- **Envoltorios de salida estrictos:** Toda respuesta debe componerse de los bloques canónicos:
  ```xml
  <response>
  ... mensaje al usuario ...
  </response>
  <commands>
  ... llamadas a herramientas ...
  </commands>
  ```
- **Catálogo de comandos CLI:** Sintaxis precisa de `/search <termino>`, `/save <XML>`, `/edit <XML>`, `/delete <titulo>`.
- **Micro-formato XML semántico:** Estructuración de conceptos con etiquetas `<definition>`, `<sections>` y relaciones tipadas en `<relations>` (`is_a`, `part_of`, `relates_to`, `depends_on`).

---

### FT2: Razonamiento ReAct Multi-Ciclo (Reasoning + Acting)
* **Generador:** [`generate_agent_dataset.py`](file:///C:/Users/ENEKO/Desktop/SAUCE/IA/generate_agent_dataset.py)
* **Dataset generado:** `data/exports/dataset_ft2_agent_react.jsonl`
* **Objetivo:** Dotar al modelo de capacidad de pensamiento autónomo antes de actuar.

#### Habilidades entrenadas:
- **Etiqueta `<thought>` (Chain-of-Thought):** El modelo explicita su razonamiento interno paso a paso antes de formular la respuesta o los comandos.
- **Ciclo ReAct Multi-Turno:**
  1. *Turno 1:* El usuario hace una pregunta -> El agente razona (`<thought>`) -> Emite una búsqueda en `<commands>`.
  2. *Turno 2:* El motor inyecta el resultado de la búsqueda -> El agente razona con el nuevo contexto -> Emite la respuesta final al usuario.
- **Autonomía selectiva:** Distingue cuándo una pregunta es trivial (saludo, capacidad general) y responde directamente sin invocar comandos innecesarios.

---

### FT3: Patrones Estructurados de Guardado y Corrección de Fallos
* **Generador:** [`generate_ft3_dataset.py`](file:///C:/Users/ENEKO/Desktop/SAUCE/IA/generate_ft3_dataset.py)
* **Dataset generado:** `data/exports/dataset_ft3_structured_saves.jsonl`
* **Objetivo:** Robustez operativa, eliminación de alucinaciones y adhesión a validaciones.

#### Habilidades entrenadas:
- **Patrón limpio de guardado:** No mezclar comentarios conversacionales dentro de `<response>` durante un `/save` o `/edit`. La definición conceptual reside exclusivamente dentro del comando XML.
- **Separación de capas narrativas:** Evita la fuga de etiquetas XML de la base de conocimientos dentro del texto conversacional humano.
- **Eficiencia en memoria:** Evita invocar `/search` si la información ya vino precargada en el bloque de contexto inyectado (`--- MEMORIA WIKI ---`).
- **Recuperación ante rechazo del validador:** Si el backend rechaza una definición XML por errores sintácticos, el modelo analiza el error devuelto y emite una versión corregida en el siguiente ciclo.
- **Uso preciso de `/read` vs `/search`:** Usar `/read` directamente cuando el título exacto del concepto ya es conocido.

---

## 3. Matriz de Versiones de Datasets y Modelos

| Versión Modelo | Dataset Acumulativo | Componentes Integrados | Novedades Clave |
|---|---|---|---|
| **v0.1** | `dataset_cumulative_v1.jsonl` | FT1 | Formato CLI y XML reactivo directo sin `<thought>`. |
| **v0.2** | `dataset_cumulative_v2.jsonl` | FT1 + FT2 | Soporte de bucle ReAct multi-ciclo y pensamiento `<thought>`. |
| **v0.3** | `dataset_cumulative_v3.jsonl` | FT1 + FT2 + FT3 | Guardado limpio, validación de esquemas y recuperación ante fallos. |

---

## 4. Pipeline de Generación y Construcción

Para generar el dataset maestro unificado:

```bash
# Ejecutar la generación completa de todos los parciales y el acumulativo v3
python build_cumulative_dataset.py
```

### Proceso Interno de `CumulativeDatasetBuilder`:
1. **Ejecución secuencial:** Lanza los métodos `main()` de `generate_ft1_dataset.py`, `generate_agent_dataset.py` y `generate_ft3_dataset.py`.
2. **Normalización a ShareGPT:** Convierte todos los esquemas al estándar de conversaciones de OpenAI/ShareGPT.
3. **Deduplicación criptográfica:** Calcula un hash MD5 de cada conversación para evitar redundancias.
4. **Balanceo:** Clasifica los patrones (ReAct vs Comandos directos) y exporta `data/exports/dataset_cumulative_v3.jsonl`.

---

## 5. Entrenamiento en Google Colab con Unsloth

1. **Subida:** Se sube el archivo generado `dataset_cumulative_v3.jsonl` a Google Drive.
2. **Fine-Tuning:** Se entrena con **Unsloth** sobre `meta-llama/Llama-3.2-3B-Instruct` o base, aprovechando optimizaciones de memoria (LoRA/QLoRA).
3. **Cuantización y Exportación:** Se genera la cuantización final a formato GGUF (generalmente `Q4_K_M`, ~2 GB).
4. **Despliegue Local:** El archivo resultante se deposita en `models/` y se enlaza en `config.yaml`.

