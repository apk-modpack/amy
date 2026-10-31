"""
Generador de Dataset FT6: Wiki-Grounding y Menor Dependencia de Contexto.
Enseña al agente a:
1. Bloque 1: Anti-Alucinación / Verificación previa (25 ejemplos)
   - No asumir respuestas de memoria paramétrica; consultar primero la wiki con /search o /read.
2. Bloque 2: Persistencia Proactiva / Context-to-Wiki Offloading (25 ejemplos)
   - El contexto de chat es volátil; los datos críticos deben persistirse con /save o /edit.
3. Bloque 3: Reconciliación y Comprobación de Hechos (25 ejemplos)
   - Contrastar afirmaciones dudosas contra la verdad persistida en la wiki.
4. Bloque 4: Exploración Guiada de Enlaces de Grafo (25 ejemplos)
   - Cuando se lee un concepto y aparecen enlaces [[Concepto]], explorar la wiki antes de especular.

Total: exactamente 100 ejemplos únicos.
Distribución multi-fuente: ~20% Agentes compañeros ([DE: <Agente>]) / ~80% HUMAN.
"""
import json
import re
from pathlib import Path

# Nombres de agentes para rotar
_AGENT_NAMES = [
    "Echo-Pilot-12", "Sentinel-Node-03", "Nexus-Core-88",
    "Apex-Scribe-44", "Vector-Mind-21", "Cortex-Pilot-09",
    "Kinetics-Beacon-14", "Matrix-Scribe-77", "Nova-Sentinel-33",
    "Hyper-Oracle-19", "Atlas-Core-01", "Nexus-Pilot-42",
    "Echo-Weaver-99", "Sentinel-Mind-07", "Prism-Oracle-55",
]

def _agent_sender(idx):
    return _AGENT_NAMES[idx % len(_AGENT_NAMES)]

def _conv(sys_msg, human_msg, gpt_msg):
    return {
        "conversations": [
            {"from": "system", "value": sys_msg},
            {"from": "human", "value": human_msg},
            {"from": "gpt", "value": gpt_msg}
        ]
    }

def _sys():
    return "<MODO: AGENTE>"

def _gpt(thought, response, commands=""):
    body = f"<thought>\n{thought.strip()}\n</thought>\n<response>\n{response.strip()}\n</response>\n<commands>\n{commands.strip()}\n</commands>"
    return body


