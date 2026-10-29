# Iteración 7: Fine-Tuning y Despliegue del Modelo Local

**Estado**: ✅ Completada

## Objetivos
- Ejecutar el primer fine-tuning (FT1) de Llama 3.2 con los estándares de comunicación CLI del sistema.
- Exportar el modelo entrenado a formato GGUF cuantizado.
- Integrar un proveedor LLM local que cargue el GGUF directamente sin dependencias externas.
- Configurar el sistema para usar el modelo fine-tuned como LLM activo.

## Resultados
- **FT1 completado**: Modelo entrenado con estándares de comunicación CLI y micro-formato XML (`<response>`, `<commands>`).
- **Proveedor `llamacpp`**: Implementado en `src/wiki_agent/llm/llamacpp.py` — carga directa de GGUF vía `llama-cpp-python`.
- **Proveedor `ollama`**: Disponible como alternativa en `src/wiki_agent/llm/ollama.py`.
- **Modelo exportado**: `llama3.2-finetuning2.gguf` (Q4_K_M, ~2 GB).
- **Configuración**: `config.yaml` actualizado con `provider: llamacpp` y `model_path` apuntando al GGUF.

## Archivos Creados/Modificados
- `src/wiki_agent/llm/llamacpp.py` (nuevo)
- `src/wiki_agent/llm/ollama.py` (nuevo)
- `src/wiki_agent/llm/base.py` (nuevo)
- `src/wiki_agent/llm/__init__.py` (nuevo)
- `config.yaml` (actualizado con sección `llm`)
- `models/Modelfile` (plantilla Ollama)
