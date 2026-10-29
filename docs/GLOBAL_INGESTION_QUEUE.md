# Cola de Ingesta Única y Global del Sistema

> **⚠️ DEPRECADO**: Este módulo fue implementado en la Fase 6 pero actualmente **no se utiliza activamente**.
> El código permanece en el repositorio (`src/wiki_agent/tools/queue.py`) por compatibilidad,
> pero las herramientas MCP asociadas (`wiki_queue_*`) no deben invocarse salvo instrucción explícita del usuario.

## 1. Principio de Centralización (Histórico)
El sistema mantenía **una única cola global centralizada** para todas las categorías, fuentes y disciplinas:
- **Archivo Físico Persistente**: `data/queue/ingest_queue.json`.
- **Página Viva en la Wiki**: [`data/wiki/Sistema/Cola_Global_Ingesta.md`](file:///C:/Users/ENEKO/Desktop/SAUCE/IA/data/wiki/Sistema/Cola_Global_Ingesta.md).

## 2. Ventajas del Modelo de Cola Única (Diseño Original)
1. **Control de Flujo Estricto**: Se procesaba un elemento a la vez (`process_next()`), garantizando que cada concepto estuviera completamente escrito, enlazado e indexado antes de pasar al siguiente.
2. **Priorización Transversal**: Todos los temas competían en un único orden de prioridad global.
3. **Visibilidad en la Propia Wiki**: La tabla Markdown en `Cola_Global_Ingesta.md` mostraba en tiempo real qué se había ingerido y qué estaba pendiente.

## 3. Estado Actual
Este módulo fue reemplazado en la práctica por el flujo directo de gestión de conceptos a través del agente autónomo (bucle ReAct en `agent/loop.py`) y las herramientas MCP estándar (`wiki_save_concept`, `wiki_append_note`).