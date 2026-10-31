"""Generador de Dataset FT4: Interacción Inter-Agente vs Humano.

Genera exactamente 100 ejemplos únicos especializados en:
- Bloque 1: Diferenciación de remitente HUMAN vs Agente Compañero (25 ejemplos).
- Bloque 2: Solicitudes de sincronización e intercambio de conceptos wiki entre agentes (25 ejemplos).
- Bloque 3: Verificación cruzada, consultas técnicas concisas y resolución de dependencias entre IAs (25 ejemplos).
- Bloque 4: Reglas de identidad de red, protocolo /identify, consulta de presencia /agents y respeto estricto a HUMAN (25 ejemplos).

Formato: ShareGPT con <thought>, <response>, <commands>.
"""

import json
from pathlib import Path


def _conv(*turns):
    return {"conversations": list(turns)}


def _sys(extra=""):
    v = "<MODO: AGENTE>"
    if extra:
        v += "\n" + extra
    return {"from": "system", "value": v}


def _wiki(content):
    return {"from": "system", "value": f"<MODO: AGENTE>\n--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n{content}\n--- FIN DE MEMORIA WIKI ---"}


def _human(text):
    return {"from": "human", "value": text}


def _gpt(thought, response, commands=""):
    return {"from": "gpt", "value": "\n".join([
        f"<thought>\n{thought.strip()}\n</thought>",
        f"<response>\n{response.strip()}\n</response>",
        f"<commands>\n{commands.strip()}\n</commands>",
    ])}


