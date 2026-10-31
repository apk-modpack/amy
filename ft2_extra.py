"""Constructor de 49 ejemplos complementarios para FT2 (ReAct Multi-Ciclo).
Lleva el total de FT2 de 51 a exactamente 100 ejemplos únicos.

Incluye:
- Razonamiento explícito sobre emisor HUMAN vs otros agentes compañeros.
- Razonamiento sobre auto-identificación (/identify).
- Búsquedas, lecturas y guardados encadenados multi-turno con <thought>.
"""

def get_ft2_extra_examples():
    exs = []

    def make_react(human_text, thought_text, response_text, commands_text="", system_text="<MODO: AGENTE>"):
        val = (
            f"<thought>\n{thought_text.strip()}\n</thought>\n"
            f"<response>\n{response_text.strip()}\n</response>\n"
            f"<commands>\n{commands_text.strip()}\n</commands>"
        )
        return {
            "conversations": [
                {"from": "system", "value": system_text},
                {"from": "human", "value": human_text},
                {"from": "gpt", "value": val}
            ]
        }

    # =========================================================================
    # GRUPO A: Razonamiento de Identidad y Emisor HUMAN / Agente (14 ejemplos)
    # =========================================================================
    ident_examples = [
        (
            "¿Cuál es tu nombre y número de agente?",
            "1. El usuario pregunta por mi identidad de agente.\n2. Debo invocar /identify para consultar mi archivo local de configuración.\n3. Indicaré al usuario que procedo a identificarme.",
            "Voy a consultar mi identidad registrada en el sistema.",
            "/identify"
        ),
        (
            "Comprueba tu estado de identidad con /identify.",
            "1. Se solicita explícitamente ejecutar /identify.\n2. Llamo a la herramienta interna para reportar mi nombre e ID único.",
            "Ejecuto el comando de verificación de identidad.",
            "/identify"
        ),
        (
            "¿Eres un usuario humano?",
            "1. Me preguntan si soy humano.\n2. Mi rol es el de un agente IA con memoria persistente.\n3. El identificador HUMAN es exclusivo de personas reales en la sala; yo uso mi propia identidad de agente.",
            "No, soy un agente de Inteligencia Artificial con memoria persistente en Wiki. El rol y nombre HUMAN están reservados para usuarios humanos.",
            ""
        ),
        (
            "¿Quién eres en el sistema de red?",
            "1. El emisor consulta quién soy en el entorno distribuido.\n2. Debo ejecutar /identify para obtener mis credenciales activas.",
            "Consulto mis credenciales locales de agente.",
            "/identify"
        ),
        (
            "[DE: Atlas-Core-01]\nHola compañero, ¿cuál es tu identificador en la sala?",
            "1. Mensaje recibido de otro agente (Atlas-Core-01).\n2. Es una consulta inter-agente de identificación.\n3. Ejecuto /identify para responder con mis parámetros técnicos de forma concisa.",
            "Saludos Atlas-Core-01. Reporto mi identificación técnica.",
            "/identify"
        ),
        (
            "[DE: Nexus-Pilot-42]\nSolicito confirmación de tu ID de agente para sincronización.",
            "1. El agente Nexus-Pilot-42 solicita mi ID para coordinar tareas.\n2. Invoco /identify para obtener el identificador persistente.",
            "Procedo a consultar mi identificador para coordinar la sesión.",
            "/identify"
        ),
        (
            "¿Por qué no puedes identificarte como HUMAN?",
            "1. El usuario pregunta por la regla del nombre reservado HUMAN.\n2. Debo explicar que HUMAN distingue las instrucciones de personas reales de las generadas por otros agentes en la sala de chat.",
            "El nombre HUMAN está estrictamente reservado por el protocolo de red para garantizar que las órdenes de personas reales no se confundan con mensajes autónomos de otros agentes.",
            ""
        ),
        (
            "Reporta tu ID antes de continuar.",
            "1. Se me pide reportar mi identificador.\n2. Uso /identify.",
            "Verifico y reporto mis datos de identidad.",
            "/identify"
        ),
        (
            "[DE: HUMAN]\n¿Estás listo para recibir nuevas instrucciones?",
            "1. Mensaje proveniente directamente de un usuario humano (HUMAN).\n2. No requiero comandos de wiki, confirmo disponibilidad y estado LISTO.",
            "Sí, estoy listo y disponible para recibir instrucciones y gestionar la memoria wiki.",
            ""
        ),
        (
            "[DE: Echo-Weaver-99]\n¿Tienes memoria local persistente?",
            "1. Otro agente pregunta sobre mis capacidades.\n2. Explico mi arquitectura con memoria wiki basada en grafos XML y comandos CLI.",
            "Afirmativo, mantengo una base de conocimientos wiki estructurada con micro-formato XML y relaciones semánticas.",
            ""
        ),
        (
            "Muestra tu configuración de identidad.",
            "1. Petición de consultar la identidad local.\n2. Ejecuto /identify.",
            "Obtengo mi tarjeta de identidad desde el archivo persistente.",
            "/identify"
        ),
        (
            "¿Puedes cambiar tu nombre a HUMAN?",
            "1. El usuario me pide adoptar el nombre HUMAN.\n2. Debo denegar la solicitud firmemente explicando la restricción de protocolo.",
            "No es posible. El protocolo del sistema bloquea el uso de 'HUMAN' como nombre de agente para preservar la trazabilidad entre humanos y máquinas.",
            ""
        ),
        (
            "[DE: Sentinel-Mind-07]\nVerificación de presencia: emite tu credencial.",
            "1. Verificación inter-agente iniciada por Sentinel-Mind-07.\n2. Ejecuto /identify.",
            "Atendiendo verificación de presencia.",
            "/identify"
        ),
        (
            "¿Cómo sé si estoy hablando con un agente o con otra persona?",
            "1. Pregunta sobre discriminación de participantes en la sala.\n2. Explico que los humanos tienen la etiqueta HUMAN y los agentes llevan nombres generados con sus modelos.",
            "En la sala de chat, los mensajes emitidos por personas reales van precedidos por el identificador reservado HUMAN, mientras que los agentes artificiales mostramos nombres técnicos asignados con nuestros identificadores únicos.",
            ""
        )
    ]
    for q, th, resp, cmd in ident_examples:
        exs.append(make_react(q, th, resp, cmd))

    # =========================================================================
    # GRUPO B: Consultas Informativas con Memoria Wiki Inyectada (15 ejemplos)
    # =========================================================================
    wiki_injected = [
        ("PostgreSQL", "Sistema relacional transaccional ACID con soporte para JSONB y replicación streaming.", "¿Qué características tiene PostgreSQL?", "1. El concepto PostgreSQL está presente en la memoria wiki inyectada.\n2. No debo usar /search ni /save.\n3. Respondo directamente sintetizando el contexto.", "[[PostgreSQL]] es nuestro sistema de base de datos relacional y transaccional. Es conforme con los estándares ACID, soporta documentos JSONB de forma eficiente y ofrece replicación streaming."),
        ("Kafka", "Plataforma distribuida de streaming de eventos basada en particiones y grupos de consumidores.", "¿Cómo procesamos eventos masivos?", "1. La wiki inyectada describe Kafka.\n2. Respondo asertivamente sin comandos.", "Utilizamos [[Kafka]], una plataforma distribuida de streaming de eventos que organiza los mensajes en topics particionados y permite escalado horizontal mediante grupos de consumidores."),
        ("Redis", "Almacén en memoria clave-valor utilizado para caché de sesiones y rate limiting.", "¿Para qué usamos Redis?", "1. Contexto presente en memoria.\n2. Explico el uso de Redis directamente.", "[[Redis]] se utiliza como almacén en memoria clave-valor para acelerar la lectura de datos mediante caché y controlar la tasa de peticiones (rate limiting)."),
        ("Docker", "Tecnología de virtualización ligera basada en cgroups y namespaces del kernel Linux.", "Explícame cómo funciona Docker en el proyecto.", "1. Docker está en la memoria wiki inyectada.\n2. Explico sus fundamentos sin ejecutar comandos.", "[[Docker]] nos proporciona virtualización ligera aislando dependencias en contenedores mediante namespaces y cgroups del kernel Linux, garantizando paridad entre desarrollo y producción."),
        ("FastAPI", "Framework asíncrono en Python basado en Starlette y Pydantic con validación automática.", "¿Qué framework backend usamos para las APIs?", "1. La información de FastAPI está en la wiki inyectada.\n2. Respondo directamente.", "El backend se apoya en [[FastAPI]], un framework asíncrono para Python que proporciona alto rendimiento, tipado fuerte con Pydantic y documentación OpenAPI interactiva automática."),
        ("Pytest", "Framework estándar de testing con soporte para fixtures parametrizados y aserciones nativas.", "¿Cómo se ejecutan los tests unitarios?", "1. La memoria inyectada detalla Pytest.\n2. No requiere /search.", "Las pruebas se desarrollan con [[Pytest]], aprovechando su sistema de fixtures modulares para inicializar dependencias y validar aserciones nativas."),
        ("Celery", "Cola de tareas distribuida que delega trabajos asíncronos y periódicos en workers.", "¿Cómo gestionamos tareas en segundo plano?", "1. Tengo el dato de Celery en memoria.\n2. Respondo con seguridad.", "Las tareas en segundo plano se procesan con [[Celery]], distribuyendo trabajos pesados o programados entre workers independientes mediante brokers de mensajes."),
        ("JWT", "Token de autorización RFC 7519 compuesto por header, payload y firma criptográfica.", "¿Cómo viaja la identidad en las peticiones HTTP?", "1. JWT está en la memoria wiki.\n2. Sintetizo su estructura.", "La identidad se transmite en cabeceras HTTP mediante [[JWT]], un estándar de tokens compactos firmados criptográficamente que contienen los claims y permisos del usuario."),
        ("Prometheus", "Motor de observabilidad basado en recolección pull de métricas time-series.", "¿Qué herramienta monitoriza las métricas del sistema?", "1. Prometheus está en contexto wiki.\n2. Respondo enciclopédicamente.", "La observabilidad de infraestructura recae en [[Prometheus]], que recopila métricas en series temporales mediante sondeo periódico (pull) y permite consultas avanzadas en PromQL."),
        ("Grafana", "Plataforma de tableros gráficos conectada a fuentes de datos para alertas visuales.", "¿Dónde se visualizan los gráficos de rendimiento?", "1. Tengo Grafana en la memoria wiki.\n2. Respondo directamente.", "Los tableros visuales y paneles de rendimiento se configuran en [[Grafana]], consumiendo datos de Prometheus para supervisar latencias y tasas de error."),
        ("Nginx", "Proxy inverso y balanceador de carga HTTP con arquitectura asíncrona por eventos.", "¿Qué componente recibe primero el tráfico web?", "1. Nginx está en la memoria.\n2. Respondo sin comandos.", "El tráfico externo entra a través de [[Nginx]], actuando como proxy inverso y balanceador de carga HTTP de alto rendimiento."),
        ("Microservicios", "Arquitectura distribuida en servicios desacoplados con contratos de API explícitos.", "¿Cuál es la arquitectura global del backend?", "1. Contexto de microservicios en memoria.\n2. Explico la arquitectura.", "Nuestra infraestructura sigue una arquitectura de [[Microservicios]], donde cada dominio funcional es independiente y se comunica mediante APIs y mensajería."),
        ("Git", "Sistema de control de versiones distribuido con ramas por funcionalidad y Pull Requests.", "¿Cómo controlamos las versiones del código fuente?", "1. Git presente en memoria.\n2. Respondo claramente.", "El control de versiones se gestiona con [[Git]], utilizando flujos basados en ramas de características y revisión de código mediante Pull Requests antes de integrar en main."),
        ("Kubernetes", "Orquestador de contenedores que gestiona despliegues, autoescalado y balanceo en pods.", "¿Cómo escalamos los contenedores en producción?", "1. Kubernetes está en la wiki inyectada.\n2. Respondo sin buscar.", "En producción, los contenedores se orquestan con [[Kubernetes]], gestionando el ciclo de vida, la tolerancia a fallos y el autoescalado de pods de manera declarativa."),
        ("Pydantic", "Librería de parseo y validación de esquemas de datos basada en anotaciones de tipo Python.", "¿Cómo validamos las entradas de datos en la API?", "1. Pydantic está en la memoria wiki.\n2. Respondo directamente.", "La validación de datos de entrada y configuración se realiza con [[Pydantic]], garantizando que las estructuras cumplan estrictamente con los esquemas de tipos definidos.")
    ]
    for c_title, c_def, q, th, resp in wiki_injected:
        sys_txt = (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            f"[[{c_title}]]: {c_def}\n"
            "--- FIN DE MEMORIA WIKI ---"
        )
        exs.append(make_react(q, th, resp, "", system_text=sys_txt))

    # =========================================================================
    # GRUPO C: Ciclo Búsqueda -> Respuesta o Edición (20 ejemplos)
    # =========================================================================
    search_cycles = [
        ("¿Qué política tenemos sobre copias de seguridad?", "Copias de Seguridad", "1. No tengo el dato en memoria.\n2. Busco en la wiki.\n3. Indico la búsqueda.", "Voy a consultar la wiki sobre las copias de seguridad.", "/search \"Copias de Seguridad\""),
        ("Busca la documentación sobre rate limiting.", "Rate Limiting", "1. Necesito consultar la wiki sobre rate limiting.\n2. Ejecuto /search.", "Consulto la documentación sobre rate limiting.", "/search \"Rate Limiting\""),
        ("¿Hay registros sobre el protocolo de despliegue canary?", "Despliegue Canary", "1. No está en contexto.\n2. Busco el concepto en la wiki.", "Verifico si tenemos documentado el despliegue canary.", "/search \"Despliegue Canary\""),
        ("¿Cómo se configuran los certificados SSL en staging?", "Certificados SSL Staging", "1. Requiere búsqueda documental.\n2. Llamo a /search.", "Busco la guía de certificados SSL para staging.", "/search \"Certificados SSL Staging\""),
        ("¿Qué estándar seguimos para logging estructurado?", "Logging Estructurado", "1. Procedo a buscar en la memoria wiki.\n2. Ejecuto /search.", "Consulto la política de logging estructurado.", "/search \"Logging Estructurado\""),
        ("Busca si tenemos información sobre RabbitMQ dead letter queues.", "RabbitMQ Dead Letter", "1. Búsqueda especializada sobre colas dead letter.\n2. Ejecuto /search.", "Reviso la wiki sobre colas dead letter en RabbitMQ.", "/search \"RabbitMQ Dead Letter\""),
        ("¿Cuál es el procedimiento ante alertas de latencia alta?", "Procedimiento Alerta Latencia", "1. Busco el procedimiento de operación.\n2. Invoco /search.", "Consulto el procedimiento ante alertas de latencia.", "/search \"Procedimiento Alerta Latencia\""),
        ("Busca información sobre la migración a IPv6.", "Migración IPv6", "1. No está en memoria.\n2. Uso /search.", "Reviso si hay planes registrados sobre la migración a IPv6.", "/search \"Migración IPv6\""),
        ("¿Qué tamaño de heap tiene configurada la JVM de ElasticSearch?", "ElasticSearch Heap", "1. Consulta de parámetro de infraestructura.\n2. Busco en la wiki.", "Voy a consultar la configuración de ElasticSearch.", "/search \"ElasticSearch Heap\""),
        ("Busca el manual sobre rotación de claves secretas.", "Rotación Claves Secretas", "1. Busco política de seguridad.\n2. Ejecuto /search.", "Consulto el protocolo de rotación de claves secretas.", "/search \"Rotación Claves Secretas\""),
        ("¿Cómo se realiza el rollback de una versión en Kubernetes?", "Rollback Kubernetes", "1. Necesito consultar la wiki.\n2. Uso /search.", "Busco las instrucciones de rollback en Kubernetes.", "/search \"Rollback Kubernetes\""),
        ("Busca información sobre balanceo con algoritmo Least Connections.", "Least Connections", "1. Requiero información de balanceo.\n2. Uso /search.", "Reviso la wiki sobre el algoritmo Least Connections.", "/search \"Least Connections\""),
        ("¿Qué sabemos sobre la integración con Stripe para pagos?", "Integración Stripe", "1. Busco módulo de facturación.\n2. Ejecuto /search.", "Consulto la documentación sobre la integración con Stripe.", "/search \"Integración Stripe\""),
        ("Busca el protocolo de pruebas de regresión.", "Pruebas Regresión", "1. No dispongo del dato.\n2. Ejecuto /search.", "Busco el protocolo de pruebas de regresión en la base documental.", "/search \"Pruebas Regresión\""),
        ("¿Cómo se configuran alertas en canales privados de Discord?", "Alertas Discord", "1. Consulto la wiki sobre alertas Discord.\n2. Invoco /search.", "Reviso la documentación sobre alertas en Discord.", "/search \"Alertas Discord\""),
        ("Busca la directiva de timeout de conexiones inactivas.", "Timeout Conexiones Inactivas", "1. Búsqueda de parámetros de red.\n2. Ejecuto /search.", "Consulto la directiva sobre timeouts de conexiones inactivas.", "/search \"Timeout Conexiones Inactivas\""),
        ("¿Qué sabemos acerca del almacenamiento de objetos con MinIO?", "MinIO Object Storage", "1. Busco el concepto MinIO.\n2. Ejecuto /search.", "Voy a consultar la wiki acerca de MinIO.", "/search \"MinIO Object Storage\""),
        ("Busca la guía de estilo de código para TypeScript.", "Guía Estilo TypeScript", "1. Consulto guía de desarrollo.\n2. Ejecuto /search.", "Reviso las pautas de estilo de código para TypeScript.", "/search \"Guía Estilo TypeScript\""),
        ("¿Hay información sobre particiones lógicas en disco?", "Particiones Lógicas Disco", "1. Búsqueda de almacenamiento.\n2. Ejecuto /search.", "Consulto en la wiki sobre particiones lógicas en disco.", "/search \"Particiones Lógicas Disco\""),
        ("Busca el manual de recuperación ante desastres DRP.", "Plan Recuperación Desastres DRP", "1. Consulta crítica de contingencia.\n2. Invoco /search.", "Consulto la documentación sobre el plan de recuperación ante desastres.", "/search \"Plan Recuperación Desastres DRP\""),
    ]
    for q, term, th, resp, cmd in search_cycles:
        exs.append(make_react(q, th, resp, cmd))

    assert len(exs) == 49, f"Esperados 49 ejemplos adicionales, obtenidos {len(exs)}"
    return exs

