# Guía del Repositorio Git y Flujo de Trabajo en GitHub

Este documento describe la estructura, políticas de exclusión y flujo de trabajo para el repositorio Git del proyecto **Wiki-Memory AI Agent System (amy)**.

---

## 1. Información General del Repositorio

* **URL Remota:** `https://github.com/apk-modpack/amy.git`
* **Rama Principal:** `main`
* **Visibilidad:** Pública
* **Propósito:** Control de versiones del código fuente, documentación técnica, pruebas y generadores de datos de entrenamiento para el agente de IA.

---

## 2. Política de Archivos y Exclusiones (`.gitignore`)

Para mantener el repositorio ágil, seguro y por debajo de los límites de cuota de GitHub, se han establecido reglas estrictas de exclusión:

### Archivos Rastreados (En el Repositorio):
- **Código Fuente (`src/`):** Toda la lógica del sistema (`core`, `agent`, `ui`, `llm`, `backends`, `tools`).
- **Generadores de Datasets:** `generate_ft1_dataset.py`, `generate_agent_dataset.py`, `generate_ft3_dataset.py`, `build_cumulative_dataset.py`.
- **Documentación Técnica (`docs/` y `README.md`):** Arquitectura, guías de fine-tuning, especificaciones MCP y roadmap.
- **Configuraciones de Entorno:** `config.yaml`, `pyproject.toml`, `mcp_config.json`, plantillas `Modelfile`.
- **Estructura Base de Memoria:** Esquemas base y archivos estructurales XML limpios en `data/wiki/`.

### Archivos Ignorados (Excluidos):
- ⛔ **Modelos Binarios GGUF (`models/*.gguf`):** Archivos de gran tamaño (~2 GB por modelo) que se gestionan localmente o mediante almacenamiento externo.
- ⛔ **Binarios y Bibliotecas Compiladas (`bin/`):** Servidores locales como `llama-server.exe`, CUDA DLLs y ROCm DLLs.
- ⛔ **Exports Masivos (`data/exports/`):** Archivos JSONL generados para entrenamiento que se transfieren directamente a Google Colab / Google Drive.
- ⛔ **Entornos Virtuales y Caches (`venv/`, `__pycache__/`, `.pytest_cache/`).**
- ⛔ **Registros de Ejecución (`*.log`, `latest_*.txt`).**

---

## 3. Protocolo de Trabajo y Sincronización

El flujo de trabajo combina el versionado con Git y la réplica con el entorno de pruebas local:

```
                  ┌──────────────────────────────────────────────┐
                  │          Repositorio Remoto GitHub           │
                  │     https://github.com/apk-modpack/amy       │
                  └──────────────────────▲───────────────────────┘
                                         │ git push / git pull
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ Entorno de Desarrollo (Local)                │
                  │ C:\Users\ENEKO\Desktop\SAUCE\IA              │
                  └──────────────────────┬───────────────────────┘
                                         │ Sincronización local
                                         │ (Robocopy / PowerShell)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │ Entorno de Pruebas con Datos Reales          │
                  │ E:\IA                                        │
                  └──────────────────────────────────────────────┘
```

### Comandos Frecuentes

#### 1. Comprobar estado de los cambios
```bash
git status
```

#### 2. Confirmar y subir cambios a GitHub
```bash
# Añadir cambios (respetando las exclusiones de .gitignore)
git add .

# Crear commit descriptivo (usando estándar Conventional Commits)
git commit -m "feat: descripcion del cambio"

# Enviar cambios a la rama principal
git push origin main
```

#### 3. Actualizar el entorno local con cambios remotos
```bash
git pull origin main
```

---

## 4. Replicación al Entorno de Pruebas (`E:\IA`)

Recuerda que tras hacer cambios y confirmar en Git en el entorno de desarrollo, se deben sincronizar los archivos de código fuente y documentación con el entorno de pruebas `E:\IA` siguiendo la [Guía de Entornos](file:///C:/Users/ENEKO/Desktop/SAUCE/IA/docs/ENVIRONMENTS_AND_SYNC.md).
