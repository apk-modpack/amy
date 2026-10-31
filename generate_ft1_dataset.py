import ft1_extra
"""Generador de Dataset para Fine-Tuning 1 (FT1): Comunicación CLI y Micro-Formato XML (Reactivo Directo).

Reconstruye fielmente el dataset primario del sistema antes de incorporar Chain-of-Thought (<thought>):
- Prompt de sistema canónico: <MODO: AGENTE> (con o sin inyección de MEMORIA WIKI).
- Bloques de respuesta estructurada estándar:
    <response> ... </response>
    <commands> ... </commands>
- Comandos CLI: /search, /save, /edit, /delete.
- Micro-formato XML: <definition>, <sections>, <relations> (is_a, part_of, relates_to, depends_on, etc.).
- Sin ejemplos ficticios duplicados. Todos los ejemplos son únicos y realistas.
"""

import json
from pathlib import Path


def create_ft1_examples():
    examples = []

    def make_ex(system_text, human_text, response_content, commands_text=""):
        gpt_val = f"<response>\n{response_content.strip()}\n</response>\n<commands>\n{commands_text.strip()}\n</commands>"
        return {
            "conversations": [
                {"from": "system", "value": system_text},
                {"from": "human", "value": human_text},
                {"from": "gpt", "value": gpt_val}
            ]
        }

    # =========================================================================
    # BLOQUE 1: SALUDOS E INFORMACIÓN GENERAL (Sin comandos)
    # =========================================================================
    examples.append(make_ex(
        "<MODO: AGENTE>",
        "Hola, ¿qué herramientas y capacidades tienes?",
        "Hola. Soy un asistente de IA con memoria conceptual estructurada en Wiki. Puedo:\n- Buscar conceptos en mi base de conocimientos (/search)\n- Guardar y definir nuevos conceptos (/save)\n- Enriquecer y corregir información existente (/edit)\n- Eliminar conceptos obsoletos (/delete)\n- Planificar y gestionar tareas cognitivas (/task_add, /task_done, /task_list)\n- Identificarme en la red de agentes (/identify)\n\n¿En qué puedo ayudarte o qué información deseas gestionar?",
        ""
    ))

    examples.append(make_ex(
        "<MODO: AGENTE>",
        "¿Cómo funciona la memoria de este sistema?",
        "Mi memoria no reside en una base opaca, sino en un grafo conceptual estructurado en formato XML. Cada concepto almacena su definición, secciones de detalle y relaciones semánticas (como subtipo 'is_a', dependencia 'depends_on' o parte 'part_of'). Puedo consultar y actualizar este grafo en tiempo real mediante comandos de terminal.",
        ""
    ))

    examples.append(make_ex(
        "<MODO: AGENTE>",
        "¿Qué comandos puedo ejecutar o pedirte que ejecutes?",
        "Dispones de comandos principales de gestión conceptual, tareas e identidad:\n1. `/search \"término\"`: Localiza conceptos relacionados en la wiki.\n2. `/save \"Título\"`: Guarda un nuevo concepto estructurado.\n3. `/edit \"Título\"`: Modifica o amplía un concepto existente.\n4. `/delete \"Título\"`: Borra una entrada obsoleta de la base.\n5. `/task_add`, `/task_done`, `/task_list`: Gestión de tareas cognitivas multi-paso.\n6. `/identify`: Consulta de identidad persistente del agente.",
        ""
    ))

    # =========================================================================
    # BLOQUE 2: BÚSQUEDAS EN WIKI (/search)
    # =========================================================================
    search_queries = [
        ("¿Qué información tenemos sobre Docker y virtualización ligera?", "Docker"),
        ("Busca si tenemos alguna entrada sobre Kubernetes o clusters.", "Kubernetes"),
        ("¿Qué sabemos acerca de la política de copias de seguridad?", "Política de copias de seguridad"),
        ("Consulta en la wiki qué arquitectura definimos para el frontend.", "Arquitectura Frontend"),
        ("Busca la documentación sobre el flujo de autenticación con tokens JWT.", "Autenticación JWT"),
        ("¿Hay registrado algún protocolo para el despliegue a producción?", "Protocolo Despliegue Producción"),
        ("¿Tenemos datos sobre el servicio de caché Redis?", "Redis"),
        ("Busca si existe información sobre los microservicios de facturación.", "Microservicios Facturación"),
        ("¿Qué sabemos sobre las convenciones de commit en Git?", "Convenciones Commit Git"),
        ("Revisa en la wiki qué base de datos principal tenemos configurada.", "Base de Datos Principal"),
        ("Busca documentación sobre la API Gateway del sistema.", "API Gateway"),
        ("¿Qué sabemos acerca del estándar OpenAPI / Swagger?", "OpenAPI")
    ]

    for q, term in search_queries:
        examples.append(make_ex(
            "<MODO: AGENTE>",
            q,
            f"Voy a consultar en la memoria wiki si tenemos información registrada sobre '{term}'.",
            f"/search \"{term}\""
        ))

    # =========================================================================
    # BLOQUE 3: GUARDADO SIMPLE (/save con <definition>)
    # =========================================================================
    simple_saves = [
        (
            "Registra que Python 3.12 es la versión oficial estándar para los nuevos servicios.",
            "Python 3.12",
            "<definition>\nPython 3.12 es la versión de lenguaje adoptada como estándar oficial por el equipo para el desarrollo de nuevos servicios y herramientas.\n</definition>",
            "/save \"Python 3.12\""
        ),
        (
            "Anota que el puerto por defecto de la API interna es el 8080.",
            "Puerto API Interna",
            "<definition>\nEl servicio de API interna escucha por defecto en el puerto 8080 en todos los entornos de desarrollo y pruebas.\n</definition>",
            "/save \"Puerto API Interna\""
        ),
        (
            "Guarda que las copias de seguridad de la base de datos se ejecutan diariamente a las 03:00 UTC.",
            "Backups Base de Datos",
            "<definition>\nLas copias de seguridad automáticas de las bases de datos relacionales se programan diariamente a las 03:00 UTC con retención de 30 días.\n</definition>",
            "/save \"Backups Base de Datos\""
        ),
        (
            "Registra que el timeout máximo para llamadas a APIs externas es de 30 segundos.",
            "Timeout Llamadas Externas",
            "<definition>\nEl tiempo de espera máximo permitido para llamadas HTTP hacia pasarelas o servicios externos está fijado en 30 segundos.\n</definition>",
            "/save \"Timeout Llamadas Externas\""
        ),
        (
            "Guarda que el canal oficial para alertas de infraestructura es #alerta-produccion.",
            "Canal Alertas Infraestructura",
            "<definition>\n#alerta-produccion es el canal de mensajería designado para notificaciones automáticas y coordinación de incidentes en entornos productivos.\n</definition>",
            "/save \"Canal Alertas Infraestructura\""
        ),
        (
            "Anota que usamos SendGrid como proveedor de correo transaccional.",
            "Proveedor Correo Transaccional",
            "<definition>\nSendGrid es la plataforma de entrega de correo electrónico integrada para el envío de notificaciones y emails transaccionales.\n</definition>",
            "/save \"Proveedor Correo Transaccional\""
        )
    ]

    for q, title, resp, cmd in simple_saves:
        examples.append(make_ex("<MODO: AGENTE>", q, resp, cmd))

    # =========================================================================
    # BLOQUE 4: GUARDADO ESTRUCTURADO XML COMPLETO (/save + micro-formato)
    # =========================================================================
    examples.append(make_ex(
        "<MODO: AGENTE>",
        "Crea el concepto 'Machine Learning'. Es una rama de la IA. Ejemplos típicos: redes neuronales y árboles de decisión.",
        (
            "<definition>\n"
            "Machine Learning (Aprendizaje Automático) es una disciplina de la Inteligencia Artificial que permite a los sistemas aprender y mejorar su desempeño de manera autónoma a partir de datos estructurados o no estructurados.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Algoritmos Típicos\">Redes neuronales artificiales, árboles de decisión, máquinas de vectores de soporte (SVM), regresión logística.</section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Inteligencia Artificial\">Es una subdisciplina central de la IA.</relation>\n"
            "</relations>"
        ),
        "/save \"Machine Learning\""
    ))

    examples.append(make_ex(
        "<MODO: AGENTE>",
        "Registra 'Clean Architecture'. Patrón de diseño con capas: Entidades, Casos de Uso, Controladores y Frameworks. Relacionado con Domain-Driven Design.",
        (
            "<definition>\n"
            "Clean Architecture es un patrón de diseño arquitectónico concebido por Robert C. Martin que promueve la separación de responsabilidades y el desacoplamiento estricto de la lógica de negocio respecto a frameworks y librerías externas.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Capas Concéntricas\">\n"
            "- Entidades: Reglas de negocio de la empresa.\n"
            "- Casos de Uso: Reglas de negocio específicas de la aplicación.\n"
            "- Adaptadores de Interfaz: Controladores, Presenters y Gateways.\n"
            "- Frameworks y Drivers: Base de datos, interfaz web y herramientas externas.\n"
            "  </section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Arquitectura de Software\">Patrón arquitectónico modular.</relation>\n"
            "  <relation type=\"relates_to\" target=\"Domain-Driven Design\">Facilita la implementación de modelos de dominio aislados.</relation>\n"
            "</relations>"
        ),
        "/save \"Clean Architecture\""
    ))

    examples.append(make_ex(
        "<MODO: AGENTE>",
        "Crea la página 'GraphQL'. Lenguaje de consultas para APIs alternativo a REST. Depende de un Schema y Resolvers.",
        (
            "<definition>\n"
            "GraphQL es un lenguaje de consultas y motor de ejecución en servidor para APIs que permite a los clientes solicitar exactamente los datos que necesitan mediante una única llamada.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Elementos del Servidor\">\n"
            "- Schema (SDL): Especificación tipada de queries, mutaciones y suscripciones.\n"
            "- Resolvers: Funciones que resuelven los datos para cada campo del esquema.\n"
            "  </section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Tecnología de API\">Protocolo de consulta de datos cliente-servidor.</relation>\n"
            "  <relation type=\"contradicts\" target=\"API REST\">Ofrece endpoint único y consultas exactas frente a endpoints múltiples REST.</relation>\n"
            "  <relation type=\"depends_on\" target=\"Tipado de Datos\">Requiere contratos de tipos estrictos.</relation>\n"
            "</relations>"
        ),
        "/save \"GraphQL\""
    ))

    examples.append(make_ex(
        "<MODO: AGENTE>",
        "Define 'Scrum'. Marco de trabajo ágil basado en sprints. Roles: Product Owner, Scrum Master y Desarrolladores. Relacionado con Metodologías Ágiles.",
        (
            "<definition>\n"
            "Scrum es un framework de trabajo iterativo e incremental para la gestión y desarrollo ágil de proyectos de software, estructurado en ciclos temporales fijos denominados sprints (usualmente de 1 a 4 semanas).\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Roles\">\n"
            "- Product Owner: Representa las necesidades del negocio y prioriza el backlog.\n"
            "- Scrum Master: Facilita los procesos y elimina impedimentos del equipo.\n"
            "- Equipo de Desarrollo: Profesionales multidisciplinares que entregan el incremento funcional.\n"
            "  </section>\n"
            "  <section name=\"Eventos\">\n"
            "- Sprint Planning, Daily Scrum, Sprint Review y Retrospectiva.\n"
            "  </section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Metodología Ágil\">Framework ágil para entrega continua de valor.</relation>\n"
            "  <relation type=\"part_of\" target=\"Gestión de Proyectos\">Mecanismo de organización operativa de equipos.</relation>\n"
            "</relations>"
        ),
        "/save \"Scrum\""
    ))

    examples.append(make_ex(
        "<MODO: AGENTE>",
        "Guarda 'Kubernetes'. Orquestador de contenedores. Objetos principales: Pods, Services, Deployments. Depende de un runtime de contenedores OCI.",
        (
            "<definition>\n"
            "Kubernetes (K8s) es una plataforma open source para la automatización del despliegue, escalado y gestión de aplicaciones empaquetadas en contenedores.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Objetos Fundamentales\">\n"
            "- Pod: Unidad mínima desplegable que aloja uno o más contenedores estrechamente acoplados.\n"
            "- Service: Punto de acceso estable a la red para balancear tráfico hacia pods.\n"
            "- Deployment: Especificación declarativa del estado deseado y ciclo de vida de los pods.\n"
            "  </section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Orquestador de Contenedores\">Herramienta de orquestación a escala cloud.</relation>\n"
            "  <relation type=\"depends_on\" target=\"Contenedores OCI\">Requiere un motor de ejecución compatible (containerd, CRI-O).</relation>\n"
            "  <relation type=\"relates_to\" target=\"Docker\">Gestiona clusters basados en imágenes y estándares OCI.</relation>\n"
            "</relations>"
        ),
        "/save \"Kubernetes\""
    ))

    # =========================================================================
    # BLOQUE 5: EDICIÓN Y ACTUALIZACIÓN (/edit)
    # =========================================================================
    examples.append(make_ex(
        "<MODO: AGENTE>",
        "Actualiza 'React': añade que fue creado por Facebook en 2013 y que usamos la versión 18 con Hooks y Server Components.",
        (
            "<definition>\n"
            "React es una biblioteca de JavaScript declarativa y basada en componentes para la creación de interfaces de usuario modernas.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Historia y Versión\">\n"
            "- Creado por Jordan Walke en Facebook y publicado como código abierto en 2013.\n"
            "- Versión estándar en producción: React 18, haciendo uso intensivo de Hooks y Server Components.\n"
            "  </section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Biblioteca Frontend\">Herramienta para construcción de interfaces de usuario.</relation>\n"
            "</relations>"
        ),
        "/edit \"React\""
    ))

    examples.append(make_ex(
        "<MODO: AGENTE>",
        "Actualiza la entrada de 'PostgreSQL': añade que implementamos replicación streaming asíncrona hacia dos instancias secundarias.",
        (
            "<definition>\n"
            "PostgreSQL es el sistema de gestión de bases de datos relacional y transaccional primario de nuestro ecosistema tecnológico.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Topología de Alta Disponibilidad\">\n"
            "- Instancia primaria para operaciones de escritura (Read-Write).\n"
            "- Dos réplicas de lectura (Read-Only) sincronizadas mediante streaming replication asíncrono para descarga de consultas pesadas.\n"
            "  </section>\n"
            "</sections>"
        ),
        "/edit \"PostgreSQL\""
    ))

    examples.append(make_ex(
        "<MODO: AGENTE>",
        "En la página 'Política de Git', cambia que a partir de ahora los merges a 'main' requieren dos aprobaciones y checks de CI en verde.",
        (
            "<definition>\n"
            "Conjunto de directrices obligatorias de control de versiones y flujo de integración continua en repositorios de la organización.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Reglas de Protección de Rama Main\">\n"
            "- Prohibido el push directo sin Pull Request.\n"
            "- Requiere como mínimo 2 aprobaciones de revisores independientes.\n"
            "- Todos los pipelines automáticos de CI (linters, tests unitarios y auditoría de seguridad) deben finalizar con éxito.\n"
            "  </section>\n"
            "</sections>"
        ),
        "/edit \"Política de Git\""
    ))

    examples.append(make_ex(
        "<MODO: AGENTE>",
        "Modifica 'Reuniones Semanales': el horario se traslada de los jueves a los viernes a las 11:30.",
        (
            "<definition>\n"
            "Sesión semanal de sincronización técnica de los equipos de desarrollo y arquitectura.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Horario y Lugar\">\n"
            "- Viernes de 11:30 a 12:15 en la sala principal y por videoconferencia.\n"
            "  </section>\n"
            "</sections>"
        ),
        "/edit \"Reuniones Semanales\""
    ))

    # =========================================================================
    # BLOQUE 6: ELIMINACIÓN DE CONCEPTOS (/delete)
    # =========================================================================
    delete_cases = [
        ("Elimina la página 'Test_Concepto_Temporal', ya no es necesaria.", "Procediendo a eliminar el concepto 'Test_Concepto_Temporal' de la base de conocimientos.", "/delete \"Test_Concepto_Temporal\""),
        ("Borra la entrada obsoleta 'Servidor_Local_Legacy' de la wiki.", "Eliminando el concepto obsoleto 'Servidor_Local_Legacy'.", "/delete \"Servidor_Local_Legacy\""),
        ("Quita el concepto duplicado 'Borrador_Sprint_Anterior'.", "Eliminando el borrador duplicado 'Borrador_Sprint_Anterior' de la wiki.", "/delete \"Borrador_Sprint_Anterior\""),
        ("Elimina la página 'Concepto_Prueba_123'.", "Eliminando la página de prueba 'Concepto_Prueba_123'.", "/delete \"Concepto_Prueba_123\"")
    ]

    for q, resp, cmd in delete_cases:
        examples.append(make_ex("<MODO: AGENTE>", q, resp, cmd))

    # =========================================================================
    # BLOQUE 7: MEMORIA WIKI INYECTADA (Respuestas asertivas sin comandos)
    # =========================================================================
    examples.append(make_ex(
        (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Gravedad]]: Fuerza física fundamental que atrae los cuerpos con masa entre sí en función de su distancia y masa.\n"
            "--- FIN DE MEMORIA WIKI ---"
        ),
        "¿Qué es la gravedad según nuestra memoria?",
        "La gravedad es una fuerza física fundamental mediante la cual los cuerpos con masa experimentan una atracción mutua proporcional a sus masas e inversamente proporcional al cuadrado de la distancia entre ellos. La tenemos documentada en nuestra base de conocimientos bajo el concepto [[Gravedad]].",
        ""
    ))

    examples.append(make_ex(
        (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Kafka]]: Plataforma distribuida de streaming de eventos capaz de manejar billones de eventos al día.\n"
            "[[Eventos_Facturación]]: Topic particionado donde el microservicio de pagos publica confirmaciones de cobro.\n"
            "--- FIN DE MEMORIA WIKI ---"
        ),
        "¿Cómo viajan los eventos de cobro entre los servicios?",
        "Los eventos de cobro se transmiten a través de [[Kafka]], publicándose específicamente en el topic [[Eventos_Facturación]]. Esto permite que otros módulos, como contabilidad y notificaciones, consuman las confirmaciones de forma totalmente desacoplada y asíncrona.",
        ""
    ))

    examples.append(make_ex(
        (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Gestión de Proyectos]]: La gestión de proyectos organiza el trabajo en hitos, sprints bisemanales y tareas con responsables asignados.\n"
            "--- FIN DE MEMORIA WIKI ---"
        ),
        "¿Cómo está organizada la gestión de proyectos en el sistema?",
        "Nuestra metodología de [[Gestión de Proyectos]] organiza los objetivos estratégicos en hitos temporales. El trabajo operativo se divide en sprints de dos semanas, donde cada tarea cuenta con responsables claros y criterios de aceptación definidos para asegurar entregas periódicas.",
        ""
    ))

    examples.append(make_ex(
        (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Monitoreo]]: Supervisión continua con Prometheus y Grafana para recopilar métricas de latencia y uso de CPU.\n"
            "[[Alertas_Slack]]: Canal #alerta-produccion conectado vía webhooks para avisos automáticos de errores 5xx.\n"
            "--- FIN DE MEMORIA WIKI ---"
        ),
        "¿Dónde recibimos las alertas cuando hay errores en producción?",
        "Las alertas de producción se canalizan a través de [[Alertas_Slack]] en el canal #alerta-produccion mediante webhooks automáticos. El sistema se apoya en [[Monitoreo]] continuo con Prometheus y paneles de Grafana para detectar anomalías de latencia y tasa de errores 5xx.",
        ""
    ))

        # Cargar 62 ejemplos complementarios para alcanzar exactamente 100
    examples.extend(ft1_extra.get_ft1_extra_blocks(make_ex))
    assert len(examples) == 100, f"Error: {len(examples)} != 100"
    return examples


def main():
    out_dir = Path("data/exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "dataset_ft1_cli_standards.jsonl"

    examples = create_ft1_examples()
    with open(out_file, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"[EXITO] Dataset FT1 (CLI standards & XML) generado limpiamente en:")
    print(f"📁 {out_file.resolve()}")
    print(f"Total de ejemplos generados: {len(examples)}")
    print(" - Saludos y capacidades generales: 3 ejemplos")
    print(" - Comandos de búsqueda (/search): 12 ejemplos")
    print(" - Guardado simple (/save): 6 ejemplos")
    print(" - Guardado estructurado XML (/save + micro-formato): 5 ejemplos")
    print(" - Edición (/edit): 4 ejemplos")
    print(" - Borrado (/delete): 4 ejemplos")
    print(" - Memoria Wiki inyectada: 4 ejemplos")


if __name__ == "__main__":
    main()
