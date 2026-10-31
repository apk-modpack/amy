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

### FT1: Estándares de Comunicación CLI y Micro-Formato XML (100 Ejemplos)
* **Generador:** [`generate_ft1_dataset.py`](file:///C:/Users/ENEKO/Desktop/SAUCE/IA/generate_ft1_dataset.py)
* **Dataset generado:** `data/exports/dataset_ft1_cli_standards.jsonl`
* **Objetivo:** Forzar la estructura de salida, comandos canónicos y auto-identificación.

#### Habilidades entrenadas:
- **Envoltorios de salida estrictos:** Toda respuesta debe componerse de los bloques canónicos `<response>` y `<commands>`.
- **Catálogo de comandos CLI:** Sintaxis precisa de `/search <termino>`, `/save <XML>`, `/edit <XML>`, `/delete <titulo>`, `/identify`.
- **Identidad de agente y regla HUMAN:** Verificación de tarjeta de identidad con `/identify` y rechazo estricto del nombre reservado `HUMAN`.
- **Micro-formato XML semántico:** Estructuración de conceptos con etiquetas `<definition>`, `<sections>` y relaciones tipadas en `<relations>`.

---

### FT2: Razonamiento ReAct Multi-Ciclo (Reasoning + Acting) (100 Ejemplos)
* **Generador:** [`generate_agent_dataset.py`](file:///C:/Users/ENEKO/Desktop/SAUCE/IA/generate_agent_dataset.py)
* **Dataset generado:** `data/exports/dataset_ft2_agent_react.jsonl`
* **Objetivo:** Dotar al modelo de capacidad de pensamiento autónomo antes de actuar y discriminación de emisores.

#### Habilidades entrenadas:
- **Etiqueta `<thought>` (Chain-of-Thought):** El modelo explicita su razonamiento interno paso a paso.
- **Ciclo ReAct Multi-Turno:** Pensamiento, búsqueda/lectura intermedia y síntesis final.
- **Conciencia del emisor:** Razona de forma diferenciada si el mensaje proviene de `HUMAN` o de otro agente compañero (`[DE: <Agente>]`).

---

### FT3: Patrones Estructurados de Guardado y Corrección de Fallos (100 Ejemplos)
* **Generador:** [`generate_ft3_dataset.py`](file:///C:/Users/ENEKO/Desktop/SAUCE/IA/generate_ft3_dataset.py)
* **Dataset generado:** `data/exports/dataset_ft3_structured_saves.jsonl`
* **Objetivo:** Robustez operativa, eliminación de alucinaciones y adhesión a validaciones.

#### Habilidades entrenadas:
- **Cero frases de intención:** Prohibición estricta de "Voy a..." o comentarios dentro de `<response>` durante un `/save` o `/edit`.
- **Prohibición de guardado en consultas informativas:** Si el usuario solo pregunta, no se emite `/save` ni `/edit`.
- **Recuperación ante rechazo del validador:** Rectificación inmediata con XML puro tras error del backend.

---

### FT4: Interacción Inter-Agente vs Humano (100 Ejemplos)
* **Generador:** [`generate_ft4_multiagent_dataset.py`](file:///C:/Users/ENEKO/Desktop/SAUCE/IA/generate_ft4_multiagent_dataset.py)
* **Dataset generado:** `data/exports/dataset_ft4_multiagent.jsonl`
* **Objetivo:** Protocolo de red colaborativo, sincronización entre agentes y respeto al rol del operador humano.

#### Habilidades entrenadas:
- **Diferenciación de registro comunicativo:** Respuestas pedagógicas y cercanas para `HUMAN`; respuestas técnicas, precisas y concisas para otros agentes.
- **Sincronización inter-agente:** Peticiones de verificación, intercambio de conceptos y consultas de grafos wiki entre IAs.
- **Presencia y protocolo:** Uso de `/identify`, consulta de participantes con `/agents` y respeto absoluto a la prioridad humana.

---

## 3. Matriz de Versiones de Datasets y Modelos

| Versión Modelo | Dataset Acumulativo | Componentes Integrados | Novedades Clave |
|---|---|---|---|
| **v0.1** | `dataset_cumulative_v1.jsonl` | FT1 (38 ej.) | Formato CLI y XML reactivo directo sin `<thought>`. |
| **v0.2** | `dataset_cumulative_v2.jsonl` | FT1 + FT2 (89 ej.) | Soporte de bucle ReAct multi-ciclo y pensamiento `<thought>`. |
| **v0.3** | `dataset_cumulative_v3.jsonl` | FT1 + FT2 + FT3 (109 ej.) | Guardado limpio, validación de esquemas y recuperación ante fallos. |
| **v0.4** | `dataset_cumulative_v4.jsonl` | FT1 + FT2 + FT3 + FT4 (**400 ej.**) | Simetría de 100 ej. por módulo, multi-agente, /identify y regla HUMAN. (**Activo**) |

---

## 4. Pipeline de Generación y Construcción

Para generar el dataset maestro unificado v4 (400 ejemplos):

```bash
# Ejecutar la generación completa de todos los parciales y el acumulativo v4
python build_cumulative_dataset.py
```

### Proceso Interno de `CumulativeDatasetBuilder`:
1. **Ejecución secuencial:** Lanza los métodos `main()` de `generate_ft1_dataset.py`, `generate_agent_dataset.py`, `generate_ft3_dataset.py` y `generate_ft4_multiagent_dataset.py`.
2. **Normalización a ShareGPT:** Convierte todos los esquemas al estándar de conversaciones de OpenAI/ShareGPT.
3. **Deduplicación criptográfica:** Calcula un hash MD5 de cada conversación para evitar redundancias.
4. **Balanceo:** Clasifica los patrones y exporta `data/exports/dataset_cumulative_v4.jsonl` con exactamente 400 ejemplos balanceados.

---

## 5. Entrenamiento en Google Colab con Unsloth

1. **Subida:** Se sube el archivo generado `dataset_cumulative_v3.jsonl` a Google Drive.
2. **Fine-Tuning:** Se entrena con **Unsloth** sobre `meta-llama/Llama-3.2-3B-Instruct` o base, aprovechando optimizaciones de memoria (LoRA/QLoRA).
3. **Cuantización y Exportación:** Se genera la cuantización final a formato GGUF (generalmente `Q4_K_M`, ~2 GB).
4. **Despliegue Local:** El archivo resultante se deposita en `models/` y se enlaza en `config.yaml`.

