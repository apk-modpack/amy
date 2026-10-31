"""Constructor de 80 ejemplos complementarios para FT3.
Lleva el total de FT3 de 20 a exactamente 100 ejemplos únicos.

Especializado en:
- Bloque A: NUNCA emitir frases de intención ("Voy a...") en <response> al usar /save o /edit (20 ejemplos).
- Bloque B: Respuestas directas a consultas informativas sin invocar /save ni /edit (20 ejemplos).
- Bloque C: Ciclo ReAct /search -> /edit con definición estructurada inmediata (20 ejemplos).
- Bloque D: Recuperación inmediata y limpia tras rechazos del validador de guardado (20 ejemplos).
"""

def get_ft3_extra_examples(_conv, _sys, _wiki, _human, _gpt):
    exs = []

    # =========================================================================
    # BLOQUE A EXTENDIDO: Cero frases de anuncio en /save o /edit (20 ejemplos)
    # =========================================================================
    no_announcements = [
        (
            "Registra que Prometheus es un sistema de monitorización time-series con lenguaje PromQL.",
            "Prometheus",
            "1. El usuario aporta definición completa de Prometheus.\n2. Debo usar /save.\n3. En <response> emito el XML directo sin anuncios conversacionales.",
            "<definition>\nPrometheus es un sistema de monitorización y alertas que recopila y almacena métricas como series temporales, ofreciendo el lenguaje PromQL para consultas.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Sistema de Monitorización\">Herramienta de observabilidad.</relation>\n</relations>",
            '/save "Prometheus"'
        ),
        (
            "Anota que PostgreSQL soporta índices GIN para búsquedas eficientes sobre campos JSONB.",
            "PostgreSQL",
            "1. Información técnica sobre índices GIN.\n2. Emito el XML directo en <response>.\n3. Ejecuto /edit.",
            "<definition>\nPostgreSQL es un sistema gestor de bases de datos relacional y transaccional con soporte nativo para índices GIN sobre columnas de tipo JSONB.\n</definition>",
            '/edit "PostgreSQL"'
        ),
        (
            "Guarda que Docker Compose utiliza archivos YAML declarativos para levantar servicios multicontenedor.",
            "Docker Compose",
            "1. Definición para Docker Compose.\n2. Cero frases de intención.\n3. Formato micro-XML estricto.",
            "<definition>\nDocker Compose es la herramienta de orquestación local que define y ejecuta aplicaciones multicontenedor mediante ficheros de configuración YAML declarativos.\n</definition>\n<relations>\n  <relation type=\"part_of\" target=\"Docker\">Herramienta complementaria de contenedores.</relation>\n</relations>",
            '/save "Docker Compose"'
        ),
        (
            "Registra que RabbitMQ utiliza el protocolo AMQP 0-9-1 para enrutamiento flexible de mensajes.",
            "RabbitMQ",
            "1. Nuevo concepto RabbitMQ.\n2. Guardado estructurado inmediato sin comentarios previos.",
            "<definition>\nRabbitMQ es un servidor de mensajería asíncrona que implementa el protocolo AMQP 0-9-1 con exchanges direct, fanout, topic y headers.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Message Broker\">Intermediario de mensajes distribuido.</relation>\n</relations>",
            '/save "RabbitMQ"'
        ),
        (
            "Añade que FastAPI compila los esquemas Pydantic a especificaciones OpenAPI 3.0 automáticamente.",
            "FastAPI",
            "1. Edición de FastAPI con detalle técnico.\n2. Emito el XML de definición sin anuncios.",
            "<definition>\nFastAPI es un framework web de alto rendimiento para Python que genera especificaciones OpenAPI 3.0 interactivas a partir de esquemas Pydantic.\n</definition>",
            '/edit "FastAPI"'
        ),
        (
            "Guarda que Celery soporta Redis y RabbitMQ como brokers de transporte de mensajes.",
            "Celery",
            "1. Definición para Celery.\n2. Ejecuto /save con micro-XML puro.",
            "<definition>\nCelery es un sistema de colas de tareas distribuidas en segundo plano para Python que utiliza RabbitMQ o Redis como brokers de transporte.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Cola de Tareas\">Gestor asíncrono de jobs.</relation>\n</relations>",
            '/save "Celery"'
        ),
        (
            "Registra que Nginx soporta terminación SSL/TLS y compresión Gzip nativa.",
            "Nginx",
            "1. Detalle técnico de Nginx.\n2. Ejecuto /edit emitiendo el XML en <response>.",
            "<definition>\nNginx es un servidor web y proxy inverso asíncrono con capacidades integradas para terminación SSL/TLS y compresión HTTP mediante Gzip.\n</definition>",
            '/edit "Nginx"'
        ),
        (
            "Anota que Pytest permite parametrizar funciones de test mediante el decorador @pytest.mark.parametrize.",
            "Pytest",
            "1. Concepto técnico sobre Pytest.\n2. XML estructurado directo.",
            "<definition>\nPytest es un framework de testing en Python que soporta parametrización declarativa de casos de prueba usando el decorador @pytest.mark.parametrize.\n</definition>",
            '/edit "Pytest"'
        ),
        (
            "Guarda que MinIO proporciona una API 100% compatible con Amazon S3 para almacenamiento de objetos.",
            "MinIO",
            "1. Nuevo concepto MinIO.\n2. Formato XML limpio sin 'Voy a registrar'.",
            "<definition>\nMinIO es un servidor de almacenamiento de objetos distribuido de alto rendimiento compatible con la API de Amazon S3.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Almacenamiento de Objetos\">Servidor S3 compatible.</relation>\n</relations>",
            '/save "MinIO"'
        ),
        (
            "Registra que Grafana permite definir alertas mediante evaluación periódica de expresiones PromQL.",
            "Grafana",
            "1. Ampliación de Grafana.\n2. XML directo en <response> y /edit en <commands>.",
            "<definition>\nGrafana es una plataforma de visualización interactiva y dashboards con motor unificado de alertas basado en consultas periódicas sobre PromQL.\n</definition>",
            '/edit "Grafana"'
        ),
        (
            "Añade que el protocolo NDJSON delimita objetos JSON mediante caracteres de nueva línea.",
            "NDJSON",
            "1. Guardado de NDJSON.\n2. Sin charla introductoria.",
            "<definition>\nNDJSON (Newline-Delimited JSON) es un estándar de transmisión que estructura secuencias de documentos JSON independientes separados por saltos de línea '\\n'.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Formato de Datos\">Protocolo de serialización por líneas.</relation>\n</relations>",
            '/save "NDJSON"'
        ),
        (
            "Registra que JWT se divide en tres segmentos separados por puntos: cabecera, carga útil y firma.",
            "JWT",
            "1. Detalle anatómico de JWT.\n2. XML directo en /edit.",
            "<definition>\nJSON Web Token (JWT) es un estándar compacto de autorización estructurado en tres partes codificadas en Base64Url separadas por puntos: header, payload y signature.\n</definition>",
            '/edit "JWT"'
        ),
        (
            "Guarda que Redis Cluster proporciona particionamiento automático de datos entre múltiples nodos maestros.",
            "Redis Cluster",
            "1. Nuevo concepto Redis Cluster.\n2. /save sin preámbulos.",
            "<definition>\nRedis Cluster es la solución distribuida de Redis que reparte automáticamente las claves entre 16384 slots hash distribuidos en múltiples nodos maestros.\n</definition>\n<relations>\n  <relation type=\"part_of\" target=\"Redis\">Modo distribuido de Redis.</relation>\n</relations>",
            '/save "Redis Cluster"'
        ),
        (
            "Anota que Kubernetes organiza los contenedores en unidades atómicas de despliegue denominadas Pods.",
            "Kubernetes Pod",
            "1. Concepto Pod en Kubernetes.\n2. Micro-XML directo.",
            "<definition>\nUn Pod es la unidad mínima de ejecución en Kubernetes que encapsula uno o varios contenedores estrechamente acoplados que comparten red y almacenamiento.\n</definition>\n<relations>\n  <relation type=\"part_of\" target=\"Kubernetes\">Unidad básica de cómputo.</relation>\n</relations>",
            '/save "Kubernetes Pod"'
        ),
        (
            "Registra que Git Rebase vuelve a aplicar commits sobre la punta de otra rama base sin crear commit de merge.",
            "Git Rebase",
            "1. Definición para Git Rebase.\n2. Formato XML en <response>.",
            "<definition>\nGit Rebase es un comando de Git que traslada una secuencia de commits al extremo superior de una nueva rama base manteniendo un historial lineal.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Comando Git\">Operación de reorganización de historial.</relation>\n</relations>",
            '/save "Git Rebase"'
        ),
        (
            "Guarda que el algoritmo RS256 en JWT emplea una clave privada RSA para firmar y una clave pública para verificar.",
            "RS256",
            "1. Concepto RS256.\n2. XML estructurado puro.",
            "<definition>\nRS256 es un algoritmo de firma digital asimétrico que utiliza pares de claves RSA y función hash SHA-256 para firmar y validar tokens JWT.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Algoritmo Criptográfico\">Algoritmo asimétrico de firma.</relation>\n</relations>",
            '/save "RS256"'
        ),
        (
            "Añade que Pydantic v2 realiza la coerción estricta de tipos mediante su decorador @validate_call.",
            "Pydantic",
            "1. Edición de Pydantic.\n2. XML sin comentarios conversacionales.",
            "<definition>\nPydantic es una librería de validación de datos que incluye el decorador @validate_call para imponer validación estricta de argumentos y retornos en funciones Python.\n</definition>",
            '/edit "Pydantic"'
        ),
        (
            "Registra que Locust define escenarios de pruebas de carga como código en Python estándar.",
            "Locust",
            "1. Definición de Locust.\n2. Emito XML en /save.",
            "<definition>\nLocust es una herramienta de pruebas de carga y rendimiento de código abierto que permite definir escenarios y comportamiento de usuarios mediante scripts en Python.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Herramienta de Rendimiento\">Generador de carga distribuida.</relation>\n</relations>",
            '/save "Locust"'
        ),
        (
            "Guarda que el protocolo HTTP/2 introduce multiplexación de peticiones sobre una única conexión TCP.",
            "HTTP/2",
            "1. Concepto HTTP/2.\n2. Guardado limpio sin anuncios.",
            "<definition>\nHTTP/2 es una revisión del protocolo de red HTTP que introduce multiplexación binaria de streams sobre una única conexión TCP continua.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Protocolo de Red\">Evolución de HTTP/1.1.</relation>\n</relations>",
            '/save "HTTP/2"'
        ),
        (
            "Anota que PostgreSQL soporta particionamiento declarativo de tablas por rango, lista o hash.",
            "Particionamiento PostgreSQL",
            "1. Nuevo concepto particionamiento.\n2. XML estructurado directo.",
            "<definition>\nEl particionamiento declarativo en PostgreSQL permite dividir una tabla lógica grande en particiones físicas individuales basadas en rango, lista o hash.\n</definition>\n<relations>\n  <relation type=\"part_of\" target=\"PostgreSQL\">Técnica de optimización de datos.</relation>\n</relations>",
            '/save "Particionamiento PostgreSQL"'
        )
    ]
    for q, title, th, resp, cmd in no_announcements:
        exs.append(_conv(_sys(), _human(q), _gpt(th, resp, cmd)))

    # =========================================================================
    # BLOQUE B EXTENDIDO: Consultas informativas puras (CERO /save o /edit) (20 ejemplos)
    # =========================================================================
    pure_queries = [
        ("Nginx", "Proxy inverso HTTP y balanceador asíncrono.", "¿Qué ventajas ofrece Nginx frente a servidores tradicionales?", "1. Consulta puramente informativa.\n2. La memoria wiki ya tiene Nginx.\n3. PROHIBIDO usar /save o /edit.\n4. Respondo directamente.", "[[Nginx]] ofrece una arquitectura asíncrona basada en eventos que le permite atender miles de conexiones concurrentes con un consumo mínimo de memoria, a diferencia del modelo de proceso por hilo de servidores tradicionales."),
        ("PostgreSQL", "Motor relacional ACID con replicación streaming y soporte JSONB.", "¿Por qué elegimos PostgreSQL como base de datos?", "1. Pregunta sobre justificación técnica.\n2. No hay datos nuevos que guardar.\n3. <commands> debe quedar vacío.", "Elegimos [[PostgreSQL]] por su estricta conformidad con ACID, su madurez en integridad transaccional y su excelente rendimiento con datos semiestructurados gracias al tipo JSONB."),
        ("Kafka", "Plataforma de eventos distribuida y particionada.", "¿Cómo garantiza Kafka que no se pierdan mensajes?", "1. Consulta conceptual.\n2. Cero comandos de guardado.\n3. Respondo con el conocimiento en memoria.", "[[Kafka]] garantiza la durabilidad persistiendo los eventos en disco dentro de particiones inmutables y replicándolos entre múltiples brokers del clúster con acuses de recibo configurables."),
        ("FastAPI", "Framework asíncrono Python con OpenAPI y tipado Pydantic.", "¿Qué beneficios aporta FastAPI al desarrollo?", "1. Pregunta de opinión o resumen.\n2. Respondo directamente en <response>.", "[[FastAPI]] agiliza el desarrollo mediante tipado estricto, genera documentación OpenAPI interactiva sin esfuerzo adicional y aprovecha async/await para maximizar el throughput de I/O."),
        ("Docker", "Aislamiento de dependencias mediante contenedores Linux.", "¿Qué problema resuelve Docker en nuestro flujo?", "1. Consulta conceptual.\n2. Sin comandos de guardado.", "[[Docker]] elimina el problema del 'en mi máquina funciona' empaquetando la aplicación con todas sus dependencias exactas en una imagen inmutable ejecutable en cualquier entorno."),
        ("Redis", "Almacén en memoria para caché y rate limiting.", "¿Por qué es tan rápido Redis comparado con una base de datos en disco?", "1. Pregunta informativa sobre Redis.\n2. Respondo enciclopédicamente.", "[[Redis]] opera íntegramente en la memoria RAM con estructuras de datos nativas optimizadas, evitando los retardos de lectura y escritura asociados a discos persistentes."),
        ("Pytest", "Framework de pruebas unitarias con fixtures modulares.", "¿Qué ventaja tienen los fixtures de Pytest sobre setUp()?", "1. Consulta sobre mejores prácticas de testing.\n2. Respondo sin invocar /save.", "Los fixtures de [[Pytest]] ofrecen mayor modularidad y reutilización que setUp(), ya que admiten inyección de dependencias explícita y gestión granular del ciclo de vida con yield."),
        ("RabbitMQ", "Message broker AMQP con colas y exchanges.", "¿En qué se diferencia RabbitMQ de Kafka?", "1. Pregunta de comparación conceptual.\n2. Cero /save o /edit.", "[[RabbitMQ]] es un broker orientado a mensajes individuales con enrutamiento dinámico y acuses de recibo en colas, mientras que [[Kafka]] es un log de eventos distribuido optimizado para streaming masivo."),
        ("Prometheus", "Sistema de métricas time-series con recolección pull.", "¿Qué diferencia el modelo pull de Prometheus del modelo push?", "1. Consulta sobre arquitectura de observabilidad.\n2. Respondo directamente.", "El modelo pull de [[Prometheus]] sondea periódicamente los endpoints de métricas de los servicios, lo que permite detectar caídas de instancias y desacoplar la carga de monitorización del servicio monitorizado."),
        ("Grafana", "Plataforma de tableros interactivos para visualización de métricas.", "¿Cómo ayuda Grafana al equipo de operaciones?", "1. Pregunta informativa.\n2. Sin comandos.", "[[Grafana]] unifica métricas de diferentes fuentes en tableros gráficos en tiempo real, permitiendo al equipo correlacionar latencias, uso de CPU y tasas de error en un único panel."),
        ("JWT", "Token de autorización RFC 7519 compacto y firmado.", "¿Por qué JWT evita consultar la base de datos en cada petición?", "1. Consulta sobre tokens sin estado (stateless).\n2. Respondo claramente.", "[[JWT]] es autónomo (stateless): contiene toda la información de identidad y permisos firmada criptográficamente, permitiendo al servidor validar la autenticidad sin consultar la sesión en base de datos."),
        ("Celery", "Cola de tareas distribuida y asíncrona.", "¿Por qué no ejecutar tareas pesadas directamente en la petición HTTP?", "1. Pregunta sobre buenas prácticas web.\n2. Respondo sin comandos.", "Ejecutar tareas pesadas en la petición HTTP bloquearía el servidor web y degradaría la latencia del usuario; delegarlas en [[Celery]] libera de inmediato la respuesta HTTP."),
        ("Microservicios", "Arquitectura en servicios autónomos desacoplados.", "¿Cuál es el principal reto de adoptar microservicios?", "1. Consulta conceptual.\n2. Sin guardar.", "El principal reto de los [[Microservicios]] radica en la complejidad operativa: gestión distribuida de transacciones, observabilidad en red, latencia de comunicación y despliegues coordinados."),
        ("Kubernetes", "Orquestador declarativo de pods y servicios.", "¿Qué hace Kubernetes cuando un contenedor se detiene de forma inesperada?", "1. Pregunta de tolerancia a fallos.\n2. Respondo directamente.", "[[Kubernetes]] monitoriza el estado deseado frente al estado real; si un contenedor falla, su controlador de réplicas reinicia automáticamente el pod o programa uno nuevo."),
        ("Git", "Control de versiones distribuido con historial criptográfico.", "¿Qué ventaja ofrece Git al ser un sistema distribuido?", "1. Consulta sobre Git.\n2. Sin /save.", "Al ser distribuido, cada desarrollador tiene una copia completa del repositorio y su historial en local, permitiendo trabajar, hacer commits y consultar ramas sin conexión a red."),
        ("Pydantic", "Validación y parseo con type hints.", "¿Qué diferencia a Pydantic de la validación manual de diccionarios?", "1. Pregunta técnica de Python.\n2. Respondo asertivamente.", "[[Pydantic]] automatiza la coerción y validación de tipos mediante anotaciones de Python, generando mensajes de error estructurados y garantizando datos sanitizados."),
        ("NDJSON", "Formato de streaming línea por línea.", "¿Por qué NDJSON es mejor que un array JSON para streaming de red?", "1. Consulta sobre protocolos de red.\n2. Sin comandos.", "[[NDJSON]] permite al receptor procesar cada mensaje en cuanto llega sin esperar al cierre de un array general, eliminando la necesidad de acumular todo el payload en memoria."),
        ("HTTP/2", "Protocolo web multiplexado y binario.", "¿Cómo reduce HTTP/2 el problema del head-of-line blocking en navegadores?", "1. Pregunta sobre rendimiento web.\n2. Respondo directamente.", "[[HTTP/2]] multiplexa múltiples peticiones y respuestas simultáneas sobre la misma conexión TCP usando frames binarios, evitando abrir conexiones paralelas repetitivas."),
        ("Locust", "Framework de stress testing en Python.", "¿Por qué es ventajoso escribir pruebas de carga en código Python con Locust?", "1. Consulta sobre herramientas de testing.\n2. Respondo sin /save.", "Escribir pruebas en Python con [[Locust]] permite versionar los escenarios en Git, parametrizar dinámicamente datos de usuarios y simular flujos complejos con lógica condicional real."),
        ("MinIO", "Almacenamiento de objetos S3 compatible.", "¿Qué caso de uso típico tiene MinIO en un entorno de desarrollo?", "1. Pregunta informativa sobre almacenamiento.\n2. Respondo claramente.", "[[MinIO]] permite levantar localmente un servidor compatible con la API de Amazon S3 mediante Docker, facilitando pruebas de subida y descarga de archivos sin costes de nube.")
    ]
    for c_title, c_def, q, th, resp in pure_queries:
        exs.append(_conv(_wiki(f"[[{c_title}]]: {c_def}"), _human(q), _gpt(th, resp, "")))

    # =========================================================================
    # BLOQUE C EXTENDIDO: Ciclo /search -> /edit con definición inmediata (20 ejemplos)
    # =========================================================================
    search_edit_cycles = [
        ("Nginx", "Actualiza Nginx añadiendo soporte para el protocolo QUIC y HTTP/3.", "Nginx", "<definition>\nNginx es un servidor web y proxy inverso de alto rendimiento con soporte nativo para los protocolos QUIC y HTTP/3 sobre UDP.\n</definition>", '/edit "Nginx"'),
        ("PostgreSQL", "Añade a PostgreSQL que soporta tablas lógicas no registradas (UNLOGGED) para mayor velocidad.", "PostgreSQL", "<definition>\nPostgreSQL es un sistema gestor de bases de datos relacional que permite crear tablas UNLOGGED para optimizar escrituras temporales omitiendo el WAL.\n</definition>", '/edit "PostgreSQL"'),
        ("FastAPI", "Actualiza FastAPI indicando que incluye middleware CORS nativo y soporte WebSocket.", "FastAPI", "<definition>\nFastAPI es un framework web asíncrono para Python que proporciona middlewares integrados para políticas CORS y controladores nativos de WebSockets.\n</definition>", '/edit "FastAPI"'),
        ("Docker", "Añade a Docker que BuildKit optimiza la construcción paralela de capas mediante caché distribuida.", "Docker", "<definition>\nDocker es una plataforma de contenedores que utiliza el motor BuildKit para compilar imágenes en paralelo y aprovechar cachés multinivel.\n</definition>", '/edit "Docker"'),
        ("Redis", "Actualiza Redis agregando que Redis Streams implementa logs de eventos con grupos de consumidores.", "Redis", "<definition>\nRedis es un almacén en memoria clave-valor que incorpora la estructura Redis Streams para gestión de eventos con grupos de consumidores y acuse de recibo.\n</definition>", '/edit "Redis"'),
        ("Pytest", "Modifica Pytest añadiendo que soporta cobertura de código mediante el plugin pytest-cov.", "Pytest", "<definition>\nPytest es un framework de pruebas en Python compatible con el ecosistema de plugins como pytest-cov para medir la cobertura de código en tests.\n</definition>", '/edit "Pytest"'),
        ("Prometheus", "Actualiza Prometheus indicando que Alertmanager se encarga de agrupar y enrutar notificaciones de alerta.", "Prometheus", "<definition>\nPrometheus es un motor de métricas en series temporales que se integra con Alertmanager para agrupar, silenciar y enrutar alertas a canales externos.\n</definition>", '/edit "Prometheus"'),
        ("Grafana", "Añade a Grafana que soporta provisionamiento declarativo de tableros mediante ficheros JSON.", "Grafana", "<definition>\nGrafana es una plataforma de visualización interactiva que permite el provisionamiento declarativo de tableros y fuentes de datos como código en JSON.\n</definition>", '/edit "Grafana"'),
        ("RabbitMQ", "Actualiza RabbitMQ indicando que soporta el protocolo MQTT para entornos de dispositivos IoT.", "RabbitMQ", "<definition>\nRabbitMQ es un message broker multi-protocolo que además de AMQP soporta adaptadores nativos para MQTT y STOMP en arquitecturas IoT.\n</definition>", '/edit "RabbitMQ"'),
        ("Celery", "Modifica Celery indicando que Flower proporciona una interfaz web en tiempo real para supervisar workers.", "Celery", "<definition>\nCelery es una cola de tareas asíncrona para Python que se complementa con Flower para monitorizar workers, tareas activas y tasas de error en tiempo real.\n</definition>", '/edit "Celery"'),
        ("JWT", "Añade a JWT que la especificación RFC 7519 recomienda tiempos de expiración cortos y rotación con refresh tokens.", "JWT", "<definition>\nJSON Web Token (JWT) es un estándar de claims de autorización cuya especificación RFC 7519 recomienda tiempos de expiración reducidos junto con tokens de refresco.\n</definition>", '/edit "JWT"'),
        ("Git", "Actualiza Git indicando que git bisect permite localizar commits defectuosos mediante búsqueda binaria.", "Git", "<definition>\nGit es un sistema de control de versiones distribuido que incluye el comando git bisect para identificar regresiones mediante búsqueda binaria automatizada en el historial.\n</definition>", '/edit "Git"'),
        ("Kubernetes", "Modifica Kubernetes indicando que Helm es el gestor de paquetes estándar para desplegar charts de aplicaciones.", "Kubernetes", "<definition>\nKubernetes es un orquestador de contenedores que utiliza Helm como gestor de paquetes para empaquetar, versionar y desplegar aplicaciones declarativas en charts.\n</definition>", '/edit "Kubernetes"'),
        ("Pydantic", "Actualiza Pydantic agregando que BaseModel incluye serialización a JSON mediante model_dump_json().", "Pydantic", "<definition>\nPydantic es una librería de validación de datos en Python cuyo tipo BaseModel ofrece el método model_dump_json() para exportación serializada de alta velocidad.\n</definition>", '/edit "Pydantic"'),
        ("MinIO", "Añade a MinIO que incluye soporte para cifrado en reposo del lado del servidor SSE-S3.", "MinIO", "<definition>\nMinIO es un servidor de objetos compatible con Amazon S3 que proporciona cifrado en reposo del lado del servidor (SSE-S3 y SSE-C) con gestión de claves KMS.\n</definition>", '/edit "MinIO"'),
        ("NDJSON", "Actualiza NDJSON señalando que permite ingesta streaming en ElasticSearch mediante la API _bulk.", "NDJSON", "<definition>\nNDJSON es un formato de delimitación por saltos de línea utilizado como estándar de entrada por motores como ElasticSearch para operaciones masivas de ingesta _bulk.\n</definition>", '/edit "NDJSON"'),
        ("HTTP/2", "Modifica HTTP/2 agregando que la compresión de cabeceras se realiza mediante el algoritmo HPACK.", "HTTP/2", "<definition>\nHTTP/2 es una revisión del protocolo web que utiliza el algoritmo HPACK para comprimir cabeceras repetitivas y reducir el overhead de transmisión.\n</definition>", '/edit "HTTP/2"'),
        ("Locust", "Actualiza Locust indicando que permite ejecución distribuida maestro-trabajador para pruebas a gran escala.", "Locust", "<definition>\nLocust es una herramienta de pruebas de carga en Python con arquitectura distribuida que permite orquestar miles de usuarios concurrentes mediante nodos worker coordinados por un master.\n</definition>", '/edit "Locust"'),
        ("WebSocket", "Añade a WebSocket que el handshake inicial se negocia mediante una actualización de protocolo HTTP (Upgrade).", "WebSocket", "<definition>\nWebSocket es un protocolo dúplex continuo cuya conexión se inicia mediante una petición HTTP estándar con cabeceras Upgrade: websocket para conmutar a socket TCP.\n</definition>", '/edit "WebSocket"'),
        ("Microservicios", "Actualiza Microservicios añadiendo que el patrón Saga gestiona transacciones distribuidas compensatorias.", "Microservicios", "<definition>\nUn microservicio es un componente independiente de negocio que implementa el patrón Saga para coordinar transacciones distribuidas mediante eventos y acciones compensatorias.\n</definition>", '/edit "Microservicios"')
    ]
    for c_title, q, term, def_xml, cmd in search_edit_cycles:
        exs.append(_conv(
            _sys(),
            _human(q),
            _gpt(
                f"1. El usuario solicita actualizar [[{term}]].\n2. Consulto la wiki primero para verificar existencia.\n3. Ejecuto /search.",
                f"Consulto la ficha de [[{term}]] en la base de conocimientos.",
                f'/search "{term}"'
            ),
            _human(f"[RESULTADO COMANDO /search \"{term}\"]\n- [[{term}]]: Entrada existente."),
            _gpt(
                f"1. Concepto localizado.\n2. Emito la definición estructurada con la información ampliada.\n3. Aplico /edit sin emitir frases de anuncio.",
                def_xml,
                cmd
            )
        ))

    # =========================================================================
    # BLOQUE D EXTENDIDO: Recuperación limpia tras rechazos del validador (20 ejemplos)
    # =========================================================================
    recovery_scenarios = [
        ("Nginx", "Actualiza Nginx con balanceo least-connected.", "Procedo a actualizar el balanceo.", "<definition>\nNginx es un servidor web y proxy inverso asíncrono con soporte para balanceo de carga mediante el algoritmo least-connected.\n</definition>", '/edit "Nginx"'),
        ("PostgreSQL", "Añade que PostgreSQL soporta foreign data wrappers.", "Voy a registrar los wrappers.", "<definition>\nPostgreSQL es un motor de base de datos relacional con soporte para Foreign Data Wrappers (SQL/MED) para consultar fuentes externas.\n</definition>", '/edit "PostgreSQL"'),
        ("Docker", "Anota que Docker soporta redes overlay para clusters Swarm.", "Procederé a actualizar la red.", "<definition>\nDocker es una plataforma de contenedores que incluye controladores de red overlay para comunicación segura entre contenedores en clúster.\n</definition>", '/edit "Docker"'),
        ("FastAPI", "Guarda que FastAPI usa dependencias inyectables con Depends().", "Voy a guardar la inyección.", "<definition>\nFastAPI es un framework web para Python con un sistema nativo de inyección de dependencias modular gestionado mediante Depends().\n</definition>", '/edit "FastAPI"'),
        ("RabbitMQ", "Añade que RabbitMQ soporta colas de quórum basadas en Raft.", "Actualizaré las colas.", "<definition>\nRabbitMQ es un servidor de mensajería AMQP que implementa colas de quórum replicadas mediante el algoritmo de consenso Raft para alta disponibilidad.\n</definition>", '/edit "RabbitMQ"'),
        ("Redis", "Registra que Redis tiene persistencia RDB y AOF.", "Procedo a registrar la persistencia.", "<definition>\nRedis es un almacén en memoria que ofrece persistencia configurable mediante instantáneas periódicas en disco (RDB) y registro de operaciones (AOF).\n</definition>", '/edit "Redis"'),
        ("Pytest", "Añade que Pytest permite crear marcas personalizadas con custom markers.", "Voy a modificar Pytest.", "<definition>\nPytest es un framework de testing que permite definir marcas personalizadas (custom markers) para categorizar y filtrar la ejecución de tests.\n</definition>", '/edit "Pytest"'),
        ("Prometheus", "Guarda que Prometheus soporta scrape pools con service discovery.", "Procedo a guardar el discovery.", "<definition>\nPrometheus es un motor de métricas con soporte para service discovery dinámico en entornos Kubernetes, DNS o archivos estáticos.\n</definition>", '/edit "Prometheus"'),
        ("Grafana", "Actualiza Grafana con plugins de paneles comunitarios.", "Voy a registrar los plugins.", "<definition>\nGrafana es un entorno de dashboards visuales extensible mediante plugins comunitarios para visualización de grafos, diagramas y mapas.\n</definition>", '/edit "Grafana"'),
        ("Celery", "Anota que Celery Beat programa tareas periódicas tipo cron.", "Actualizaré Celery Beat.", "<definition>\nCelery es una cola de tareas asíncrona que incluye el planificador Celery Beat para despachar tareas periódicas en intervalos regulares tipo cron.\n</definition>", '/edit "Celery"'),
        ("JWT", "Guarda que JWT soporta claims privados y registrados.", "Procedo a registrar los claims.", "<definition>\nJSON Web Token (JWT) es un estándar de autorización que estructura claims registrados (iss, exp, sub) y claims personalizados de aplicación.\n</definition>", '/edit "JWT"'),
        ("Git", "Añade que git cherry-pick aplica un commit específico a la rama actual.", "Voy a guardar cherry-pick.", "<definition>\nGit es un sistema de control de versiones distribuido que incluye el comando git cherry-pick para replicar un commit aislado en la rama de trabajo.\n</definition>", '/edit "Git"'),
        ("Kubernetes", "Actualiza Kubernetes con soporte para ingress controllers.", "Procederé a actualizar ingress.", "<definition>\nKubernetes es un orquestador de contenedores que utiliza Ingress Controllers para gestionar el enrutamiento HTTP y TLS hacia servicios internos.\n</definition>", '/edit "Kubernetes"'),
        ("Pydantic", "Añade que Pydantic soporta validadores personalizados con @field_validator.", "Voy a modificar los validadores.", "<definition>\nPydantic es una librería de validación en Python que permite definir validadores de atributos personalizados mediante el decorador @field_validator.\n</definition>", '/edit "Pydantic"'),
        ("MinIO", "Registra que MinIO soporta replicación bucket-to-bucket multi-sitio.", "Procedo a registrar la replicación.", "<definition>\nMinIO es un servidor de almacenamiento de objetos con soporte para replicación bidireccional continua entre buckets de múltiples centros de datos.\n</definition>", '/edit "MinIO"'),
        ("NDJSON", "Anota que cada línea en NDJSON debe ser un objeto JSON válido.", "Voy a registrar la regla.", "<definition>\nNDJSON es un protocolo de datos por líneas donde cada registro individual debe ser un objeto JSON sintácticamente válido terminado en '\\n'.\n</definition>", '/edit "NDJSON"'),
        ("HTTP/2", "Actualiza HTTP/2 con la capacidad de server push.", "Procedo a guardar server push.", "<definition>\nHTTP/2 es una revisión del protocolo web que incorpora la capacidad Server Push para anticipar el envío de recursos antes de que el cliente los solicite.\n</definition>", '/edit "HTTP/2"'),
        ("Locust", "Guarda que Locust permite definir pesos de probabilidad por tarea.", "Voy a actualizar Locust.", "<definition>\nLocust es un framework de pruebas de carga donde cada tarea puede llevar pesos numéricos @task(weight) para simular navegación realista.\n</definition>", '/edit "Locust"'),
        ("WebSocket", "Añade que WebSocket utiliza frames de ping y pong para latidos.", "Procedo a guardar los latidos.", "<definition>\nWebSocket es un protocolo dúplex continuo que implementa tramas de control opcode 0x9 (Ping) y 0xA (Pong) para comprobar la salud del canal.\n</definition>", '/edit "WebSocket"'),
        ("Microservicios", "Registra que el API Gateway centraliza enrutamiento y autenticación.", "Voy a registrar el gateway.", "<definition>\nEn una arquitectura de microservicios, el API Gateway actúa como punto único de entrada para enrutamiento, terminación de seguridad y agregación de respuestas.\n</definition>", '/edit "Microservicios"')
    ]
    for c_title, user_req, bad_announcement, clean_xml, cmd in recovery_scenarios:
        exs.append(_conv(
            _sys(),
            _human(user_req),
            _gpt(
                f"1. Solicitud recibida para {c_title}.\n2. Error: emití una frase de anuncio.\n3. Ejecuto comando.",
                bad_announcement,
                cmd
            ),
            _human(f"[ERROR VALIDADOR]: save_last_response rechazado: frase de intención detectada ('{bad_announcement}')"),
            _gpt(
                f"1. El validador rechazó la respuesta previa por contener frase de anuncio.\n2. Me recupero de inmediato: elimino toda charla conversacional y emito el XML estructurado puro.\n3. Reintento el comando {cmd}.",
                clean_xml,
                cmd
            )
        ))

    assert len(exs) == 80, f"Esperados 80 ejemplos adicionales en FT3, obtenidos {len(exs)}"
    return exs

