# Visión y Filosofía: Wiki como Memoria a Largo Plazo de la IA

## 1. El Problema de la Memoria Tradicional en LLMs
Los sistemas de memoria convencionales para agentes IA (como almacenes puramente basados en vectores / RAG ingenuo) presentan problemas críticos:
1. **Falta de estructura conceptual**: Los fragmentos recuperados por similitud vectorial a menudo carecen de contexto jerárquico, relaciones causales o taxonomía.
2. **Opacidad y difícil edición**: Es difícil para el usuario humano inspeccionar, corregir o enriquecer directamente los "vectores" de conocimiento del agente.
3. **Pérdida de relaciones bidireccionales**: Un vector no comprende de forma explícita que el concepto `A` está enlazado a `B` y que `B` es parte de `C`.

## 2. La Solución: Memoria Basada en Wiki (Wiki-as-Memory)
Este proyecto adopta un enfoque radicalmente diferente:
- **La Wiki como Grafo Vivo de Conocimiento**: Toda la información que el agente aprende, procesa o extrae se sintetiza en artículos XML interconectados mediante enlaces tipo wiki (`[[Concepto]]`) y metadatos estructurados (Frontmatter YAML).
- **Legibilidad Dual (Humano + Máquina)**: La base de conocimientos es 100% legible y editable tanto por el usuario (en un editor de texto, VSCode, o visor web) como por el agente.
- **Navegación Relacional y Backlinks**: El agente no solo busca texto, sino que navega por el grafo: si consulta el concepto `Transformers`, automáticamente sabe qué páginas lo citan (backlinks) y a qué páginas enlaza (enlaces salientes).
- **Ciclo de Auto-Mejora y Fine-Tuning**: La wiki y los datasets del sistema alimentan un pipeline de entrenamiento acumulativo que perfecciona continuamente el modelo local.

## 3. Principios de Diseño
- **Independencia del LLM**: Diseñado hoy para Antigravity y Llama 3.2, pero desacoplado para operar con cualquier modelo o agente futuro. El proveedor de LLM es configurable (`llamacpp`, `ollama`, o futuros).
- **Configurabilidad de Almacenamiento**: Backend activo `local_xml` para ficheros XML locales, con soporte heredado para Markdown y adaptadores futuros para Wikis remotas.
- **Estructuración Activa**: La IA no almacena texto en bruto; sintetiza, categoriza, enlaza conceptos clave y actualiza notas existentes.
- **Autonomía Cognitiva**: El agente opera con un bucle ReAct (`<thought>` → `<response>` → `<commands>`) que le permite razonar, buscar información y ejecutar acciones de forma autónoma antes de responder al usuario.
- **Entrenamiento Acumulativo**: Cada iteración de fine-tuning parte del modelo base (Llama 3.2) con un dataset acumulativo que incorpora todos los ámbitos de conocimiento previos más los nuevos, garantizando coherencia total.