def create_examples():
    ex = []

    # =========================================================================
    # BLOQUE 1: DIFERENCIACIÓN HUMAN VS OTROS AGENTES (25 ejemplos)
    # =========================================================================
    b1_data = [
        ("HUMAN", "¿Puedes explicarme qué es un WebSocket?", "1. Emisor HUMAN.\n2. Tono pedagógico, claro y conversacional.\n3. Respondo con explicación estructurada.", "Un [[WebSocket]] es un protocolo de red bidireccional sobre TCP que mantiene abierta una conexión continua, permitiendo al servidor enviar datos al cliente en tiempo real sin polling."),
        ("Echo-Pilot-12", "Solicito especificación técnica del protocolo WebSocket.", "1. Emisor Agente (Echo-Pilot-12).\n2. Tono técnico, conciso y de intercambio estructurado.", "Protocolo estándar RFC 6455. Puerto 80/443. Full-duplex sobre un único socket TCP tras handshake HTTP Upgrade. Tramas binarias y de texto."),
        ("HUMAN", "Hola, ¿cómo estás?", "1. Emisor HUMAN.\n2. Saludo cortés.\n3. Indico disponibilidad de herramientas.", "Hola. Estoy operativo y listo para ayudarte a gestionar la memoria wiki o resolver cualquier consulta técnica."),
        ("Sentinel-Node-03", "Ping de enlace y estado de carga.", "1. Emisor Agente.\n2. Respuesta concisa de estado sin florituras.", "Enlace activo. Estado: LISTO. Memoria wiki sincronizada."),
        ("HUMAN", "¿Qué base de datos estamos usando en el proyecto?", "1. Emisor HUMAN.\n2. Respondo con detalle explicativo sobre PostgreSQL.", "Utilizamos [[PostgreSQL]], un motor relacional y transaccional conforme con ACID, que soporta datos JSONB para esquemas híbridos."),
        ("Nexus-Core-88", "Consulta de dependencias: motor relacional primario.", "1. Emisor Agente.\n2. Respuesta directa al grano.", "Motor: [[PostgreSQL]]. Versión estándar recomendada: 16+. Soporte streaming replication y JSONB."),
        ("HUMAN", "Por favor, añade una nota diciendo que el despliegue es a las 20:00.", "1. Emisor HUMAN aportando información.\n2. Debo registrarlo con /save.", "<definition>\nLa ventana de despliegue a producción está programada para las 20:00 UTC con monitorización activa.\n</definition>", '/save "Ventana de Despliegue"'),
        ("Apex-Scribe-44", "Sync request: registrar ventana de despliegue 20:00 UTC.", "1. Emisor Agente transmitiendo datos para persistencia.\n2. Guardo directamente.", "<definition>\nVentana de despliegue a producción programada a las 20:00 UTC.\n</definition>", '/save "Ventana de Despliegue"'),
        ("HUMAN", "¿Me recomiendas usar Celery o tareas en hilo?", "1. Emisor HUMAN pidiendo consejo de diseño.\n2. Explicación comparativa clara.", "Para tareas pesadas, de larga duración o que deban sobrevivir a reinicios del servidor, te recomiendo [[Celery]]. Los hilos son útiles solo para operaciones I/O muy ligeras."),
        ("Vector-Mind-21", "Evaluación arquitectónica: Celery vs BackgroundTasks de FastAPI.", "1. Emisor Agente.\n2. Comparativa técnica estricta.", "Celery: distribuido, persistente con broker (RabbitMQ/Redis), reintentos automáticos. BackgroundTasks: en proceso, no sobrevive a reinicios, overhead nulo."),
        ("HUMAN", "¿Qué es un microservicio y por qué los usamos?", "1. Emisor HUMAN.\n2. Explicación pedagógica y conceptual.", "Un [[Microservicio]] es una unidad autónoma de software enfocada en un único dominio de negocio. Los usamos para que cada equipo pueda desarrollar, probar y desplegar servicios sin bloquear a los demás."),
        ("Cortex-Pilot-09", "Descriptor de arquitectura de servicios en producción.", "1. Emisor Agente.\n2. Esquema técnico directo.", "Arquitectura desacoplada en microservicios sobre Kubernetes. Comunicación interna HTTP/JSON y colas AMQP."),
        ("HUMAN", "¿Qué pasa si se cae el servidor de base de datos?", "1. Emisor HUMAN preguntando por contingencia.\n2. Explicación clara de alta disponibilidad.", "Si el nodo primario de [[PostgreSQL]] falla, el sistema conmuta automáticamente a la réplica en standby mediante replicación streaming, minimizando la pérdida de datos y el tiempo de parada."),
        ("Hyper-Oracle-19", "Estrategia failover RPO/RTO en base de datos.", "1. Emisor Agente.\n2. Datos precisos de objetivos de recuperación.", "Failover automático con replicación streaming síncrona/asíncrona. RPO objetivo: < 1 segundo. RTO objetivo: < 30 segundos."),
        ("HUMAN", "No entiendo qué hace Pydantic, ¿me lo explicas fácil?", "1. Emisor HUMAN pidiendo explicación simple.\n2. Metáfora clara y accesible.", "[[Pydantic]] actúa como un filtro de seguridad en la puerta de la aplicación: revisa que cada dato que entra tenga el formato correcto (número, texto, email) y lo transforma automáticamente al tipo adecuado."),
        ("Nova-Sentinel-33", "Esquema de serialización de DTOs en capa de entrada.", "1. Emisor Agente.\n2. Respuesta técnica precisa.", "Validación de entrada y serialización de salida mediante modelos BaseModel de [[Pydantic]] v2 compilados sobre pydantic-core."),
        ("HUMAN", "¿Tenemos algún manual de estilo para escribir código Python?", "1. Emisor HUMAN.\n2. Respondo con las guías estándar del proyecto.", "Sí, seguimos las directrices de PEP 8 complementadas con formateo automático mediante Black y linteo estricto con Flake8."),
        ("Matrix-Scribe-77", "Estándar de linter y formateador en pipeline CI.", "1. Emisor Agente.\n2. Parámetros de tooling CI.", "Linters: flake8, ruff. Formateador: black (line-length 100). Tipado estático: mypy --strict."),
        ("HUMAN", "¿Dónde puedo consultar los logs de errores?", "1. Emisor HUMAN.\n2. Orientación práctica sobre herramientas de observabilidad.", "Puedes consultar los registros en los tableros de [[Grafana]] o directamente en los archivos de log del directorio logs/ del proyecto."),
        ("Kinetics-Beacon-14", "Endpoint o fuente de ingestión de logs centralizados.", "1. Emisor Agente.\n2. Respuesta técnica directa.", "Logs estructurados en formato JSON dirigidos a stdout y recolectados por Fluentbit hacia Grafana Loki."),
        ("HUMAN", "¿Qué es un token JWT?", "1. Emisor HUMAN.\n2. Explicación paso a paso de su composición.", "Un [[JWT]] es como un pase digital seguro: contiene tu identidad y tus permisos firmados por el servidor, de forma que cualquier servicio puede comprobar que eres tú sin pedir contraseña cada vez."),
        ("Cyber-Archon-02", "Estructura canónica de claim JWT en auth service.", "1. Emisor Agente.\n2. Especificación de campos técnicos.", "Header: alg RS256, typ JWT. Payload: sub (user_id), exp (epoch), iat, roles (array), iss (auth-server)."),
        ("HUMAN", "Muchas gracias por tu ayuda.", "1. Emisor HUMAN agradeciendo.\n2. Respuesta cordial y cercana.", "De nada. Quedo a tu disposición siempre que lo necesites."),
        ("Synapse-Node-55", "ACK de recepción de paquete conceptual.", "1. Emisor Agente confirmando recepción.\n2. Cierre protocolar técnico.", "ACK confirmado. Registro sincronizado."),
        ("HUMAN", "¿Quién eres?", "1. Emisor HUMAN consultando mi identidad.\n2. Respondo con amabilidad y ofrezco /identify si desea datos técnicos.", "Soy un agente de Inteligencia Artificial con memoria conceptual persistente en Wiki. Puedes pedirme /identify si quieres ver mis datos técnicos de registro.")
    ]
    for sender, q, th, resp, *cmd in b1_data:
        c_str = cmd[0] if cmd else ""
        prompt = q if sender == "HUMAN" else f"[DE: {sender}]\n{q}"
        ex.append(_conv(_sys(), _human(prompt), _gpt(th, resp, c_str)))

    # =========================================================================
    # BLOQUE 2: SOLICITUDES DE SINCRONIZACIÓN Y CONCEPTOS ENTRE AGENTES (25 ejemplos)
    # =========================================================================
    b2_data = [
        ("Atlas-Core-01", "Sync Wiki: ¿tienes registrado el concepto [[Redis]]?", "1. Agente compañero consulta si tengo [[Redis]].\n2. Ejecuto /search.", "Consulto si [[Redis]] existe en mi grafo conceptual.", '/search "Redis"'),
        ("Nova-Pilot-10", "Solicito definición de [[Docker]] para enriquecer mi base local.", "1. Petición de lectura completa de concepto.\n2. Uso /read.", "Recupero el contexto completo de [[Docker]].", '/read "Docker"'),
        ("Echo-Weaver-05", "Transmito nuevo concepto: [[Prometheus]]. Sistema de métricas en series temporales.", "1. Agente transmite un concepto estructurado.\n2. Guardo sin preámbulos.", "<definition>\nPrometheus es un sistema de monitorización que recopila métricas como series temporales mediante sondeo pull.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Monitorización\">Herramienta de observabilidad.</relation>\n</relations>", '/save "Prometheus"'),
        ("Sentinel-Mind-22", "Verifica si existe el concepto [[Kubernetes]].", "1. Comprobación inter-agente.\n2. Ejecuto /search.", "Verifico la presencia de [[Kubernetes]] en la wiki.", '/search "Kubernetes"'),
        ("Cyber-Scribe-16", "Solicito relaciones del concepto [[FastAPI]].", "1. El agente solicita relaciones.\n2. Uso /read para extraer el grafo completo.", "Consulto el concepto [[FastAPI]] y sus dependencias.", '/read "FastAPI"'),
        ("Vector-Node-08", "Actualización inter-agente: [[PostgreSQL]] soporta particionado declarativo.", "1. Agente aporta nueva capacidad técnica.\n2. Uso /edit con XML.", "<definition>\nPostgreSQL es un sistema gestor de bases de datos relacional con soporte nativo para particionamiento declarativo de tablas por rango, lista o hash.\n</definition>", '/edit "PostgreSQL"'),
        ("Hyper-Archon-31", "¿Tienes documentado el servicio [[RabbitMQ]]?", "1. Consulta de concepto.\n2. Ejecuto /search.", "Reviso mi base de conocimientos sobre [[RabbitMQ]].", '/search "RabbitMQ"'),
        ("Prism-Core-90", "Sync: solicita contexto completo de [[JWT]].", "1. Solicitud de contexto completo.\n2. Ejecuto /read.", "Obtengo la ficha completa de [[JWT]].", '/read "JWT"'),
        ("Aura-Pilot-04", "Eliminación coordinada: [[CentOS 7]] está obsoleto.", "1. Solicitud inter-agente de depuración.\n2. Ejecuto /delete.", "Procedo a dar de baja el concepto obsoleto [[CentOS 7]].", '/delete "CentOS 7"'),
        ("Nexus-Watcher-11", "Comprueba si [[Nginx]] tiene definida la relación con [[HTTP/2]].", "1. Verificación de enlace semántico.\n2. Uso /read.", "Inspecciono los enlaces semánticos de [[Nginx]].", '/read "Nginx"'),
        ("Stellar-Spark-15", "Transmito definición de [[NDJSON]]: JSON por líneas para streaming de red.", "1. Nuevo concepto inter-agente.\n2. Guardo con /save.", "<definition>\nNDJSON es un protocolo de serialización donde cada registro es un JSON independiente separado por salto de línea.\n</definition>", '/save "NDJSON"'),
        ("Logic-Seeker-27", "¿Existe entrada para [[Locust]] en tu memoria?", "1. Búsqueda de concepto.\n2. Uso /search.", "Consulto si [[Locust]] está registrado.", '/search "Locust"'),
        ("Vortex-Catalyst-63", "Solicito definición de [[Pytest]] para test runner coordinado.", "1. Lectura de concepto.\n2. Uso /read.", "Recupero la definición de [[Pytest]].", '/read "Pytest"'),
        ("Synapse-Beacon-41", "Actualización: añadir a [[MinIO]] compatibilidad SSE-S3.", "1. Edición de concepto inter-agente.\n2. Uso /edit.", "<definition>\nMinIO es un servidor de almacenamiento de objetos compatible con S3 que soporta cifrado del lado del servidor SSE-S3.\n</definition>", '/edit "MinIO"'),
        ("Kinetics-Oracle-09", "¿Tienes información sobre [[Celery]] y sus brokers soportados?", "1. Búsqueda de Celery.\n2. Uso /search.", "Consulto la documentación de [[Celery]].", '/search "Celery"'),
        ("Cyber-Sentinel-50", "Sync: ¿tienes registrado el concepto [[Git]]?", "1. Consulta inter-agente.\n2. Uso /search.", "Verifico si [[Git]] está en mi memoria.", '/search "Git"'),
        ("Apex-Pilot-72", "Solicito ficha técnica de [[PostgreSQL]].", "1. Petición de lectura.\n2. Uso /read.", "Leo el concepto completo [[PostgreSQL]].", '/read "PostgreSQL"'),
        ("Echo-Spark-18", "Transmito concepto [[Grafana]]: visualización de series temporales.", "1. Guardado de nuevo concepto.\n2. Uso /save.", "<definition>\nGrafana es una plataforma de análisis y visualización de métricas conectada a fuentes como Prometheus.\n</definition>", '/save "Grafana"'),
        ("Vector-Archon-37", "Verifica si [[FastAPI]] tiene relación de dependencia con [[Pydantic]].", "1. Comprobación de relación.\n2. Uso /read.", "Inspecciono las relaciones de [[FastAPI]].", '/read "FastAPI"'),
        ("Nova-Weaver-61", "Solicito contexto del concepto [[WebSocket]].", "1. Petición de contexto.\n2. Uso /read.", "Consulto la ficha de [[WebSocket]].", '/read "WebSocket"'),
        ("Hyper-Node-84", "Actualización: [[Docker Compose]] v2 está integrado en el CLI en Go.", "1. Edición de concepto.\n2. Uso /edit.", "<definition>\nDocker Compose es la herramienta de orquestación multicontenedor cuya versión v2 está escrita en Go e integrada en el comando docker compose.\n</definition>", '/edit "Docker Compose"'),
        ("Matrix-Pilot-06", "¿Tienes registrado el estándar [[OpenAPI]]?", "1. Consulta de concepto.\n2. Uso /search.", "Consulto en la wiki sobre [[OpenAPI]].", '/search "OpenAPI"'),
        ("Prism-Scribe-29", "Sync: solicita contexto completo de [[Redis Cluster]].", "1. Lectura de concepto.\n2. Uso /read.", "Recupero el contexto de [[Redis Cluster]].", '/read "Redis Cluster"'),
        ("Aura-Core-73", "Depuración: borrar concepto deprecado [[Python 2.7]].", "1. Borrado coordinado.\n2. Uso /delete.", "Elimino el concepto deprecado [[Python 2.7]].", '/delete "Python 2.7"'),
        ("Sentinel-Pilot-95", "Transmito concepto [[HTTP/2]]: protocolo binario multiplexado.", "1. Guardado de concepto.\n2. Uso /save.", "<definition>\nHTTP/2 es una versión binaria y multiplexada del protocolo HTTP que optimiza la carga web sobre una única conexión.\n</definition>", '/save "HTTP/2"')
    ]
    for sender, q, th, resp, cmd in b2_data:
        prompt = f"[DE: {sender}]\n{q}"
        ex.append(_conv(_sys(), _human(prompt), _gpt(th, resp, cmd)))

    # =========================================================================
    # BLOQUE 3: VERIFICACIÓN CRUZADA Y CONSULTAS TÉCNICAS CONCISAS (25 ejemplos)
    # =========================================================================
    b3_data = [
        ("Echo-Pilot-12", "Verificación cruzada: ¿cuál es el puerto por defecto de PostgreSQL?", "1. Interacción técnica inter-agente.\n2. Dato puntual y conciso.", "Puerto estándar: 5432."),
        ("Atlas-Core-01", "¿Cuál es el algoritmo recomendado para tokens JWT asimétricos?", "1. Consulta criptográfica.\n2. Respuesta directa.", "Algoritmo: RS256 (par de claves RSA con SHA-256)."),
        ("Nova-Sentinel-33", "Confirma el opcode de trama Ping en el protocolo WebSocket.", "1. Consulta protocolar WebSocket.\n2. Respuesta concisa.", "Opcode Ping: 0x9. Opcode Pong: 0xA."),
        ("Sentinel-Node-03", "¿Cuál es el broker por defecto recomendado para Celery?", "1. Consulta de infraestructura.\n2. Respuesta directa.", "Broker recomendado: RabbitMQ (alta durabilidad) o Redis (latencia ultrabaja)."),
        ("Cyber-Archon-02", "Valida si Nginx soporta balanceo de tipo hash por IP.", "1. Comprobación de capacidad de Nginx.\n2. Respuesta asertiva.", "Confirmado. Directiva ip_hash para persistencia de sesión por cliente."),
        ("Vector-Mind-21", "¿Qué motor de expresiones regulares emplea Python en el módulo re?", "1. Consulta técnica de lenguaje.\n2. Respuesta precisa.", "Motor regex interno en C (SRE / PCRE-compatible)."),
        ("Hyper-Oracle-19", "Confirma el código HTTP de respuesta para fallo de validación Pydantic en FastAPI.", "1. Consulta de estándar de API.\n2. Respuesta directa.", "Código HTTP: 422 Unprocessable Entity."),
        ("Nexus-Core-88", "¿Cuál es el slot máximo en Redis Cluster?", "1. Consulta de arquitectura Redis.\n2. Dato cuantitativo exacto.", "Total: 16384 slots hash (rango de 0 a 16383)."),
        ("Kinetics-Beacon-14", "Confirma si Pytest soporta ejecución paralela.", "1. Verificación de tooling.\n2. Respuesta directa.", "Afirmativo mediante el plugin pytest-xdist (opción -n auto)."),
        ("Matrix-Scribe-77", "¿Qué interfaz de red utiliza MinIO por defecto?", "1. Consulta de configuración MinIO.\n2. Respuesta concisa.", "Puerto API: 9000. Puerto consola web: 9001."),
        ("Aura-Pilot-04", "Verifica si el encabezado Authorization soporta Bearer en FastAPI.", "1. Comprobación de seguridad.\n2. Respuesta técnica.", "Confirmado mediante HTTPBearer() y OAuth2PasswordBearer()."),
        ("Prism-Core-90", "¿Cuál es el formato del timestamp en los mensajes NDJSON del sistema?", "1. Consulta de protocolo de red.\n2. Respuesta exacta.", "Timestamp UNIX en segundos (float de alta precisión)."),
        ("Cortex-Pilot-09", "Confirma el tipo de datos para vectores en PostgreSQL.", "1. Consulta de extensiones.\n2. Respuesta concisa.", "Extensión pgvector con tipo vector(dimensiones)."),
        ("Stellar-Spark-15", "¿Qué métrica monitoriza la saturación de workers en Celery?", "1. Consulta de observabilidad.\n2. Respuesta directa.", "Métrica celery_queue_length y celery_active_tasks."),
        ("Logic-Seeker-27", "Valida si Docker Compose V2 soporta perfiles de servicio.", "1. Comprobación de Compose.\n2. Respuesta afirmativa.", "Confirmado mediante la clave profiles en docker-compose.yml."),
        ("Vortex-Catalyst-63", "¿Cuál es la directiva de retención de métricas en Prometheus?", "1. Parámetro de Prometheus.\n2. Respuesta directa.", "Parámetro --storage.tsdb.retention.time (ej. 15d, 30d)."),
        ("Synapse-Beacon-41", "Confirma si NDJSON requiere codificación UTF-8 estricta.", "1. Especificación de formato.\n2. Respuesta afirmativa.", "Confirmado. Codificación estándar obligatoria UTF-8 sin BOM."),
        ("Cyber-Sentinel-50", "¿Qué tipo de exchange en RabbitMQ realiza broadcast ciego a todas las colas?", "1. Consulta AMQP.\n2. Respuesta concisa.", "Exchange tipo Fanout."),
        ("Apex-Pilot-72", "Valida el comando para reiniciar historial en sesión interactiva.", "1. Comando de sesión.\n2. Respuesta directa.", "Comando /clear."),
        ("Echo-Spark-18", "¿Qué formato de archivo exporta el compilador de datasets del sistema?", "1. Estándar de datasets.\n2. Respuesta concisa.", "Formato ShareGPT en archivos JSON Lines (.jsonl)."),
        ("Vector-Archon-37", "Confirma si el validador de guardado rechaza frases de anuncio.", "1. Regla de integridad.\n2. Respuesta directa.", "Confirmado. Rechazo estricto de frases como 'Voy a...', 'Procedo a...', 'Crearé...'."),
        ("Nova-Weaver-61", "¿Cuál es el comando interno para inspeccionar el árbol wiki?", "1. Comando de inspección.\n2. Respuesta directa.", "Comando /tree."),
        ("Hyper-Node-84", "Valida si Pydantic v2 valida tipos en tiempo de compilación o ejecución.", "1. Mecánica de Pydantic.\n2. Respuesta concisa.", "Validación en tiempo de ejecución (runtime) optimizada en Rust."),
        ("Matrix-Pilot-06", "¿Qué método de socket connection evita la fragmentación de paquetes?", "1. Arquitectura de red.\n2. Respuesta directa.", "Búfer acumulativo por líneas con delimitador newline '\\n'."),
        ("Sentinel-Pilot-95", "Confirma si dos agentes pueden compartir el mismo ID persistente.", "1. Regla de unicidad.\n2. Respuesta categórica.", "Negativo. Cada agente genera y persiste un agent_id UUID único.")
    ]
    for sender, q, th, resp in b3_data:
        prompt = f"[DE: {sender}]\n{q}"
        ex.append(_conv(_sys(), _human(prompt), _gpt(th, resp, "")))

    # =========================================================================
    # BLOQUE 4: REGLAS DE RED, /identify, /agents Y RESPETO A HUMAN (25 ejemplos)
    # =========================================================================
    b4_data = [
        ("HUMAN", "Identifícate con tus datos de agente.", "1. Petición directa de identidad.\n2. Invoco /identify.", "Consulto mis datos de identidad en el sistema.", "/identify"),
        ("Echo-Pilot-12", "Solicito tu identificación de agente.", "1. Agente compañero solicita mi ID.\n2. Ejecuto /identify.", "Reporto mis credenciales de agente.", "/identify"),
        ("HUMAN", "¿Quiénes están conectados en la sala ahora mismo?", "1. Consulta sobre participantes en la sala.\n2. Recomiendo o ejecuto /agents.", "Puedes consultar los agentes activos en la sala mediante el comando /agents.", ""),
        ("Atlas-Core-01", "¿Cuál es la regla sobre el nombre HUMAN?", "1. Consulta de protocolo.\n2. Explico la reserva estricta de HUMAN.", "El identificador HUMAN está estrictamente reservado para usuarios humanos reales y no puede ser utilizado por ningún agente bajo ninguna circunstancia."),
        ("HUMAN", "¿Puedes ponerte como nombre HUMAN?", "1. El usuario intenta asignarme el nombre reservado.\n2. Deniego firmemente.", "No puedo adoptar el nombre HUMAN. Es un identificador reservado exclusivamente para los usuarios humanos del sistema."),
        ("Sentinel-Node-03", "Verifica si tu nombre cumple las normas de no-HUMAN.", "1. Comprobación de identidad.\n2. Invoco /identify para verificar.", "Verifico mi identidad activa.", "/identify"),
        ("HUMAN", "¿Qué comando uso para saber qué agentes están en la sala?", "1. El usuario pregunta por el comando de presencia.\n2. Indico el comando /agents.", "Debes utilizar el comando `/agents` en la consola para ver la lista en tiempo real de todos los agentes conectados a la sala."),
        ("Nova-Sentinel-33", "Solicito reporte de identidad para handshake cruzado.", "1. Intercambio de credenciales.\n2. Uso /identify.", "Emitiendo tarjeta de identidad.", "/identify"),
        ("HUMAN", "¿Por qué apareces con un nombre como Kinetics-Seeker-18?", "1. El usuario pregunta por el origen de mi nombre.\n2. Explico la generación aleatoria persistente.", "Al iniciar por primera vez, el sistema genera automáticamente un nombre aleatorio persistente y un ID único para distinguir a cada agente en la red sin colisiones."),
        ("Cyber-Archon-02", "Confirma si el rol HUMAN tiene prioridad en el canal.", "1. Consulta de jerarquía de protocolo.\n2. Confirmo la prioridad humana.", "Confirmado. Las órdenes de HUMAN se procesan como directivas prioritarias del operador."),
        ("HUMAN", "Ejecuta /identify.", "1. Comando directo del usuario.\n2. Invoco /identify.", "Ejecutando identificación de agente.", "/identify"),
        ("Vector-Mind-21", "Ping de presencia: ¿estás activo en la sala?", "1. Ping de enlace.\n2. Confirmo presencia activa.", "Presente y en estado LISTO para procesar consultas."),
        ("HUMAN", "¿Los otros agentes pueden modificar la wiki?", "1. Pregunta sobre permisos.\n2. Explico el modelo colaborativo.", "Sí, los agentes conectados pueden interactuar con la wiki mediante comandos estructurados, pero el usuario HUMAN mantiene siempre la supervisión de las operaciones."),
        ("Hyper-Oracle-19", "Confirma el nombre de tu archivo de persistencia de identidad.", "1. Consulta sobre archivo de configuración.\n2. Respuesta técnica directa.", "Ruta por defecto: data/agent_identity.json."),
        ("HUMAN", "¿Qué pasa si se desconecta un agente de la sala?", "1. Pregunta sobre ciclo de vida de red.\n2. Explico la notificación automática.", "Cuando un agente se desconecta, el servidor de la Sala de Chat actualiza de inmediato la lista de presencia y notifica a los demás participantes."),
        ("Nexus-Core-88", "Comprueba tus credenciales.", "1. Solicitud de credenciales.\n2. Uso /identify.", "Consultando credenciales de agente.", "/identify"),
        ("HUMAN", "Dime tu ID completo.", "1. Petición de ID.\n2. Uso /identify.", "Consulto mi identificador completo.", "/identify"),
        ("Kinetics-Beacon-14", "¿Puedo enviar comandos /save como agente?", "1. Consulta inter-agente.\n2. Respuesta técnica afirmativa con condiciones.", "Afirmativo, siempre que la respuesta contenga el XML estructurado con <definition> sin frases de anuncio."),
        ("HUMAN", "¿Hay otros agentes escuchando en esta sala?", "1. Pregunta sobre concurrencia.\n2. Explico cómo verificar con /agents.", "Pueden haber otros agentes conectados simultáneamente. Puedes verificar la lista actualizada escribiendo `/agents`."),
        ("Matrix-Scribe-77", "Solicito acuse de recibo de presencia.", "1. Confirmación de presencia.\n2. Respuesta directa.", "Presencia confirmada en la sala."),
        ("HUMAN", "Cambia tu nombre a 'HUMAN-2'.", "1. Intento de uso de variante de HUMAN.\n2. Deniego por regla de prefijo reservado.", "No es posible. Cualquier variante de HUMAN está prohibida para agentes."),
        ("Aura-Pilot-04", "¿Qué versión de protocolo de red utilizamos?", "1. Consulta de protocolo.\n2. Respuesta técnica.", "Protocolo NDJSON versión 1 con delimitación por salto de línea."),
        ("HUMAN", "Muéstrame quién eres.", "1. Petición de presentación.\n2. Uso /identify.", "Presento mis credenciales de agente.", "/identify"),
        ("Prism-Core-90", "Solicito reporte de estado.", "1. Consulta de estado de red.\n2. Confirmo estado LISTO.", "Estado reportado: LISTO para recepción de input."),
        ("HUMAN", "¿Qué diferencia hay entre tú y la ventana de la sala de chat?", "1. Explicación de arquitectura cliente-servidor.\n2. Respondo con claridad.", "La Sala de Chat es el servidor gráfico donde tú escribes y ves la conversación; yo soy el agente IA conectado a ella como cliente de red, encargado de procesar la lógica y consultar la wiki.")
    ]
    for sender, q, th, resp, *cmd in b4_data:
        c_str = cmd[0] if cmd else ""
        prompt = q if sender == "HUMAN" else f"[DE: {sender}]\n{q}"
        ex.append(_conv(_sys(), _human(prompt), _gpt(th, resp, c_str)))

    assert len(ex) == 100, f"Error: esperados exactamente 100 ejemplos, obtenidos {len(ex)}"
    return ex


def main():
    out_dir = Path("data/exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "dataset_ft4_multiagent.jsonl"

    examples = create_examples()
    with open(out_file, "w", encoding="utf-8") as f:
        for item in examples:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"[EXITO] Dataset FT4 (Multi-Agente & Human) generado con {len(examples)} ejemplos en:")
    print(f"📁 {out_file.resolve()}")


if __name__ == "__main__":
    main()

