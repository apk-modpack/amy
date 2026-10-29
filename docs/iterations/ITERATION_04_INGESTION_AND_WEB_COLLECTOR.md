# IteraciÃ³n 4: Pipeline de Ingesta Inteligente de Documentos y RecopilaciÃ³n Web

## 1. Objetivos de la IteraciÃ³n
- Incorporar capacidades para alimentar la memoria Wiki desde archivos locales y fuentes web externas.
- Implementar el motor de **Auto-enlazado Conceptual (`AutoLinker`)** que analiza el texto nuevo y aÃ±ade automÃ¡ticamente enlaces `[[Concepto Existente]]` sin alterar bloques de cÃ³digo ni duplicar enlaces previos.
- Permitir la segmentaciÃ³n de documentos extensos por encabezados temÃ¡ticos (`##`).

## 2. Componentes Implementados
1. **`src/wiki_agent/tools/autolinker.py`**:
   - `AutoLinker.apply_links(text)`:
     - Protege bloques de cÃ³digo y enlaces ya existentes.
     - Detecta nombres de conceptos conocidos ordenados por longitud descendente para evitar colisiones parciales.
     - Transforma menciones en enlaces wiki navegables.
2. **`src/wiki_agent/tools/ingest.py`**:
   - `DocumentIngestor.ingest_file()`: Ingesta archivos `.txt`, `.md`, etc. con opciÃ³n de segmentaciÃ³n por secciones.
3. **`src/wiki_agent/tools/collector.py`**:
   - `WebCollector.fetch_url()`: Scraper HTTP con limpieza de DOM (elimina `<script>`, `<style>`, navegaciones) y pasa el contenido por el `AutoLinker`.
4. **Nuevos comandos CLI y herramientas MCP**:
   - CLI: `wiki-agent ingest <ruta_fichero> [--split]`, `wiki-agent collect-url <url>`.
   - MCP: `wiki_collect_url` y `wiki_ingest_text` con soporte `auto_link`.