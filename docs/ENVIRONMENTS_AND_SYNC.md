# Manual de Entornos del Sistema y Guía de Sincronización

Este documento describe la topología de dos entornos del proyecto, sus roles específicos y el protocolo estricto para sincronizar código sin alterar los datos de prueba.

---

## 1. Topología de Entornos

El sistema opera bajo dos instancias físicas diferenciadas:

```
┌──────────────────────────────────────────────┐
│  Entorno 1: Desarrollo Limpio                │
│  Ruta: C:\Users\ENEKO\Desktop\SAUCE\IA       │
│  Rol: Desarrollo activo de código fuente,   │
│       refactorizaciones y nuevos generadores.│
└──────────────────────┬───────────────────────┘
                       │ Sincronización unidireccional
                       │ de código (sin sobreescribir datos)
                       ▼
┌──────────────────────────────────────────────┐
│  Entorno 2: Pruebas y Memoria Real          │
│  Ruta: E:\IA                                 │
│  Rol: Pruebas de integración, ejecución     │
│       con base de conocimiento poblada,      │
│       logs y memoria acumulada.              │
└──────────────────────────────────────────────┘
```

---

## 2. Diferenciación de Contenidos

| Componente / Directorio | Entorno de Desarrollo (`SAUCE\IA`) | Entorno de Pruebas (`E:\IA`) | Regla de Sincronización |
|---|---|---|---|
| `src/` | Código fuente maestro | Réplica exacta para ejecución | **Se sincroniza siempre** tras modificaciones |
| `tests/` | Suites de pruebas unitarias | Réplica para tests locales | **Se sincroniza siempre** |
| `config.yaml` | Configuración base / desarrollo | Configuración adaptada a pruebas | **Se sincroniza con precaución** (ver rutas de modelos) |
| `README.md`, `docs/` | Documentación actualizada | Documentación sincronizada | **Se sincroniza siempre** |
| `data/wiki/` | Wiki limpia / plantilla inicial | **Wiki real** poblada de conceptos | ⛔ **PROHIBIDO SOBREESCRIBIR** |
| `data/exports/` | Salidas de compilación local | Salidas históricas de datos | ⛔ No sobreescribir exports de prueba |
| `models/` | Binarios GGUF activos | Binarios GGUF disponibles | Se actualiza cuando hay un modelo nuevo |
| `logs/`, `latest_*.log` | Registros locales | Registros de sesiones de prueba | ⛔ Conservar en su propio entorno |

---

## 3. Protocolo de Sincronización

Cada vez que se introduzcan cambios en la lógica del agente, herramientas o generadores en `C:\Users\ENEKO\Desktop\SAUCE\IA`, deben replicarse a `E:\IA`.

### Comando de Sincronización de Código (PowerShell / Robocopy)

```powershell
# Sincronizar código fuente sin tocar temporales
robocopy "C:\Users\ENEKO\Desktop\SAUCE\IA\src" "E:\IA\src" /E /XO /XD "__pycache__" ".pytest_cache"

# Sincronizar generadores raíz y configuración principal
Copy-Item "C:\Users\ENEKO\Desktop\SAUCE\IA\config.yaml" "E:\IA\config.yaml" -Force
Copy-Item "C:\Users\ENEKO\Desktop\SAUCE\IA\build_cumulative_dataset.py" "E:\IA\build_cumulative_dataset.py" -Force
Copy-Item "C:\Users\ENEKO\Desktop\SAUCE\IA\generate_*.py" "E:\IA\" -Force

# Sincronizar documentación
robocopy "C:\Users\ENEKO\Desktop\SAUCE\IA\docs" "E:\IA\docs" /E /XO
Copy-Item "C:\Users\ENEKO\Desktop\SAUCE\IA\README.md" "E:\IA\README.md" -Force
```

---

## 4. Gestión de Nuevas Versiones de Modelos GGUF

Cuando se genera un nuevo `.gguf` cuantizado:
1. Depositar el archivo en `models/` del entorno de desarrollo.
2. Copiarlo a `E:\IA\models/`.
3. Actualizar la clave `llm.model_path` en `config.yaml` de ambos entornos.
4. Actualizar la ruta por defecto en [`src/wiki_agent/llm/__init__.py`](file:///C:/Users/ENEKO/Desktop/SAUCE/IA/src/wiki_agent/llm/__init__.py).

