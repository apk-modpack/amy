# Iteración 10: Arquitectura Cliente-Servidor — Sala de Chat GUI + Modo Red

## Resumen Ejecutivo

En esta iteración se separó el sistema en **dos programas independientes** comunicados por red, dando respuesta a la necesidad de disponer de una interfaz gráfica de chat desacoplada del motor de IA. La Sala de Chat actúa como **servidor** con interfaz Tkinter, mientras que el Agente IA actúa como **cliente** que se conecta a ella. El agente mantiene su interfaz de terminal completa y puede operar igualmente en modo local (teclado) sin ningún cambio.

---

## Objetivos Alcanzados

### 1. Protocolo de Red Robusto y Extensible (`src/wiki_agent/network/`)
- **NDJSON sobre TCP puro** (Newline-Delimited JSON): sin frameworks externos, reimplementable en cualquier lenguaje.
- **Versionado explícito** (`"version": 1` en cada mensaje): permite detectar incompatibilidades y añadir campos sin romper clientes existentes.
- **`RobustSocketConnection`** con búfer acumulativo de líneas: resuelve de forma transparente la fragmentación TCP (packet sticking y splitting).
- **`send_lock` thread-safe**: permite envíos desde múltiples hilos sin corrupción de frames.
- **Tipos de mensajes estructurados**: `handshake`, `handshake_ack`, `chat_message`, `agent_status`, `agent_response`, `ping/pong`, `disconnect`, `error`.

### 2. Sala de Chat GUI (`src/wiki_agent/chat_room.py`)
- Ventana Tkinter con **tema oscuro** (paleta Catppuccin Mocha) sin dependencias externas — tkinter es estándar en toda instalación de Python.
- Historial de mensajes con **etiquetas de color** diferenciadas: usuario (verde), IA (azul), sistema (gris), metadatos (morado).
- **Barra de estado en tiempo real** de la IA: iconos e indicadores de `🧠 Pensando…`, `🔍 Buscando…`, `📖 Leyendo…`, `💾 Guardando…`.
- **Panel lateral** con IPs de escucha disponibles (auto-detectadas), puerto, nombre del agente conectado, modelo en uso e indicador de conexión (punto verde/rojo).
- Entrada con `Enter` (enviar) / `Shift+Enter` (nueva línea). Botón de limpieza del historial.
- Diseño desacoplado mediante **callbacks**: el `ChatRoomServer` no conoce la GUI, lo que permite reemplazarla por cualquier otra interfaz (web, móvil, CLI) sin modificar la lógica de red.

### 3. `InteractiveChatSession` extendida — modo LOCAL y NETWORK
- Nuevo parámetro `network_client=None` en el constructor — **100% retrocompatible**.
- Sin `network_client`: modo LOCAL, comportamiento original por teclado intacto.
- Con `network_client`: modo NETWORK — el bucle lee mensajes de la red, ejecuta el turno con el agente, y envía la respuesta y los metadatos (`tok/s`, latencia, `wiki_count`) de vuelta a la Sala de Chat.
- El agente envía **notificaciones de estado** (`agent_status`) durante el procesamiento, que la Sala de Chat muestra en su barra de estado en tiempo real.
- La terminal sigue mostrando toda la información habitual (árbol conceptual, métricas, comandos ejecutados) independientemente del modo de entrada.

### 4. CLI Ampliada
- `wiki-agent chat`: sin cambios en modo local; ahora pregunta interactivamente la IP al inicio (Enter vacío = modo local).
- `wiki-agent chat --connect <IP> [--port N]`: activa modo red directamente, sin preguntas interactivas.
- `wiki-agent chat-room [--port N]`: nuevo comando que lanza la Sala de Chat GUI.

### 5. Launchers Actualizados
- `iniciar_sala_de_chat.bat` — Inicia la Sala de Chat (ejecutar primero).
- `iniciar_agente_modo_red.bat` — Inicia el Agente IA (solicita IP por teclado).
- `iniciar_wiki_agent.bat` — Actualizado con instrucciones de referencia a los nuevos launchers.

---

## Nuevos Módulos y Arquitectura