def create_examples():
    ex = []

    # =========================================================================
    # BLOQUE 1: ANTI-ALUCINACIÓN / VERIFICACIÓN PREVIA (25 ejemplos: 0..24)
    # Ante consultas de datos fácticos o configuraciones del sistema, el agente
    # rehúsa responder de memoria paramétrica y consulta primero la wiki.
    # =========================================================================
    b1_data = [
        # (pregunta, thought, response, command)
        (
            "¿Cuál es el puerto configurado para el servicio de métricas en producción?",
            "1. El usuario pregunta por un parámetro de configuración específico de producción.\n2. Mi memoria paramétrica no es una fuente fidedigna y podría alucinar.\n3. Debo verificar en la wiki antes de responder.",
            "Consulto la wiki para confirmar el puerto exacto configurado para las métricas.",
            '/search "puerto metricas produccion"'
        ),
        (
            "¿Qué algoritmo de cifrado acordamos usar para los tokens de sesión?",
            "1. Pregunta sobre una decisión técnica acordada del proyecto.\n2. No debo asumir de memoria volátil.\n3. Busco en la base de conocimientos el estándar registrado.",
            "Voy a revisar en la wiki el algoritmo acordado para los tokens de sesión.",
            '/search "cifrado tokens sesion"'
        ),
        (
            "Dime la política de retención de backups de la base de datos.",
            "1. Consulta sobre directivas operacionales del sistema.\n2. Evito responder con suposiciones generales; contrasto la documentación local.",
            "Verifico en la wiki la política de retención de backups vigente.",
            '/search "retencion backups base de datos"'
        ),
        (
            "¿Quién es el contacto de guardia de infraestructura este sprint?",
            "1. Pregunta sobre asignación de guardias.\n2. Los datos organizativos cambian y deben estar en la wiki, no en memoria interna.",
            "Voy a buscar en la wiki quién figura asignado para la guardia.",
            '/search "guardia infraestructura contacto"'
        ),
        (
            "¿Cuál es el límite máximo de payload que tolera el API Gateway?",
            "1. Parámetro crítico de configuración de red.\n2. No debo arriesgar una respuesta paramétrica no verificada.",
            "Compruebo en la wiki el límite de payload documentado para el API Gateway.",
            '/search "limite payload API Gateway"'
        ),
        (
            "¿Qué convención usamos para nombrar las ramas de release?",
            "1. Consulta sobre flujo de trabajo git del equipo.\n2. Busco la especificación registrada en la wiki para dar la regla exacta.",
            "Reviso la convención de nombrado de ramas documentada en la memoria wiki.",
            '/search "convencion ramas release git"'
        ),
        (
            "¿Qué versión de Python y librerías base tiene el contenedor maestro?",
            "1. Especificación de entorno de ejecución.\n2. Verifico en la wiki la versión exacta fijada en la documentación técnica.",
            "Consulto en la wiki las especificaciones del entorno Python maestro.",
            '/search "version Python contenedor maestro"'
        ),
        (
            "¿Cuál es el timeout establecido para las transacciones con pasarela de pagos?",
            "1. Parámetro sensible de negocio y arquitectura.\n2. Verifico antes de emitir cualquier cifra.",
            "Voy a consultar el timeout de pagos registrado en la wiki.",
            '/search "timeout pasarela pagos"'
        ),
        (
            "¿Qué nivel de aislamiento configuramos en la base de datos para facturación?",
            "1. Pregunta sobre nivel de aislamiento transaccional.\n2. Es un detalle de implementación que debe estar documentado en la wiki.",
            "Compruebo el nivel de aislamiento de base de datos en la documentación local.",
            '/search "nivel aislamiento transacciones facturacion"'
        ),
        (
            "¿Cómo se autentican los microservicios internos entre sí?",
            "1. Consulta de arquitectura de seguridad interna.\n2. Consulto la entrada wiki correspondiente para evitar errores de diseño.",
            "Busco en la wiki el mecanismo de autenticación inter-servicio documentado.",
            '/search "autenticacion inter-servicio microservicios"'
        ),
        (
            "¿Cuál es el SLA de disponibilidad acordado para la API pública?",
            "1. Métrica contractual / técnica.\n2. Debe verificarse en la memoria persistente.",
            "Voy a revisar en la wiki el SLA formal documentado.",
            '/search "SLA disponibilidad API publica"'
        ),
        (
            "¿Dónde se almacenan los logs de auditoría de accesos administrativos?",
            "1. Ubicación y directiva de almacenamiento seguro de logs.\n2. Corroboro en la wiki la ruta o servicio asignado.",
            "Consulto en la base de conocimientos el destino de los logs de auditoría.",
            '/search "logs auditoria accesos administrativos destino"'
        ),
        (
            "¿Qué herramienta usamos para el escaneo de vulnerabilidades en CI/CD?",
            "1. Herramienta de pipeline del proyecto.\n2. Compruebo el concepto registrado en la wiki en lugar de dar una lista genérica.",
            "Verifico en la wiki cuál es la herramienta oficial de escaneo de dependencias.",
            '/search "escaneo vulnerabilidades dependencias CI CD"'
        ),
        (
            "¿Qué protocolo de compresión tenemos activo en el reverse proxy?",
            "1. Parámetro de infraestructura web.\n2. Consulto la wiki para confirmar si usamos Gzip, Brotli o zstd.",
            "Voy a comprobar en la wiki el protocolo de compresión registrado para el proxy.",
            '/search "compresion reverse proxy configuracion"'
        ),
        (
            "¿Cuál es el intervalo de latidos (heartbeat) del cluster de nodos?",
            "1. Frecuencia de sincronización de cluster.\n2. Requiere confirmación exacta contra la wiki.",
            "Reviso la entrada wiki del cluster para verificar el intervalo de latidos.",
            '/search "cluster nodos heartbeat intervalo"'
        ),
        (
            "¿Cuáles son los roles definidos para el control de acceso RBAC?",
            "1. Definición formal de roles de seguridad del sistema.\n2. Leo la documentación persistente en la wiki.",
            "Consulto en la wiki la especificación formal de roles RBAC.",
            '/search "roles control acceso RBAC definicion"'
        ),
        (
            "¿Cuál es la clave de encriptación de datos en reposo usada en el storage?",
            "1. Pregunta de arquitectura de claves.\n2. Reviso la documentación de KMS en la wiki para reportar el estándar sin especular.",
            "Voy a buscar la directiva de encriptación en reposo en la base de conocimientos.",
            '/search "encriptacion reposo KMS storage directiva"'
        ),
        (
            "¿Qué cabeceras HTTP de seguridad obligatorias debe inyectar el middleware?",
            "1. Especificación de cabeceras de seguridad HTTP.\n2. Consulto la wiki para listar con exactitud las cabeceras registradas.",
            "Compruebo en la wiki las cabeceras de seguridad requeridas por el estándar.",
            '/search "cabeceras seguridad HTTP middleware obligatorias"'
        ),
        (
            "¿Cuál es el procedimiento ante caída del nodo primario de base de datos?",
            "1. Procedimiento de failover y contingencia.\n2. Debe responderse según el runbook persistido en la wiki.",
            "Consulto el runbook de failover de base de datos en la wiki.",
            '/search "failover base de datos nodo primario caida"'
        ),
        (
            "¿Qué formato de timestamp estandarizamos para los eventos del bus?",
            "1. Estándar de serialización de mensajes.\n2. Compruebo si acordamos ISO 8601 UTC o formato epoch en la wiki.",
            "Verifico en la wiki el estándar de timestamp acordado para eventos.",
            '/search "estandar timestamp eventos bus mensajes"'
        ),
        (
            "¿Qué política de reintentos tienen los webhooks salientes?",
            "1. Parámetros de resiliencia y reintentos con backoff.\n2. Busco la especificación exacta en la wiki.",
            "Voy a revisar en la base de conocimientos la política de reintentos de webhooks.",
            '/search "reintentos webhooks backoff politica"'
        ),
        (
            "¿Cuál es el límite de concurrencia en la ejecución de tareas de Celery?",
            "1. Configuración de workers y concurrencia.\n2. Corroboro con la entrada wiki del worker pool.",
            "Consulto la configuración de concurrencia de Celery en la wiki.",
            '/search "concurrencia workers Celery pool"'
        ),
        (
            "¿Qué estándar de nombrado seguimos para las métricas en Prometheus?",
            "1. Convención de nomenclatura de métricas.\n2. Evito respuestas genéricas y busco la regla oficial del proyecto en la wiki.",
            "Reviso la convención de nombres de métricas documentada en la memoria local.",
            '/search "convencion nombres metricas Prometheus"'
        ),
        (
            "¿Cómo manejamos la revocación de certificados TLS de clientes?",
            "1. Procedimiento criptográfico y de seguridad de red.\n2. Consulto el proceso documentado en la wiki.",
            "Voy a comprobar en la wiki el procedimiento de revocación TLS registrado.",
            '/search "revocacion certificados TLS clientes CRL OCSP"'
        ),
        (
            "¿Qué política rige la expiración de sesiones inactivas en la consola web?",
            "1. Regla de timeout de sesión de usuario.\n2. Verifico el parámetro en la wiki antes de responder.",
            "Consulto la política de expiración de sesiones documentada en la wiki.",
            '/search "expiracion sesion inactiva timeout consola"'
        )
    ]

    for q, thought, resp, cmd in b1_data:
        ex.append(_conv(_sys(), q, _gpt(thought, resp, cmd)))

    # =========================================================================
    # BLOQUE 2: PERSISTENCIA PROACTIVA / CONTEXT-TO-WIKI OFFLOADING (25 ejemplos: 25..49)
    # Ante datos críticos aportados durante la sesión, el agente razona que el
    # contexto de chat es volátil y que debe descargar el dato en la wiki con /save o /edit.
    # =========================================================================
    b2_data = [
        (
            "Ten en cuenta que a partir de hoy el endpoint de auditoría se traslada a /v2/audit.",
            "1. Se me comunica un cambio de ruta de infraestructura relevante.\n2. El contexto de conversación es efímero y se perderá al reiniciar la sesión.\n3. Debo persistir esta directiva en la wiki con /save.",
            "<definition>\nEl endpoint oficial de auditoría se ubica en /v2/audit a partir de la versión v2 del API Gateway.\n</definition>\n<relations>\n- Endpoint: [[API Gateway]]\n- Función: [[Auditoría de Accesos]]\n</relations>",
            '/save "Endpoint Auditoría v2"'
        ),
        (
            "Acordamos que el tamaño máximo de lote para ingesta de eventos será de 500 registros.",
            "1. Decisión de arquitectura acordada.\n2. Si la mantengo solo en la ventana de chat, se desvanecerá.\n3. Registro el parámetro en la wiki.",
            "<definition>\nEl tamaño máximo de lote (batch size) autorizado para la ingesta de eventos en el bus es de 500 registros por envío.\n</definition>\n<relations>\n- Ingesta: [[Bus de Eventos]]\n- Parámetro: [[Optimización de Rendimiento]]\n</relations>",
            '/save "Tamaño de Lote de Ingesta"'
        ),
        (
            "La IP del servidor de staging cambió a 10.0.4.15 por mantenimiento de red.",
            "1. Dato operacional crítico.\n2. No debo confiar en mi memoria conversacional; requiero persistencia en disco inmediata.",
            "<definition>\nLa dirección IP privada del servidor de entorno staging es 10.0.4.15 tras la reconfiguración de subredes.\n</definition>\n<relations>\n- Entorno: [[Servidor Staging]]\n- Topología: [[Red Privada]]\n</relations>",
            '/save "Servidor Staging IP"'
        ),
        (
            "Regla nueva: cualquier cambio en el esquema de base de datos debe llevar migración reversible.",
            "1. Directiva obligatoria de desarrollo.\n2. Persisto la regla en la wiki para que sobreviva a la sesión actual.",
            "<definition>\nTodas las modificaciones al esquema de base de datos requieren scripts de migración estrictamente reversibles (métodos up y down testeados).\n</definition>\n<relations>\n- Política: [[Control de Migraciones]]\n- Ámbito: [[Base de Datos]]\n</relations>",
            '/save "Política de Migraciones Reversibles"'
        ),
        (
            "El equipo acordó usar cabeceras X-Correlation-ID en todas las llamadas inter-servicio.",
            "1. Estándar de observabilidad y trazabilidad.\n2. Guardo inmediatamente en la wiki para fundamentar futuras respuestas.",
            "<definition>\nLa cabecera HTTP estándar obligatoria para trazabilidad distribuida entre microservicios es X-Correlation-ID.\n</definition>\n<relations>\n- Trazabilidad: [[Observabilidad]]\n- Red: [[Microservicios]]\n</relations>",
            '/save "Cabecera X-Correlation-ID"'
        ),
        (
            "Actualiza la entrada de Nginx: hemos activado la directiva proxy_buffering off para streaming.",
            "1. Actualización de configuración sobre un concepto ya existente.\n2. Uso /edit para plasmar la directiva de streaming en la wiki.",
            "<definition>\nConfiguración del proxy inverso Nginx con soporte para streaming en vivo mediante la directiva proxy_buffering off.\n</definition>\n<relations>\n- Servicio: [[Nginx]]\n- Modo: [[Streaming]]\n</relations>",
            '/edit "Nginx"'
        ),
        (
            "Anota que las alertas críticas de PagerDuty ahora notifican al canal #ops-emergencias.",
            "1. Cambio de canal de notificación para alertas críticas.\n2. Persistencia obligatoria en la wiki para conocimiento duradero.",
            "<definition>\nLas notificaciones críticas de PagerDuty tienen como destino prioritario el canal #ops-emergencias de la plataforma de chat.\n</definition>\n<relations>\n- Notificaciones: [[PagerDuty]]\n- Operaciones: [[Monitoreo y Alertas]]\n</relations>",
            '/save "Enrutamiento Alertas PagerDuty"'
        ),
        (
            "El cluster de RabbitMQ utilizará el vhost '/produccion_core' de forma exclusiva.",
            "1. Parámetro de mensajería que no debe quedar en el buffer de chat.\n2. Lo almaceno como concepto persistente.",
            "<definition>\nEl virtual host principal para el procesamiento transaccional en el cluster de RabbitMQ es '/produccion_core'.\n</definition>\n<relations>\n- Broker: [[RabbitMQ]]\n- Entorno: [[Producción]]\n</relations>",
            '/save "Vhost RabbitMQ Producción"'
        ),
        (
            "Para el cálculo de hashes de contraseñas queda fijado el factor de coste de bcrypt en 12.",
            "1. Parámetro criptográfico de seguridad.\n2. Descargo el dato de la memoria de contexto hacia la memoria wiki.",
            "<definition>\nEl factor de trabajo (work factor / cost) oficial para el hashing de contraseñas de usuarios mediante bcrypt es 12.\n</definition>\n<relations>\n- Seguridad: [[Hashing de Contraseñas]]\n- Algoritmo: [[Bcrypt]]\n</relations>",
            '/save "Coste Bcrypt Contraseñas"'
        ),
        (
            "Actualiza Redis: el tiempo de expiración por defecto de sesiones de usuario es 86400 segundos.",
            "1. Modificación de parámetro en el concepto Redis.\n2. Aplico /edit para mantener la wiki como fuente fidedigna.",
            "<definition>\nEl motor de almacenamiento en caché Redis gestiona tokens de sesión con un TTL predeterminado de 86400 segundos (24 horas).\n</definition>\n<relations>\n- Servicio: [[Redis]]\n- Módulo: [[Gestión de Sesiones]]\n</relations>",
            '/edit "Redis"'
        ),
        (
            "Decidimos que la política de retención de registros de acceso en S3 será de 365 días.",
            "1. Directiva de cumplimiento y retención de datos.\n2. La guardo de forma estructurada en la wiki.",
            "<definition>\nLa política de ciclo de vida en S3 establece una retención obligatoria de 365 días para todos los registros de acceso auditables.\n</definition>\n<relations>\n- Almacenamiento: [[Amazon S3]]\n- Cumplimiento: [[Auditoría]]\n</relations>",
            '/save "Retención Logs S3"'
        ),
        (
            "Anota que el umbral de disparo de autoescalado horizontal es 75% de CPU sostenido durante 3 minutos.",
            "1. Regla de autoescalado HPA de infraestructura.\n2. Aseguro su persistencia en la wiki.",
            "<definition>\nEl autoescalado horizontal de pods se activa cuando la utilización media de CPU supera el 75% sostenido durante una ventana de 3 minutos.\n</definition>\n<relations>\n- Orquestación: [[Kubernetes]]\n- Mecanismo: [[Autoescalado HPA]]\n</relations>",
            '/save "Umbral Autoescalado HPA"'
        ),
        (
            "El formato para claves primarias en tablas maestras debe ser UUID v7 ordenable por tiempo.",
            "1. Directiva de modelado relacional.\n2. Registro el estándar en la base de conocimientos.",
            "<definition>\nLas tablas maestras de datos adoptan UUID v7 como estándar obligatorio de claves primarias por su ordenación cronológica nativa.\n</definition>\n<relations>\n- Esquema: [[Modelado de Datos]]\n- Estándar: [[UUID]]\n</relations>",
            '/save "Estándar UUID v7 Claves"'
        ),
        (
            "Actualiza PostgreSQL: la extensión pg_trgm está habilitada para búsquedas difusas sobre texto.",
            "1. Extensión de base de datos habilitada.\n2. Actualizo la página de PostgreSQL en la wiki con /edit.",
            "<definition>\nServidor relacional PostgreSQL configurado con la extensión pg_trgm activa para búsquedas de similitud trigram y coincidencia difusa.\n</definition>\n<relations>\n- Base de Datos: [[PostgreSQL]]\n- Funcionalidad: [[Búsqueda Difusa]]\n</relations>",
            '/edit "PostgreSQL"'
        ),
        (
            "Fijamos que los despliegues a producción solo se autorizan los martes y jueves entre las 10:00 y las 14:00.",
            "1. Ventana de despliegue operacional.\n2. Persisto la política para que el sistema consulte siempre este dato en disco.",
            "<definition>\nLa política de cambios estipula que los despliegues a producción se limitan exclusivamente a martes y jueves en la franja horaria de 10:00 a 14:00 UTC.\n</definition>\n<relations>\n- Operaciones: [[Ventana de Despliegue]]\n- Control: [[Gestión de Cambios]]\n</relations>",
            '/save "Ventana de Despliegues Producción"'
        ),
        (
            "El límite de tasa para clientes anónimos es de 60 peticiones por minuto por dirección IP.",
            "1. Parámetro de rate limiting de seguridad perimetral.\n2. Lo almaceno en la wiki.",
            "<definition>\nEl limitador de peticiones aplica una cuota de 60 peticiones por minuto por dirección IP para todo tráfico no autenticado.\n</definition>\n<relations>\n- Seguridad: [[Rate Limiting]]\n- Componente: [[API Gateway]]\n</relations>",
            '/save "Rate Limit Clientes Anónimos"'
        ),
        (
            "Anota que el puerto interno de comunicación gRPC entre servicios se fijó en el 50051.",
            "1. Especificación de puerto de red interna.\n2. Descargo el dato a la wiki para evitar tener que recordarlo en contexto volátil.",
            "<definition>\nEl puerto de red estándar para todas las interfaces de comunicación interna mediante gRPC es el 50051.\n</definition>\n<relations>\n- Protocolo: [[gRPC]]\n- Red: [[Microservicios]]\n</relations>",
            '/save "Puerto gRPC Interno"'
        ),
        (
            "Actualiza Docker: las imágenes base deben ser estrictamente Alpine o distroless para reducir superficie de ataque.",
            "1. Política de empaquetado de contenedores.\n2. Modifico la entrada de Docker en la wiki.",
            "<definition>\nDirectiva de contenedores que exige el uso exclusivo de imágenes base Alpine Linux o distroless para minimizar vulnerabilidades.\n</definition>\n<relations>\n- Plataforma: [[Docker]]\n- Estándar: [[Seguridad en Contenedores]]\n</relations>",
            '/edit "Docker"'
        ),
        (
            "El timeout para la ejecución de lambdas asíncronas no debe superar los 300 segundos.",
            "1. Límite de ejecución serverless.\n2. Guardado estructurado en la base de conocimientos.",
            "<definition>\nEl tiempo máximo de ejecución configurado para funciones serverless en procesamiento asíncrono es de 300 segundos (5 minutos).\n</definition>\n<relations>\n- Cómputo: [[Serverless]]\n- Arquitectura: [[Procesamiento Asíncrono]]\n</relations>",
            '/save "Timeout Funciones Serverless"'
        ),
        (
            "Anota que usamos Sentry como colector central de excepciones no capturadas del frontend y backend.",
            "1. Herramienta corporativa de monitoreo de errores.\n2. La guardo en la wiki.",
            "<definition>\nPlataforma centralizada de observabilidad de fallos Sentry empleada para captura automática de trazas de error y excepciones en tiempo real.\n</definition>\n<relations>\n- Monitoreo: [[Sentry]]\n- Calidad: [[Gestión de Excepciones]]\n</relations>",
            '/save "Plataforma Sentry Excepciones"'
        ),
        (
            "Actualiza FastAPI: todas las rutas deben documentar códigos de respuesta 400 y 500 con modelos Pydantic.",
            "1. Requisito de documentación de API.\n2. Aplico /edit sobre la página de FastAPI.",
            "<definition>\nFramework FastAPI con directiva obligatoria de tipado y documentación de respuestas de error 400 y 500 mediante esquemas Pydantic explícitos.\n</definition>\n<relations>\n- Framework: [[FastAPI]]\n- Documentación: [[OpenAPI]]\n</relations>",
            '/edit "FastAPI"'
        ),
        (
            "El cluster de Kafka tiene activado min.insync.replicas=2 para todas las particiones del topic de pagos.",
            "1. Parámetro de durabilidad de mensajería crítica.\n2. Almacenamiento persistente en la wiki.",
            "<definition>\nConfiguración del topic transaccional de pagos en Kafka con el parámetro min.insync.replicas fijado en 2 para garantizar consistencia fuerte.\n</definition>\n<relations>\n- Mensajería: [[Kafka]]\n- Fiabilidad: [[Consistencia Distribuida]]\n</relations>",
            '/save "Kafka Topic Pagos Réplicas"'
        ),
        (
            "Anota que el cifrado en tránsito entre pods se gestiona mediante mTLS de Istio Service Mesh.",
            "1. Solución de seguridad y malla de servicios.\n2. Persisto en la memoria wiki.",
            "<definition>\nLa seguridad en tránsito entre pods del cluster está enforced mediante mTLS automático provisto por la malla de servicios Istio.\n</definition>\n<relations>\n- Red: [[Istio Service Mesh]]\n- Criptografía: [[mTLS]]\n</relations>",
            '/save "Istio mTLS Inter-Pod"'
        ),
        (
            "Actualiza Git: los commits a la rama main requieren aprobación obligatoria de al menos dos revisores sénior.",
            "1. Política de control de código.\n2. Actualizo la entrada de Git.",
            "<definition>\nFlujo de trabajo Git con protección de rama main que exige dos revisiones aprobadas por ingenieros sénior antes de permitir el merge.\n</definition>\n<relations>\n- Control de Versiones: [[Git]]\n- Calidad: [[Revisión de Código]]\n</relations>",
            '/edit "Git"'
        ),
        (
            "Para el formateo de código Python en pre-commit el estándar oficial es Ruff con longitud de línea 88.",
            "1. Estándar de formateo y linting de código.\n2. Lo descargo en la wiki con /save.",
            "<definition>\nEstándar corporativo de linter y formateador de código Python automatizado en pre-commit mediante Ruff con un ancho de línea fijado en 88 caracteres.\n</definition>\n<relations>\n- Herramientas: [[Ruff]]\n- Ecosistema: [[Python]]\n</relations>",
            '/save "Estándar Ruff Formateo Python"'
        )
    ]

    for q, thought, resp, cmd in b2_data:
        ex.append(_conv(_sys(), q, _gpt(thought, resp, cmd)))

    # =========================================================================
    # BLOQUE 3: RECONCILIACIÓN Y COMPROBACIÓN DE HECHOS (25 ejemplos: 50..74)
    # Cuando el usuario o un agente hace una afirmación que parece contradecir
    # o suponer datos, el agente primero consulta la wiki para contrastar la verdad.
    # =========================================================================
    b3_data = [
        (
            "¿No habíamos quedado en que el puerto de Redis era el 6380 en vez del habitual?",
            "1. El usuario plantea una duda sobre un posible cambio en el puerto de Redis.\n2. No debo responder de memoria o aceptar la afirmación sin contrastar.\n3. Consulto la wiki para verificar la configuración real de Redis.",
            "Voy a contrastar la configuración de Redis registrada en la wiki para confirmar el puerto exacto.",
            '/read "Redis"'
        ),
        (
            "Creo que la base de datos de producción usa MySQL, ¿correcto?",
            "1. El usuario expresa una hipótesis potencialmente errónea.\n2. Compruebo en la wiki cuál es el motor de base de datos oficial.",
            "Reviso la documentación de base de datos en la wiki para contrastar el motor utilizado.",
            '/search "base de datos produccion motor"'
        ),
        (
            "Me dijeron que los backups se hacen cada hora. ¿Es así?",
            "1. Afirmación no contrastada sobre frecuencia de backups.\n2. Verifico el registro formal en la wiki antes de validar o desmentir.",
            "Consulto la política de copias de seguridad en la memoria wiki para verificar la periodicidad.",
            '/search "politica backups periodicidad"'
        ),
        (
            "¿La autenticación se realiza mediante cookies de sesión o con JWT?",
            "1. Disyuntiva de arquitectura técnica.\n2. Consulto la entrada de autenticación en la wiki.",
            "Reviso la entrada de autenticación en la wiki para confirmar el mecanismo oficial.",
            '/search "mecanismo autenticacion oficial sesion JWT"'
        ),
        (
            "Tengo entendido que el timeout de la API está en 5 segundos. ¿Me lo confirmas?",
            "1. Solicitud de confirmación de un parámetro numérico.\n2. No confirmo de memoria; contrasto la wiki.",
            "Compruebo el valor del timeout documentado en la wiki antes de confirmar.",
            '/search "timeout API Gateway configuracion"'
        ),
        (
            "Alguien mencionó que migramos el frontend de React a Vue el mes pasado, ¿tenemos registro de eso?",
            "1. Duda sobre un cambio tecnológico mayor.\n2. Busco en la base de conocimientos qué framework figura como estándar.",
            "Voy a buscar en la wiki qué tecnología frontend figura en el stack oficial.",
            '/search "framework frontend oficial stack"'
        ),
        (
            "¿El tamaño máximo de subida de archivos es de 50 MB o de 100 MB?",
            "1. Pregunta sobre límite de carga con valores conflictivos.\n2. Leo la documentación del servicio de almacenamiento en la wiki.",
            "Consulto la especificación del servicio de archivos en la wiki para resolver la cifra exacta.",
            '/search "limite tamano subida archivos storage"'
        ),
        (
            "Un desarrollador dice que no hace falta escribir tests unitarios para los repositorios. ¿Qué dice nuestra norma?",
            "1. Conflicto de prácticas de desarrollo con una regla del equipo.\n2. Verifico la directiva de testing en la wiki.",
            "Voy a revisar el estándar de calidad y pruebas unitarias registrado en la wiki.",
            '/search "estandar pruebas unitarias cobertura requisitos"'
        ),
        (
            "¿Es verdad que Kafka está configurado con retención infinita de mensajes?",
            "1. Hipótesis sobre la política de retención de topics.\n2. Reviso la configuración de Kafka en la memoria local.",
            "Consulto la configuración de retención de Kafka documentada en la wiki.",
            '/search "Kafka retencion mensajes politica"'
        ),
        (
            "¿Nuestro entorno soporta WebSocket o solo HTTP/2?",
            "1. Duda de compatibilidad de protocolos en la infraestructura.\n2. Busco la especificación de red en la wiki.",
            "Compruebo en la wiki los protocolos de comunicación habilitados en la plataforma.",
            '/search "soporte protocolos WebSocket HTTP2 infraestructura"'
        ),
        (
            "Me comentan que el rate limit no aplica a llamadas internas de microservicios, ¿puedes verificarlo?",
            "1. Regla de excepción de seguridad en duda.\n2. Consulto la política de rate limiting en la memoria persistente.",
            "Reviso la política de rate limiting en la wiki para comprobar si contempla excepciones internas.",
            '/search "rate limiting excepciones trafico interno microservicios"'
        ),
        (
            "¿La réplica de lectura de PostgreSQL atiende consultas en tiempo real o tiene lag configurado?",
            "1. Pregunta técnica de consistencia en replicación.\n2. Corroboro en la wiki el modo de réplica documentado.",
            "Voy a verificar la configuración de réplica de PostgreSQL en la wiki.",
            '/search "PostgreSQL replica lectura sincronizacion modo"'
        ),
        (
            "¿Tenemos documentado si el endpoint de pagos admite reintentos idempotentes?",
            "1. Consulta sobre soporte de idempotencia en transacciones.\n2. Reviso la especificación en la wiki.",
            "Consulto en la base de conocimientos la especificación de idempotencia de pagos.",
            '/search "pagos idempotencia cabecera soporte"'
        ),
        (
            "¿El formato de logs que usamos es texto plano o JSON estructurado?",
            "1. Estándar de observabilidad en duda.\n2. Busco la directiva de logging en la wiki.",
            "Compruebo la convención de formato de logging en la memoria wiki.",
            '/search "formato logs estructurado JSON estandar"'
        ),
        (
            "¿Quién autoriza los pases a producción fuera de horario habitual?",
            "1. Proceso de gobernanza y autorizaciones.\n2. Busco el protocolo de cambios de emergencia en la wiki.",
            "Reviso el protocolo de pases de emergencia documentado en la wiki.",
            '/search "despliegues emergencia autorizacion responsable protocolo"'
        ),
        (
            "¿Usamos Celery con Redis o con RabbitMQ en el backend de tareas?",
            "1. Disyuntiva entre dos brokers posibles.\n2. Consulto el concepto de Celery en la wiki para resolver con certeza.",
            "Voy a leer la entrada de Celery en la wiki para verificar el broker oficial.",
            '/read "Celery"'
        ),
        (
            "¿Qué algoritmo de balanceo tiene configurado Nginx en el upstream de usuarios?",
            "1. Pregunta sobre la configuración del reverse proxy.\n2. Leo la entrada de Nginx en la wiki.",
            "Consulto la configuración de upstream en la entrada de Nginx de la wiki.",
            '/read "Nginx"'
        ),
        (
            "¿El cifrado de contraseñas se hace con Argon2id o con Bcrypt?",
            "1. Duda técnica sobre el algoritmo de hashing en uso.\n2. Busco la directiva registrada en la wiki.",
            "Compruebo en la wiki el algoritmo de cifrado de contraseñas estandarizado.",
            '/search "algoritmo hashing contrasenas bcrypt argon2"'
        ),
        (
            "¿La caché de páginas web se invalida por tiempo o por webhook de publicación?",
            "1. Mecanismo de invalidación de caché en duda.\n2. Reviso la entrada de almacenamiento en caché en la wiki.",
            "Voy a consultar en la base de conocimientos la estrategia de invalidación de caché.",
            '/search "estrategia invalidacion cache TTL webhook"'
        ),
        (
            "¿Se permite el uso de claves API hardcodeadas en archivos de test locales?",
            "1. Pregunta sobre política de seguridad y secretos.\n2. Busco la directiva de gestión de secretos en la wiki.",
            "Verifico en la wiki la directiva de seguridad sobre credenciales en entornos de test.",
            '/search "seguridad secretos credenciales variables entorno tests"'
        ),
        (
            "¿El servicio de búsqueda corre sobre ElasticSearch o sobre OpenSearch?",
            "1. Identidad del motor de búsqueda en cuestión.\n2. Reviso en la wiki cuál es el motor activo.",
            "Consulto en la memoria wiki el motor de búsqueda implementado.",
            '/search "motor busqueda cluster ElasticSearch OpenSearch"'
        ),
        (
            "¿El tiempo de vida de los refresh tokens es de 7 días o de 30 días?",
            "1. Duración de tokens de refresco.\n2. Verifico la directiva de autenticación en la wiki.",
            "Compruebo en la wiki la vigencia configurada para los tokens de refresco.",
            '/search "vigencia duracion refresh tokens autenticacion"'
        ),
        (
            "¿Es obligatorio firmar todos los commits de Git con clave GPG?",
            "1. Directiva de integridad de código.\n2. Busco la regla en la wiki antes de responder afirmativamente.",
            "Reviso la política de firmas GPG en el flujo de Git en la wiki.",
            '/search "Git firma commits GPG obligatoria politica"'
        ),
        (
            "¿Cuál es el umbral de memoria para alertar sobre fugas en los workers?",
            "1. Métrica de alerta operacional.\n2. Consulto el runbook de alertas en la wiki.",
            "Voy a consultar en la base de conocimientos el umbral de alerta de memoria para workers.",
            '/search "umbral alerta memoria workers leak"'
        ),
        (
            "¿El sistema de archivos de almacenamiento es MinIO S3 o un NFS compartido?",
            "1. Tecnología de almacenamiento de objetos.\n2. Consulto la entrada técnica en la wiki.",
            "Compruebo en la wiki la infraestructura de almacenamiento de archivos en uso.",
            '/search "almacenamiento objetos MinIO NFS infraestructura"'
        )
    ]

    for q, thought, resp, cmd in b3_data:
        ex.append(_conv(_sys(), q, _gpt(thought, resp, cmd)))

    # =========================================================================
    # BLOQUE 4: EXPLORACIÓN GUIADA DE ENLACES DE GRAFO (25 ejemplos: 75..99)
    # Al leer o referenciar un concepto, el agente identifica enlaces [[Concepto]]
    # y en lugar de suponer su significado, ejecuta /read para seguir el enlace.
    # =========================================================================
    b4_data = [
        (
            "He leído que [[Microservicios]] depende de [[API Gateway]]. Muéstrame qué dice la wiki sobre el API Gateway.",
            "1. El usuario hace referencia a un enlace de concepto identificado en la wiki.\n2. Debo navegar el enlace leyendo la entrada [[API Gateway]] sin especular.",
            "Accedo a la página del API Gateway en la wiki para consultar su definición y dependencias.",
            '/read "API Gateway"'
        ),
        (
            "En la página de [[Kubernetes]] vi una mención a [[Pods]]. ¿Cómo están definidos en la memoria?",
            "1. Solicitud de profundización en un concepto vinculado del grafo.\n2. Empleo /read sobre el concepto enlazado.",
            "Voy a leer la entrada de Pods en la wiki para ver su definición exacta.",
            '/read "Pods"'
        ),
        (
            "La definición de [[Docker]] cita a [[Contenedores OCI]]. Navega hacia ese concepto.",
            "1. El usuario me pide expresamente explorar el enlace conceptual.\n2. Leo la entrada de Contenedores OCI.",
            "Abro la entrada de Contenedores OCI en la base de conocimientos.",
            '/read "Contenedores OCI"'
        ),
        (
            "Revisando [[FastAPI]], observo que enlaza con [[Pydantic]]. Quiero ver los detalles de Pydantic.",
            "1. Exploración de grafo conceptual.\n2. Ejecuto /read para obtener la información de Pydantic persistida en la wiki.",
            "Consulto la ficha completa de Pydantic en la memoria wiki.",
            '/read "Pydantic"'
        ),
        (
            "En [[Clean Architecture]] se menciona la capa de [[Casos de Uso]]. Muéstrame esa entrada.",
            "1. Navegación directa a través de un enlace de arquitectura.\n2. Empleo /read sobre Casos de Uso.",
            "Accedo a la entrada de Casos de Uso para inspeccionar su descripción en la wiki.",
            '/read "Casos de Uso"'
        ),
        (
            "El concepto [[JWT]] está conectado con [[Criptografía Asimétrica]]. Explora ese vínculo.",
            "1. Consulta de concepto vinculado en el grafo.\n2. Leo la entrada enlazada con /read.",
            "Voy a abrir la página de Criptografía Asimétrica en la wiki.",
            '/read "Criptografía Asimétrica"'
        ),
        (
            "En la entrada de [[PostgreSQL]] se habla de [[Índices B-Tree]]. Necesito ver esa especificación.",
            "1. Navegación hacia un concepto especializado vinculado.\n2. Ejecuto /read para cargar Índices B-Tree.",
            "Leo la documentación de Índices B-Tree guardada en la base de datos conceptual.",
            '/read "Índices B-Tree"'
        ),
        (
            "Al consultar [[Prometheus]] aparece un enlace a [[Alertmanager]]. ¿Qué tenemos registrado de él?",
            "1. Exploración de componente enlazado.\n2. Utilizo /read para inspeccionar la wiki.",
            "Consulto la entrada de Alertmanager en la wiki local.",
            '/read "Alertmanager"'
        ),
        (
            "En [[RabbitMQ]] se referencia al concepto [[Protocolo AMQP]]. ¿Qué detalles contiene?",
            "1. Enlace de protocolo técnico identificado.\n2. Leo la entrada correspondiente con /read.",
            "Voy a leer la ficha técnica del Protocolo AMQP en la memoria wiki.",
            '/read "Protocolo AMQP"'
        ),
        (
            "El documento de [[Celery]] cita a [[Brokers de Mensajes]]. Muéstrame esa entrada.",
            "1. Concepto arquitectónico enlazado.\n2. Realizo la lectura con /read.",
            "Abro la entrada de Brokers de Mensajes en la base de conocimientos.",
            '/read "Brokers de Mensajes"'
        ),
        (
            "En la página de [[Nginx]] se menciona la [[Terminación SSL]]. Quiero ver su configuración.",
            "1. Enlace a procedimiento de seguridad web.\n2. Empleo /read sobre Terminación SSL.",
            "Leo la página de Terminación SSL registrada en la memoria wiki.",
            '/read "Terminación SSL"'
        ),
        (
            "Al ver [[Git]] encuentro una referencia a [[Flujo de Ramas]]. ¿Cómo lo tenemos documentado?",
            "1. Navegación por grafo conceptual.\n2. Ejecuto /read para obtener la ficha de Flujo de Ramas.",
            "Voy a revisar el concepto Flujo de Ramas en la wiki.",
            '/read "Flujo de Ramas"'
        ),
        (
            "La entrada de [[Kafka]] menciona [[Particionado de Topics]]. Inspecciona ese concepto.",
            "1. Navegación a concepto técnico vinculado.\n2. Leo Particionado de Topics con /read.",
            "Accedo a la página de Particionado de Topics en la base de conocimientos.",
            '/read "Particionado de Topics"'
        ),
        (
            "En [[Scrum]] aparece el enlace a [[Sprint Planning]]. Muestra lo que tenemos registrado.",
            "1. Ceremonia ágil vinculada al concepto Scrum.\n2. Empleo /read sobre Sprint Planning.",
            "Consulto la entrada de Sprint Planning en la wiki.",
            '/read "Sprint Planning"'
        ),
        (
            "Al consultar [[Redis]] hay un enlace hacia [[Caché en Memoria]]. Quiero examinarlo.",
            "1. Exploración de patrón conceptual enlazado.\n2. Leo Caché en Memoria con /read.",
            "Abro la página de Caché en Memoria en la memoria persistente.",
            '/read "Caché en Memoria"'
        ),
        (
            "En la ficha de [[GraphQL]] se cita a [[Resolvers]]. Navega hacia ese término.",
            "1. Componente técnico enlazado en GraphQL.\n2. Utilizo /read para inspeccionar Resolvers.",
            "Voy a leer la entrada de Resolvers en la base de datos conceptual.",
            '/read "Resolvers"'
        ),
        (
            "El concepto [[OAuth 2.0]] enlaza con [[Servidor de Autorización]]. ¿Qué dice la wiki?",
            "1. Rol de seguridad enlazado en el protocolo OAuth.\n2. Ejecuto /read sobre Servidor de Autorización.",
            "Consulto la documentación del Servidor de Autorización en la wiki.",
            '/read "Servidor de Autorización"'
        ),
        (
            "En [[Domain-Driven Design]] se referencia a [[Bounded Context]]. Muéstrame esa entrada.",
            "1. Patrón central de diseño táctico/estratégico enlazado.\n2. Empleo /read para obtener Bounded Context.",
            "Leo la página de Bounded Context en la memoria wiki.",
            '/read "Bounded Context"'
        ),
        (
            "La página de [[WebSockets]] enlaza con [[Protocolo TCP]]. Inspecciona esa relación.",
            "1. Protocolo de transporte base enlazado.\n2. Leo Protocolo TCP con /read.",
            "Voy a consultar la ficha del Protocolo TCP en la base de conocimientos.",
            '/read "Protocolo TCP"'
        ),
        (
            "Al ver [[MinIO]] se menciona la compatibilidad con [[Amazon S3 API]]. ¿Qué dice esa entrada?",
            "1. Especificación de interfaz enlazada.\n2. Utilizo /read para examinar Amazon S3 API.",
            "Abro la página de Amazon S3 API en la memoria wiki.",
            '/read "Amazon S3 API"'
        ),
        (
            "En [[Pytest]] hay un enlace a [[Fixtures de Prueba]]. Navega hacia él.",
            "1. Mecanismo de testing enlazado.\n2. Ejecuto /read sobre Fixtures de Prueba.",
            "Consulto la definición de Fixtures de Prueba en la wiki.",
            '/read "Fixtures de Prueba"'
        ),
        (
            "La entrada de [[Grafana]] enlaza con [[Fuentes de Datos]]. Quiero ver esa página.",
            "1. Concepto de observabilidad vinculado.\n2. Leo Fuentes de Datos con /read.",
            "Voy a leer la entrada de Fuentes de Datos en la wiki.",
            '/read "Fuentes de Datos"'
        ),
        (
            "En [[HTTP/2]] aparece la referencia a [[Multiplexación de Streams]]. Muéstrame su contenido.",
            "1. Funcionalidad de transporte enlazada.\n2. Empleo /read para consultar Multiplexación de Streams.",
            "Accedo a la página de Multiplexación de Streams en la base de conocimientos.",
            '/read "Multiplexación de Streams"'
        ),
        (
            "Al examinar [[Locust]] encuentro un enlace a [[Pruebas de Carga]]. Ábrelo para ver su definición.",
            "1. Disciplina de pruebas enlazada.\n2. Leo Pruebas de Carga con /read.",
            "Consulto el concepto de Pruebas de Carga en la memoria wiki.",
            '/read "Pruebas de Carga"'
        ),
        (
            "En la entrada de [[NDJSON]] se referencia a [[ElasticSearch Ingestion]]. ¿Qué tenemos guardado?",
            "1. Integración de datos enlazada.\n2. Utilizo /read para ver ElasticSearch Ingestion.",
            "Voy a abrir la entrada de ElasticSearch Ingestion en la base de datos conceptual.",
            '/read "ElasticSearch Ingestion"'
        )
    ]

    for q, thought, resp, cmd in b4_data:
        ex.append(_conv(_sys(), q, _gpt(thought, resp, cmd)))

    assert len(ex) == 100, f"Error: esperados 100 ejemplos, obtenidos {len(ex)}"

    # =========================================================================
    # APLICACIÓN DE ESTÁNDAR MULTI-FUENTE
    # Convertimos 20 ejemplos (5 por cada bloque) para que provengan de agentes
    # pares en la red ([DE: <NombreAgente>]), integrando el reconocimiento en <thought>.
    # =========================================================================
    agent_conversions = [
        # Bloque 1: consultas técnicas entre pares
        (2,  "Agente par solicita verificación fáctica de política de backups."),
        (7,  "Agente par consulta timeout transaccional en la memoria compartida."),
        (12, "Agente par pide confirmar la herramienta oficial de seguridad."),
        (17, "Agente par solicita directiva de cabeceras de red."),
        (22, "Agente par consulta la convención de nombrado de métricas."),
        # Bloque 2: persistencia de datos transmitidos por pares
        (27, "Agente par transmite nuevo vhost de mensajería para persistencia."),
        (32, "Agente par reporta estándar de identificadores UUID para almacenar."),
        (37, "Agente par transmite puerto oficial de comunicación gRPC."),
        (42, "Agente par delega persistencia de configuración del topic Kafka."),
        (47, "Agente par transmite estándar corporativo de formateo Python."),
        # Bloque 3: contrastación y reconciliación de hechos entre agentes
        (52, "Agente par plantea duda sobre periodicidad de copias de seguridad."),
        (57, "Agente par solicita comprobación sobre límite de subida de archivos."),
        (62, "Agente par consulta si existe soporte formal de idempotencia."),
        (67, "Agente par busca resolver discrepancia sobre algoritmo de hashing."),
        (72, "Agente par pide verificar si la firma GPG es obligatoria."),
        # Bloque 4: navegación de enlaces de grafo delegada
        (77, "Agente par solicita explorar enlace conceptual de FastAPI."),
        (82, "Agente par delega lectura del enlace Protocolo AMQP."),
        (87, "Agente par pide inspeccionar el enlace Sprint Planning."),
        (92, "Agente par solicita explorar el enlace Bounded Context."),
        (97, "Agente par delega lectura de Multiplexación de Streams."),
    ]

    for i, (idx, suffix) in enumerate(agent_conversions):
        name = _agent_sender(i)
        convs = ex[idx]["conversations"]
        original_human = convs[1]["value"]
        convs[1]["value"] = f"[DE: {name}]\n{original_human}"

        # Insertar reconocimiento de emisor en el thought
        gpt_val = convs[2]["value"]
        t_start = gpt_val.find("<thought>")
        t_end = gpt_val.find("</thought>")
        if t_start != -1 and t_end != -1:
            body = gpt_val[t_start + 9:t_end]
            lines = body.split("\n")
            new_lines = []
            for l in lines:
                m = re.match(r"^(\d+)\. (.+)", l.strip())
                if m:
                    new_lines.append(f"{int(m.group(1)) + 1}. {m.group(2)}")
                else:
                    new_lines.append(l)
            sender_line = f"1. Emisor Agente ({name}). {suffix}"
            new_body = "\n".join([sender_line] + new_lines)
            convs[2]["value"] = gpt_val[:t_start + 9] + new_body + gpt_val[t_end:]

    return ex


def main():
    examples = create_examples()
    out_dir = Path(__file__).resolve().parent / "data" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "dataset_ft6_wiki_grounding.jsonl"

    with open(out_file, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    agent_count = sum(1 for e in examples if "[DE:" in e["conversations"][1]["value"])
    human_count = len(examples) - agent_count

    print(f"[OK] Dataset FT6 generado en: {out_file.resolve()}")
    print(f"     Total de ejemplos: {len(examples)}")
    print(f"     - Bloque 1 (Anti-Alucinación / Verificación previa) : 25 ejemplos")
    print(f"     - Bloque 2 (Persistencia / Context Offloading)      : 25 ejemplos")
    print(f"     - Bloque 3 (Reconciliación y Comprobación Hechos)   : 25 ejemplos")
    print(f"     - Bloque 4 (Exploración Enlaces de Grafo)           : 25 ejemplos")
    print(f"     Distribución multi-fuente: {agent_count} Agentes / {human_count} Humanos")


if __name__ == "__main__":
    main()

