# Iteración 5: Pipeline de Generación de Datasets de Entrenamiento para IA Local

## 1. Objetivos de la Iteración
- Cerrar el ciclo de auto-mejora del sistema: convertir la base de conocimiento estructurada de la Wiki en material de entrenamiento (Fine-Tuning / LoRA / Ollama) para iteraciones futuras de modelos de IA locales.
- Generar ejemplos sintéticos tanto de **definición conceptual** como de **razonamiento relacional** (preguntas y respuestas sobre cómo interactúan conceptos vinculados y dependencias).
- Facilitar el despliegue inmediato en entornos locales mediante la generación automática de **Modelfiles para Ollama**.

## 2. Formatos Soportados
1. **ShareGPT (sharegpt)**: Formato de conversación multivuelta compatible con herramientas de fine-tuning populares como Axolotl, FastChat y Unsloth.
2. **ChatML / OpenAI (chatml / openai)**: Formato estándar de mensajes {role: system|user|assistant}.
3. **Alpaca (lpaca)**: Formato de pares {instruction, input, output}.
4. **Ollama Modelfile**: Archivo de especificación de modelo local con el grafo conceptual precargado en su SYSTEM prompt.

## 3. Componentes Implementados
- **src/wiki_agent/tools/dataset_exporter.py**:
  - DatasetExporter.export_to_jsonl()
  - DatasetExporter.generate_ollama_modelfile()
- **Comandos CLI**:
  - wiki-agent export --format [sharegpt|alpaca|chatml|openai]
  - wiki-agent modelfile --model llama3.2
- **Herramientas MCP**:
  - wiki_export_training_dataset
  - wiki_generate_ollama_modelfile