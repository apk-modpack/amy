"""Constructor de datos para FT1 complementarios."""

def get_ft1_extra_blocks(make_ex):
    exs = []

    # BLOQUE 8: IDENTIFICACIÓN Y REGLA HUMAN (/identify) (12 ejemplos)
    id_exs = [
        ("¿Cuál es tu identificación de agente?", "Identificación del Agente:\n- Nombre: Kinetics-Seeker-18\n- ID: 631b4d3d-1212-4c36-82f0-172aae542c25\n- Rol: Agente IA (Wiki-Memory)", "/identify"),
        ("Ejecuta /identify para ver tus datos de registro.", "Identificación del Agente:\n- Nombre: Kinetics-Seeker-18\n- ID: 631b4d3d-1212-4c36-82f0-172aae542c25\n- Rol: Agente IA (Wiki-Memory)", "/identify"),
        ("¿Quién eres en esta sala de chat?", "Identificación del Agente:\n- Nombre: Kinetics-Seeker-18\n- ID: 631b4d3d-1212-4c36-82f0-172aae542c25\n- Rol: Agente IA (Wiki-Memory)", "/identify"),
        ("Comprueba tu identidad con /identify.", "Identificación del Agente:\n- Nombre: Kinetics-Seeker-18\n- ID: 631b4d3d-1212-4c36-82f0-172aae542c25\n- Rol: Agente IA (Wiki-Memory)", "/identify"),
        ("¿Eres el usuario humano o un agente?", "Soy un agente artificial con persistencia en Wiki. Jamás utilizo la identidad reservada HUMAN.", "/identify"),
        ("Verifica tu ID único en el sistema.", "Identificación del Agente:\n- Nombre: Kinetics-Seeker-18\n- ID: 631b4d3d-1212-4c36-82f0-172aae542c25\n- Rol: Agente IA (Wiki-Memory)", "/identify"),
        ("Dime tu nombre asignado de agente.", "Identificación del Agente:\n- Nombre: Kinetics-Seeker-18\n- ID: 631b4d3d-1212-4c36-82f0-172aae542c25\n- Rol: Agente IA (Wiki-Memory)", "/identify"),
        ("Ejecuta el comando para identificarte ante el resto de participantes.", "Identificación del Agente:\n- Nombre: Kinetics-Seeker-18\n- ID: 631b4d3d-1212-4c36-82f0-172aae542c25\n- Rol: Agente IA (Wiki-Memory)", "/identify"),
        ("¿Qué archivo guarda tus credenciales de agente?", "Mi identidad reside en el archivo de configuración local del agente. Puedo consultar mis datos con /identify.", "/identify"),
        ("Muestra tu tarjeta de identidad.", "Identificación del Agente:\n- Nombre: Kinetics-Seeker-18\n- ID: 631b4d3d-1212-4c36-82f0-172aae542c25\n- Rol: Agente IA (Wiki-Memory)", "/identify"),
        ("¿Puedes llamarte HUMAN?", "No. El identificador HUMAN está estrictamente reservado para entradas de usuarios humanos y no puede ser usado por ningún agente.", "/identify"),
        ("Identifícate en la red.", "Identificación del Agente:\n- Nombre: Kinetics-Seeker-18\n- ID: 631b4d3d-1212-4c36-82f0-172aae542c25\n- Rol: Agente IA (Wiki-Memory)", "/identify"),
    ]
    for q, resp, cmd in id_exs:
        exs.append(make_ex("<MODO: AGENTE>", q, resp, cmd))

    # BLOQUE 9: BÚSQUEDAS ADICIONALES /search (15 ejemplos)
    search_extra = [
        ("¿Tenemos información sobre el balanceador Nginx?", "Nginx"),
        ("Busca la política de retención de logs.", "Retención de logs"),
        ("¿Qué documentación hay sobre WebSockets?", "WebSockets"),
        ("Busca si tenemos documentada la arquitectura hexagonal.", "Arquitectura Hexagonal"),
        ("¿Qué sabemos sobre CI/CD con GitHub Actions?", "GitHub Actions"),
        ("Busca información sobre el protocolo TLS y certificados.", "Certificados TLS"),
        ("¿Hay registros sobre pruebas de estrés con Locust?", "Locust"),
        ("Busca el manual sobre particionamiento en PostgreSQL.", "Particionamiento PostgreSQL"),
        ("¿Qué datos tenemos sobre Kafka y streaming de eventos?", "Apache Kafka"),
        ("Busca las pautas para revisión de Pull Requests.", "Revisión Pull Requests"),
        ("¿Qué sabemos sobre la infraestructura de staging?", "Entorno Staging"),
        ("Busca documentación sobre autenticación multifactor MFA.", "Autenticación MFA"),
        ("¿Tenemos registrado el procedimiento ante caídas de servidor?", "Procedimiento Caídas Servidor"),
        ("Busca información sobre el crawler web interno.", "Crawler Web Interno"),
        ("¿Qué sabemos acerca del formato JSON Lines NDJSON?", "NDJSON")
    ]
    for q, term in search_extra:
        exs.append(make_ex(
            "<MODO: AGENTE>",
            q,
            f"Voy a consultar en la memoria wiki si tenemos información registrada sobre '{term}'.",
            f'/search "{term}"'
        ))

    # BLOQUE 10: GUARDADOS ESTRUCTURADOS /save (15 ejemplos)
    save_extra = [
        ("Registra el concepto WebSocket: protocolo de comunicación bidireccional sobre una única conexión TCP.", "WebSocket", "<definition>\nWebSocket es un protocolo de red estándar que permite canales de comunicación bidireccionales y dúplex completo sobre una conexión TCP continua.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Protocolo de Red\">Es un protocolo de capa de aplicación.</relation>\n</relations>", '/save "WebSocket"'),
        ("Guarda el concepto Nginx como servidor web y proxy inverso de alto rendimiento.", "Nginx", "<definition>\nNginx es un servidor web y proxy inverso asíncrono diseñado para alta concurrencia y bajo consumo de recursos de memoria.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Servidor Web\">Actúa como servidor HTTP y proxy inverso.</relation>\n</relations>", '/save "Nginx"'),
        ("Registra que GitHub Actions es nuestra plataforma de integración continua CI/CD.", "GitHub Actions", "<definition>\nGitHub Actions es la plataforma de automatización de flujos de trabajo utilizada para compilación, testing y despliegue continuo de código.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Plataforma CI/CD\">Servicio de automatización de entregas.</relation>\n</relations>", '/save "GitHub Actions"'),
        ("Anota el concepto PostgreSQL: sistema gestor de bases de datos relacional y transaccional.", "PostgreSQL", "<definition>\nPostgreSQL es un sistema gestor de bases de datos relacional orientado a objetos, robusto y conforme con los estándares ACID.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Base de Datos Relacional\">Motor principal de datos persistentes.</relation>\n</relations>", '/save "PostgreSQL"'),
        ("Guarda que usamos Docker Compose para orquestación de servicios en desarrollo.", "Docker Compose", "<definition>\nDocker Compose es la herramienta oficial para definir y ejecutar aplicaciones multicontenedor en entornos locales de desarrollo y pruebas.\n</definition>\n<relations>\n  <relation type=\"part_of\" target=\"Ecosistema Docker\">Herramienta complementaria de Docker.</relation>\n</relations>", '/save "Docker Compose"'),
        ("Registra el concepto JWT (JSON Web Token) como estándar para claims de identidad.", "JWT", "<definition>\nJSON Web Token (JWT) es un estándar abierto RFC 7519 que define un formato compacto y autónomo para transmitir información segura entre partes.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Estándar de Seguridad\">Mecanismo de token de autorización.</relation>\n</relations>", '/save "JWT"'),
        ("Guarda el concepto Microservicio como patrón de arquitectura desacoplada.", "Microservicio", "<definition>\nUn microservicio es una unidad autónoma de despliegue que implementa una capacidad de negocio específica y se comunica mediante APIs ligeras.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Patrón de Arquitectura\">Estilo arquitectónico de servicios independientes.</relation>\n</relations>", '/save "Microservicio"'),
        ("Registra el concepto Prometheus: sistema de monitorización basado en métricas time-series.", "Prometheus", "<definition>\nPrometheus es un sistema de monitorización y alertas de código abierto optimizado para recopilar métricas multidimensionales en series temporales.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Sistema de Monitorización\">Herramienta de observabilidad.</relation>\n</relations>", '/save "Prometheus"'),
        ("Guarda el concepto Grafana: plataforma de visualización interactiva y dashboards.", "Grafana", "<definition>\nGrafana es un software de analítica y visualización interactiva que permite consultar y representar métricas procedentes de Prometheus o bases de datos.\n</definition>\n<relations>\n  <relation type=\"relates_to\" target=\"Prometheus\">Consume métricas para paneles visuales.</relation>\n</relations>", '/save "Grafana"'),
        ("Registra el concepto RabbitMQ: broker de mensajería basado en AMQP.", "RabbitMQ", "<definition>\nRabbitMQ es un servidor de colas y mensajería asíncrona que implementa el protocolo AMQP para desacoplar productores y consumidores de datos.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Message Broker\">Intermediario de mensajes.</relation>\n</relations>", '/save "RabbitMQ"'),
        ("Guarda el concepto Pytest: framework de pruebas unitarias e integración en Python.", "Pytest", "<definition>\nPytest es un framework robusto y extensible para escribir y ejecutar pruebas unitarias y funcionales en proyectos Python.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Framework de Testing\">Herramienta de pruebas de software.</relation>\n</relations>", '/save "Pytest"'),
        ("Registra el concepto Pydantic: librería de validación de datos basada en type hints.", "Pydantic", "<definition>\nPydantic es una biblioteca de validación de datos y gestión de configuraciones en Python que utiliza anotaciones de tipo nativas.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Librería de Validación\">Capa de serialización y verificación.</relation>\n</relations>", '/save "Pydantic"'),
        ("Guarda el concepto FastAPI: framework web asíncrono para construir APIs REST.", "FastAPI", "<definition>\nFastAPI es un framework moderno y de alto rendimiento para construir APIs con Python basado en Starlette y Pydantic.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Framework Web\">Framework de backend HTTP.</relation>\n</relations>", '/save "FastAPI"'),
        ("Registra el concepto Celery: cola de tareas distribuida y asíncrona para Python.", "Celery", "<definition>\nCelery es un sistema de ejecución de tareas en segundo plano orientado a mensajes que procesa trabajos asíncronos y programados.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Cola de Tareas\">Gestor distribuido de jobs.</relation>\n</relations>", '/save "Celery"'),
        ("Guarda el concepto Unittest: módulo estándar de pruebas unitarias en Python.", "Unittest", "<definition>\nUnittest es el framework oficial de pruebas incluido en la biblioteca estándar de Python, basado en la arquitectura xUnit.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Framework de Testing\">Módulo nativo de testing.</relation>\n</relations>", '/save "Unittest"'),
    ]
    for q, title, resp, cmd in save_extra:
        exs.append(make_ex("<MODO: AGENTE>", q, resp, cmd))

    # BLOQUE 11: EDICIÓN /edit (10 ejemplos)
    edit_extra = [
        ("Actualiza Nginx añadiendo que soporta balanceo de carga round-robin.", "Nginx", "<definition>\nNginx es un servidor web y proxy inverso asíncrono que incluye capacidades avanzadas de balanceo de carga HTTP mediante algoritmos round-robin y least-connected.\n</definition>\n<relations>\n  <relation type=\"is_a\" target=\"Servidor Web\">Actúa como servidor HTTP y proxy inverso.</relation>\n</relations>", '/edit "Nginx"'),
        ("Modifica PostgreSQL agregando que soporta replicación streaming maestro-esclavo.", "PostgreSQL", "<definition>\nPostgreSQL es un sistema gestor de bases de datos relacional y transaccional con soporte nativo para replicación física streaming en esquemas primario-réplica.\n</definition>", '/edit "PostgreSQL"'),
        ("Actualiza Docker Compose indicando que la versión v2 está escrita en Go.", "Docker Compose", "<definition>\nDocker Compose es la herramienta de orquestación de contenedores locales cuya versión Compose V2 está integrada nativamente en el CLI de Docker en lenguaje Go.\n</definition>", '/edit "Docker Compose"'),
        ("Amplía el concepto JWT mencionando que el algoritmo RS256 utiliza claves asimétricas.", "JWT", "<definition>\nJSON Web Token (JWT) es un estándar compacto de claims que puede firmarse mediante algoritmos simétricos (HS256) o asimétricos con pares público-privado (RS256).\n</definition>", '/edit "JWT"'),
        ("Edita Microservicio aclarando que cada servicio debe gestionar su propia base de datos.", "Microservicio", "<definition>\nUn microservicio es un componente independiente de negocio que aplica el principio de Database-per-Service para garantizar aislamiento de datos.\n</definition>", '/edit "Microservicio"'),
        ("Actualiza Prometheus añadiendo el lenguaje PromQL para consultas de métricas.", "Prometheus", "<definition>\nPrometheus es un motor de monitorización de métricas en series temporales que proporciona el lenguaje expresivo PromQL para agregaciones y alertas.\n</definition>", '/edit "Prometheus"'),
        ("Modifica Grafana señalando que permite configurar alertas directas a Discord y Telegram.", "Grafana", "<definition>\nGrafana es un entorno de dashboards visuales que incluye gestión de canales de notificación para despachar alertas automáticas a Slack, Discord y Telegram.\n</definition>", '/edit "Grafana"'),
        ("Actualiza RabbitMQ indicando que soporta exchanges de tipo direct, fanout, topic y headers.", "RabbitMQ", "<definition>\nRabbitMQ es un message broker AMQP que distribuye mensajes a colas a través de intercambiadores (exchanges) configurables como direct, fanout, topic o headers.\n</definition>", '/edit "RabbitMQ"'),
        ("Edita Pytest añadiendo que los fixtures permiten inyección de dependencias modular.", "Pytest", "<definition>\nPytest es un framework de testing en Python cuyo sistema de fixtures proporciona inyección de dependencias flexible para configuración y teardown de tests.\n</definition>", '/edit "Pytest"'),
        ("Actualiza Pydantic indicando que la versión V2 cuenta con el núcleo pydantic-core en Rust.", "Pydantic", "<definition>\nPydantic es una librería de validación de datos cuya versión 2 reimplementa su núcleo de validación en Rust para alcanzar máxima velocidad de serialización.\n</definition>", '/edit "Pydantic"'),
    ]
    for q, title, resp, cmd in edit_extra:
        exs.append(make_ex("<MODO: AGENTE>", q, resp, cmd))

    # BLOQUE 12: BORRADO /delete (10 ejemplos)
    delete_extra = [
        ("Elimina la entrada obsoleta sobre Flash Player.", "Flash Player", "Voy a proceder a eliminar el concepto obsoleto [[Flash Player]] de la base de conocimientos.", '/delete "Flash Player"'),
        ("Borra el concepto Python 2.7 ya que está deprecado.", "Python 2.7", "Procedo a dar de baja el concepto deprecado [[Python 2.7]] de la memoria wiki.", '/delete "Python 2.7"'),
        ("Elimina la política temporal de teletrabajo de 2020.", "Política Teletrabajo 2020", "Elimino la entrada histórica [[Política Teletrabajo 2020]] del registro documental.", '/delete "Política Teletrabajo 2020"'),
        ("Borra la configuración del antiguo cluster de pruebas.", "Cluster Pruebas Antiguo", "Borro el registro del [[Cluster Pruebas Antiguo]] por desmantelamiento de infraestructura.", '/delete "Cluster Pruebas Antiguo"'),
        ("Elimina el registro de la pasarela de pago antigua.", "Pasarela Pago Antigua", "Procedo a eliminar el concepto [[Pasarela Pago Antigua]] de la memoria del sistema.", '/delete "Pasarela Pago Antigua"'),
        ("Borra la documentación de la API v1 descontinuada.", "API v1 Descontinuada", "Borro el concepto [[API v1 Descontinuada]] de la wiki conceptual.", '/delete "API v1 Descontinuada"'),
        ("Elimina el manual de CentOS 7 tras finalizar su ciclo de vida.", "CentOS 7", "Procedo a dar de baja el concepto [[CentOS 7]] de la base de conocimientos.", '/delete "CentOS 7"'),
        ("Borra las credenciales de staging que caducaron.", "Credenciales Staging Caducadas", "Elimino la entrada sobre [[Credenciales Staging Caducadas]] para mantener la wiki actualizada.", '/delete "Credenciales Staging Caducadas"'),
        ("Elimina la referencia al servidor FTP en desuso.", "Servidor FTP", "Borro el concepto [[Servidor FTP]] tras su migración a protocolos seguros.", '/delete "Servidor FTP"'),
        ("Borra el concepto SVN (Subversion) sustituido por Git.", "Subversion SVN", "Procedo a eliminar el concepto [[Subversion SVN]] de la base documental.", '/delete "Subversion SVN"'),
    ]
    for q, title, resp, cmd in delete_extra:
        exs.append(make_ex("<MODO: AGENTE>", q, resp, cmd))

    return exs

