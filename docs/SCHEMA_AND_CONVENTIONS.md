# Esquema de Datos y Convenciones de la Wiki

## 1. Backend de Almacenamiento Activo: `local_xml`

El backend principal del sistema es `local_xml`. Los conceptos se almacenan como ficheros XML con Frontmatter YAML en el directorio `data/wiki/`.

> **Nota:** Existe un backend heredado `local_markdown` en el código, pero no se utiliza activamente.

### Estructura de un Archivo de Concepto XML

Cada página se almacena con la siguiente estructura estandarizada:

```xml
---
title: Nombre del Concepto
category: NombreDeLaCategoria
tags:
  - etiqueta1
  - etiqueta2
aliases:
  - Alias1
  - Sinónimo2
created_at: 2026-08-26T10:00:00Z
updated_at: 2026-08-26T11:30:00Z
source_documents:
  - DocumentoFuente.pdf
  - https://ejemplo.com/articulo
---

<definition>
Resumen o definición ejecutiva del concepto.
</definition>

<sections>
<section title="Características Principales">
- Característica 1 relacionada con [[Otro Concepto]].
- Característica 2 que depende de [[Tercer Concepto]].
</section>
</sections>

<relations>
<relation type="is_a" target="Concepto_Padre"/>
<relation type="part_of" target="Sistema_Mayor"/>
<relation type="depends_on" target="Dependencia"/>
<relation type="relates_to" target="Concepto_Relacionado"/>
</relations>
```

## 2. Convenciones de Carpetas
Por defecto en `data/wiki/`:
- `data/wiki/<Categoria>/<Titulo>.xml`
- Los caracteres no válidos para el sistema de ficheros (`/\:*?"<>|`) se sustituyen por guiones bajos `_`.

## 3. Reglas de Validación
- El `title` en el Frontmatter debe coincidir con el nombre conceptual principal.
- Los enlaces deben ser atómicos y apuntar a conceptos sustantivos.
- Las relaciones semánticas usan los tipos: `is_a`, `part_of`, `relates_to`, `depends_on`.

## 4. Micro-Formato XML del Agente
El agente autónomo (bucle ReAct en `agent/loop.py`) utiliza un micro-formato XML para estructurar sus respuestas:
- `<thought>`: Razonamiento paso a paso (no visible para el usuario final).
- `<response>`: Texto de respuesta al usuario o contenido del concepto a guardar.
- `<commands>`: Comandos CLI a ejecutar (`/search`, `/save`, `/edit`, `/delete`). Vacío cuando es respuesta final.
- `<definition>`, `<sections>`, `<relations>`: Estructura del concepto al usar `/save` o `/edit`.