```
src/wiki_agent/
├── network/
│   ├── __init__.py          # Exportaciones del módulo de red
│   ├── protocol.py          # Protocolo NDJSON v1: NetworkMessage, MessageType, constructores
│   ├── connection.py        # RobustSocketConnection: búfer, send_lock, cierre ordenado
│   ├── server.py            # ChatRoomServer: servidor TCP con callbacks event-driven
│   └── client.py            # AgentNetworkClient: cliente TCP para el Agente IA
├── chat_room.py             # GUI Tkinter de la Sala de Chat (Programa Servidor)
└── ui/
    └── chat_session.py      # Extendida: parámetro network_client, modo LOCAL y NETWORK
```

```
(raíz del proyecto)
├── iniciar_sala_de_chat.bat          # Nuevo launcher: Sala de Chat
├── iniciar_agente_modo_red.bat       # Nuevo launcher: Agente en modo red
└── iniciar_wiki_agent.bat            # Actualizado
```

```
tests/
└── test_network.py          # 4 tests unitarios de la capa de red
```

---

## Flujo de Uso

```
1. ABRE la Sala de Chat:
   > iniciar_sala_de_chat.bat
   → Ventana GUI abierta. Esperando conexión del Agente…

2. INICIA el Agente IA (en la misma máquina o en otra de la red):
   > iniciar_agente_modo_red.bat
   → Solicita IP de la Sala de Chat (127.0.0.1 si es la misma máquina)
   → Agente verifica el modelo GGUF y se conecta
   → Sala de Chat muestra "✅ Agente conectado"

3. El usuario escribe en la Sala de Chat y pulsa Enviar
   → La Sala de Chat deshabilita el input y muestra "🧠 Pensando…"
   → El Agente procesa (con toda su lógica ReAct + Wiki visible en terminal)
   → La Sala de Chat recibe la respuesta y la muestra con metadatos

4. Para terminar: cerrar cualquiera de las dos ventanas/terminales
```

---

## Protocolo de Red — Especificación

Todos los mensajes siguen la estructura JSON:
```json
{
  "version": 1,
  "type": "<tipo>",
  "payload": { ... },
  "timestamp": 1730198400.123
}
```

Cada mensaje se delimita con `\n` (newline) para transmisión TCP (NDJSON).

| Tipo | Dirección | Payload clave |
|------|-----------|---------------|
| `handshake` | Agente → Sala | `client_name`, `model_name`, `capabilities` |
| `handshake_ack` | Sala → Agente | `server_name`, `status` |
| `chat_message` | Sala → Agente | `text`, `sender` |
| `agent_status` | Agente → Sala | `state` (`LISTO` \| `PROCESANDO` \| `ERROR`), `detail` |
| `agent_response` | Agente → Sala | `text`, `metadata` (`tok_s`, `latency`, `wiki_count`) |
| `ping` / `pong` | Ambos | — |
| `error` | Ambos | `error`, `code` |

### Estados formales del Agente (`AgentState`)
- `LISTO`: Agente conectado y preparado para recibir nuevo input (indicador verde).
- `PROCESANDO`: Agente pensando y calculando respuesta (indicador amarillo).
- `ERROR`: Fallo durante el procesamiento o en conexión (indicador rojo).

---

## Verificación y Calidad

- **Tests unitarios**: `tests/test_network.py` — 6 tests pasando (`Ran 6 tests: OK`).
  - Serialización/deserialización del protocolo NDJSON.
  - Metadatos en `agent_response`.
  - Manejo de fragmentación TCP (packet sticking) con pares de sockets reales.
  - Flujo completo handshake + `chat_message` + `agent_response` con servidor real en puerto efímero.
  - Serialización de estados formales del agente (`AgentState`).
  - Propagación y sincronización de estados cliente-servidor en tiempo real.
- **Suite completa**: `Ran 14 tests: OK` (8 de la base de conocimiento + 6 de red).
- **Importaciones verificadas**: todos los módulos nuevos importan correctamente desde el entorno `venv`.
- **Retrocompatibilidad**: `iniciar_wiki_agent.bat` (modo local) funciona sin cambios.

