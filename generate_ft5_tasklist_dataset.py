"""Generador de Dataset FT5: Lista de Tareas Cognitivas y PlanificaciÃ³n Multi-paso.

Genera exactamente 100 ejemplos Ãºnicos especializados en:
- Bloque 1: Respuestas directas sin tareas (solicitudes simples / informativas / saludos) (50 ejemplos).
- Bloque 2: PlanificaciÃ³n cognitiva estructurada con <tasks> y comandos /task_add, /task_done, /task_list (50 ejemplos).

Formato: ShareGPT con <thought>, <tasks> (cuando aplique), <response>, <commands>.
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
    return {"from": "system", "value": f"<MODO: AGENTE>\n--- MEMORIA WIKI: INFORMACIÃ“N RECUPERADA INICIALMENTE ---\n{content}\n--- FIN DE MEMORIA WIKI ---"}


def _human(text):
    return {"from": "human", "value": text}


def _gpt(thought, response, commands="", tasks=""):
    parts = [f"<thought>\n{thought.strip()}\n</thought>"]
    if tasks:
        parts.append(f"<tasks>\n{tasks.strip()}\n</tasks>")
    if response:
        parts.append(f"<response>\n{response.strip()}\n</response>")
    parts.append(f"<commands>\n{commands.strip()}\n</commands>")
    return {"from": "gpt", "value": "\n".join(parts)}



# ----------------------------------------------------------------
# Utilidades multi-fuente (aÃ±adidas automÃ¡ticamente)
# ----------------------------------------------------------------
import re as _re

_AGENT_NAMES_MS = [
    "Echo-Pilot-12", "Sentinel-Node-03", "Nexus-Core-88",
    "Apex-Scribe-44", "Vector-Mind-21", "Cortex-Pilot-09",
    "Kinetics-Beacon-14", "Matrix-Scribe-77", "Nova-Sentinel-33",
    "Hyper-Oracle-19", "Atlas-Core-01", "Nexus-Pilot-42",
    "Echo-Weaver-99", "Sentinel-Mind-07", "Prism-Oracle-55",
]


def _ms_agent(idx):
    return _AGENT_NAMES_MS[idx % len(_AGENT_NAMES_MS)]


def _ms_patch_thought(gpt_text, agent_name, suffix):
    """Inserta reconocimiento de emisor como punto 1 en <thought> y renumera."""
    t_start = gpt_text.find("<thought>")
    t_end = gpt_text.find("</thought>")
    if t_start == -1 or t_end == -1:
        return gpt_text
    thought_body = gpt_text[t_start + 9:t_end]
    lines = thought_body.split("\n")
    has_numbered = any(_re.match(r"^\d+\.", l.strip()) for l in lines if l.strip())
    sender_line = f"1. Emisor Agente ({agent_name}). {suffix}"
    if has_numbered:
        new_lines = []
        for line in lines:
            m = _re.match(r"^(\d+)\. (.+)", line.strip())
            if m:
                new_lines.append(f"{int(m.group(1)) + 1}. {m.group(2)}")
            else:
                new_lines.append(line)
        new_body = "\n".join([sender_line] + new_lines)
    else:
        new_body = sender_line + "\n" + thought_body
    return gpt_text[:t_start + 9] + new_body + gpt_text[t_end:]


def _ms_apply(examples, conversions):
    """Aplica prefijos de agente y parchea thoughts."""
    for i, (idx, suffix) in enumerate(conversions):
        if idx >= len(examples):
            continue
        convs = examples[idx]["conversations"]
        if convs[1]["value"].startswith("[DE:"):
            continue
        name = _ms_agent(i)
        convs[1]["value"] = f"[DE: {name}]\n{convs[1]['value']}"
        convs[2]["value"] = _ms_patch_thought(convs[2]["value"], name, suffix)
    return examples
# ----------------------------------------------------------------

def create_examples():
    ex = []

    # =========================================================================
    # BLOQUE 1: RESPUESTAS DIRECTAS SIN TAREAS (50 ejemplos)
    # Peticiones directas, consultas informativas simples, saludos y dudas puntuales.
    # El agente razona que NO necesita descomponer en tareas y responde directo.
    # =========================================================================
    direct_data = [
        # 1-10
        ("Â¿QuÃ© es un socket de red?", "1. Solicitud directa y conceptual sobre sockets.\n2. La informaciÃ³n es unÃ­voca y no requiere pasos mÃºltiples.\n3. Respondo directamente sin lista de tareas.", "Un [[Socket]] es un punto final (endpoint) de comunicaciÃ³n bidireccional entre dos procesos en una red."),
        ("Hola, buenos dÃ­as.", "1. Saludo cordial de cortesÃ­a.\n2. No hay proceso cognitivo complejo.\n3. Respondo saludando y ofreciendo asistencia.", "Â¡Buenos dÃ­as! Estoy listo para ayudarte con la memoria wiki o cualquier consulta tÃ©cnica."),
        ("Â¿QuÃ© significa la sigla API?", "1. Pregunta puntual sobre significado de sigla.\n2. Respuesta directa inmediata.\n3. No requiere lista de tareas.", "API significa Application Programming Interface (Interfaz de ProgramaciÃ³n de Aplicaciones)."),
        ("Â¿CuÃ¡l es la funciÃ³n principal de la RAM?", "1. Consulta elemental sobre hardware.\n2. Respuesta directa y concisa.\n3. Sin tareas complejas.", "La [[RAM]] (Memoria de Acceso Aleatorio) almacena temporalmente las instrucciones y datos que la CPU necesita ejecutar de forma inmediata."),
        ("Dime quÃ© comando de git se usa para crear una rama.", "1. Pregunta operativa directa de Git.\n2. Respondo con sintaxis estÃ¡ndar.", "Puedes usar `git branch <nombre>` para crearla, o `git checkout -b <nombre>` (y `git switch -c <nombre>`) para crearla y cambiarte a ella."),
        ("Â¿CuÃ¡l es el puerto estÃ¡ndar de HTTPS?", "1. Consulta de protocolo de red puntual.\n2. Respuesta directa.", "El puerto estÃ¡ndar para [[HTTPS]] es el 443 TCP."),
        ("Â¿QuÃ© es un booleano en programaciÃ³n?", "1. Concepto bÃ¡sico de tipos de datos.\n2. Respuesta directa pedagÃ³gica.", "Un tipo booleano es un tipo de dato que solo puede tener dos valores posibles: verdadero (`True`) o falso (`False`)."),
        ("Gracias por la ayuda anterior.", "1. Mensaje de agradecimiento del usuario.\n2. Respuesta de cortesÃ­a y disponibilidad.", "Â¡De nada! AquÃ­ estoy para cuando necesites continuar trabajando."),
        ("Â¿QuÃ© significa JSON?", "1. Significado de sigla de formato de intercambio.\n2. Respuesta directa.", "JSON significa JavaScript Object Notation, un formato ligero de intercambio de datos legible tanto por humanos como por mÃ¡quinas."),
        ("Â¿CuÃ¡l es la diferencia entre bit y byte?", "1. Pregunta directa de unidades digitales.\n2. Respuesta comparativa puntual.", "Un bit es la unidad mÃ­nima de informaciÃ³n (0 o 1), mientras que un byte estÃ¡ compuesto por un grupo de 8 bits."),

        # 11-20
        ("Â¿QuÃ© es un compilador?", "1. Concepto elemental de ciencias de la computaciÃ³n.\n2. Respuesta directa.", "Un compilador es un programa que traduce cÃ³digo fuente escrito en un lenguaje de alto nivel a lenguaje mÃ¡quina o cÃ³digo binario ejecutable."),
        ("Â¿Para quÃ© sirve el archivo .gitignore?", "1. Pregunta sobre control de versiones.\n2. Respuesta directa.", "El archivo `.gitignore` le indica a Git quÃ© archivos o directorios deliberadamente no deben ser rastreados en el repositorio."),
        ("Â¿QuÃ© es un bucle for?", "1. Estructura de control de flujo bÃ¡sica.\n2. Respuesta directa.", "Un bucle for es una estructura de control que repite un bloque de cÃ³digo un nÃºmero determinado de veces o iterando sobre los elementos de una colecciÃ³n."),
        ("Â¿QuÃ© extensiÃ³n tienen los archivos de Python?", "1. Pregunta directa de entorno de desarrollo.\n2. Respuesta directa.", "Los archivos de cÃ³digo fuente de Python llevan la extensiÃ³n `.py`."),
        ("Â¿QuÃ© es un UUID?", "1. Identificador Ãºnico universal.\n2. Respuesta directa.", "Un [[UUID]] (Universally Unique Identifier) es un identificador de 128 bits utilizado para identificar informaciÃ³n de manera unÃ­voca en sistemas distribuidos."),
        ("Buenas tardes, Â¿cÃ³mo va todo?", "1. Saludo cordial.\n2. Respuesta directa sin tareas.", "Â¡Buenas tardes! Todo funcionando correctamente y listo para trabajar."),
        ("Â¿QuÃ© es una clave primaria en una base de datos?", "1. Concepto bÃ¡sico relacional.\n2. Respuesta directa.", "Una clave primaria (Primary Key) es una columna o conjunto de columnas que identifica de forma Ãºnica cada fila en una tabla de base de datos."),
        ("Â¿CuÃ¡l es el comando de Linux para listar archivos?", "1. Pregunta de terminal estÃ¡ndar.\n2. Respuesta directa.", "El comando estÃ¡ndar es `ls` (y habitualmente `ls -la` para ver detalles y archivos ocultos)."),
        ("Â¿QuÃ© significa HTML?", "1. Significado de sigla web.\n2. Respuesta directa.", "HTML significa HyperText Markup Language (Lenguaje de Marcado de Hipertexto), el estÃ¡ndar para estructurar pÃ¡ginas web."),
        ("Â¿QuÃ© es un puntero en C?", "1. Pregunta directa sobre memoria y C.\n2. Respuesta concisa.", "Un puntero es una variable que almacena la direcciÃ³n de memoria de otra variable en lugar de su valor directo."),

        # 21-30
        ("Â¿QuÃ© es un README?", "1. DocumentaciÃ³n bÃ¡sica de proyectos.\n2. Respuesta directa.", "Un archivo `README` es el documento inicial de un proyecto que explica quÃ© es el software, cÃ³mo instalarlo y cÃ³mo usarlo."),
        ("Â¿QuÃ© es una variable de entorno?", "1. Concepto de configuraciÃ³n de sistema.\n2. Respuesta directa.", "Una variable de entorno es un valor dinÃ¡mico configurado a nivel de sistema operativo que los procesos pueden leer para obtener configuraciones."),
        ("Â¿QuÃ© puerto usa SSH por defecto?", "1. Dato de red estÃ¡ndar.\n2. Respuesta directa.", "El puerto por defecto de [[SSH]] es el 22 TCP."),
        ("Â¿QuÃ© significa CSS?", "1. Lenguaje de hojas de estilo.\n2. Respuesta directa.", "CSS significa Cascading Style Sheets (Hojas de Estilo en Cascada), utilizado para definir la presentaciÃ³n y diseÃ±o visual de documentos HTML."),
        ("Â¿QuÃ© es la recursiÃ³n?", "1. Concepto algorÃ­tmico.\n2. Respuesta concisa.", "La recursiÃ³n es una tÃ©cnica de programaciÃ³n donde una funciÃ³n se llama a sÃ­ misma para resolver un problema dividiÃ©ndolo en casos mÃ¡s pequeÃ±os."),
        ("Â¿CuÃ¡l es el cÃ³digo HTTP para 'No Encontrado'?", "1. CÃ³digo de estado web puntual.\n2. Respuesta directa.", "El cÃ³digo de estado HTTP para recurso no encontrado es el **404 Not Found**."),
        ("Â¿QuÃ© es un branch en Git?", "1. Concepto de ramificaciÃ³n de cÃ³digo.\n2. Respuesta directa.", "Una rama (branch) en Git es un puntero mÃ³vil a un commit especÃ­fico, que permite desarrollar funcionalidades de forma aislada."),
        ("Hasta luego, que tengas buen dÃ­a.", "1. Despedida del usuario.\n2. Respuesta de cortesÃ­a final.", "Â¡Hasta luego! Que tengas un excelente dÃ­a. Quedo a tu disposiciÃ³n cuando vuelvas."),
        ("Â¿QuÃ© es una funciÃ³n pura?", "1. Concepto de programaciÃ³n funcional.\n2. Respuesta directa.", "Una funciÃ³n pura es aquella que, dados los mismos argumentos, siempre devuelve el mismo resultado y no produce efectos secundarios observables."),
        ("Â¿QuÃ© significa SQL?", "1. Lenguaje de consulta de datos.\n2. Respuesta directa.", "SQL significa Structured Query Language (Lenguaje de Consulta Estructurada), el estÃ¡ndar para gestionar bases de datos relacionales."),

        # 31-40
        ("Â¿QuÃ© es un merge conflict en Git?", "1. Escenario comÃºn de integraciÃ³n de cÃ³digo.\n2. Respuesta directa.", "Un conflicto de merge ocurre cuando dos ramas modifican las mismas lÃ­neas de un archivo y Git no puede determinar automÃ¡ticamente cuÃ¡l conservar."),
        ("Â¿QuÃ© es el intÃ©rprete de Python?", "1. Entorno de ejecuciÃ³n de lenguaje.\n2. Respuesta directa.", "Es el programa que lee el cÃ³digo fuente Python, lo compila a bytecode y lo ejecuta lÃ­nea por lÃ­nea en la mÃ¡quina virtual."),
        ("Â¿CuÃ¡l es la diferencia entre TCP y UDP en una frase?", "1. Resumen conciso solicitado.\n2. Respuesta directa en una sola frase.", "TCP es orientado a conexiÃ³n y garantiza la entrega ordenada de paquetes, mientras que UDP es sin conexiÃ³n y prioriza la velocidad sin garantizar entrega."),
        ("Â¿QuÃ© es un array o arreglo?", "1. Estructura de datos fundamental.\n2. Respuesta directa.", "Un array es una estructura de datos que almacena una colecciÃ³n secuencial de elementos del mismo tipo en posiciones de memoria contiguas."),
        ("Â¿QuÃ© comando muestra la ruta actual en Linux?", "1. Pregunta puntual de shell.\n2. Respuesta directa.", "El comando es `pwd` (print working directory)."),
        ("Â¿QuÃ© es una excepciÃ³n en programaciÃ³n?", "1. Mecanismo de gestiÃ³n de anomalÃ­as.\n2. Respuesta directa.", "Una excepciÃ³n es un evento anÃ³malo que ocurre durante la ejecuciÃ³n de un programa e interrumpe el flujo normal de las instrucciones."),
        ("Â¿QuÃ© hace el operador ternario?", "1. Sintaxis condicional compacta.\n2. Respuesta directa.", "El operador ternario evalÃºa una condiciÃ³n booleana y devuelve un valor si es verdadera u otro si es falsa en una sola lÃ­nea."),
        ("Hola, Â¿estÃ¡s disponible?", "1. Consulta de disponibilidad.\n2. Respuesta afirmativa directa.", "SÃ­, estoy completamente disponible para ayudarte."),
        ("Â¿QuÃ© significa DRY en ingenierÃ­a de software?", "1. Principio de diseÃ±o estÃ¡ndar.\n2. Respuesta directa.", "DRY significa 'Don't Repeat Yourself' (No te repitas), un principio enfocado en reducir la duplicaciÃ³n de lÃ³gica en el cÃ³digo."),
        ("Â¿QuÃ© es un linter?", "1. Herramienta de calidad de cÃ³digo.\n2. Respuesta directa.", "Un linter es una herramienta de anÃ¡lisis estÃ¡tico que examina el cÃ³digo fuente en busca de errores sintÃ¡cticos, bugs potenciales y estilo inconsistente."),

        # 41-50
        ("Â¿QuÃ© es un docker container?", "1. Concepto de virtualizaciÃ³n ligera.\n2. Respuesta directa.", "Un contenedor Docker es una unidad estÃ¡ndar de software que empaqueta cÃ³digo y todas sus dependencias para ejecutarse de forma aislada y reproducible."),
        ("Â¿QuÃ© es un deadlock?", "1. Problema de concurrencia.\n2. Respuesta directa.", "Un deadlock (bloqueo mutuo) ocurre cuando dos o mÃ¡s procesos quedan bloqueados indefinidamente esperando recursos bloqueados entre sÃ­."),
        ("Â¿CuÃ¡l es el puerto estÃ¡ndar de HTTP?", "1. Dato de red elemental.\n2. Respuesta directa.", "El puerto por defecto de [[HTTP]] sin cifrar es el 80 TCP."),
        ("Â¿QuÃ© es una API REST?", "1. Estilo de arquitectura de red.\n2. Respuesta directa.", "Una API REST es un servicio web basado en la arquitectura cliente-servidor que utiliza verbos HTTP estÃ¡ndar y representaciones sin estado."),
        ("Â¿QuÃ© es un commit en Git?", "1. OperaciÃ³n de control de versiones.\n2. Respuesta directa.", "Un commit es una instantÃ¡nea (snapshot) permanente e inmutable del estado de los archivos del repositorio en un momento dado."),
        ("Â¿QuÃ© hace la funciÃ³n `len()` en Python?", "1. FunciÃ³n integrada bÃ¡sica.\n2. Respuesta directa.", "La funciÃ³n `len()` devuelve la cantidad de elementos contenidos en un objeto iterable o colecciÃ³n (como listas, cadenas o diccionarios)."),
        ("Â¿QuÃ© es la latencia de red?", "1. MÃ©trica de rendimiento de red.\n2. Respuesta directa.", "La latencia es el tiempo que tarda un paquete de datos en viajar desde el punto de origen hasta su destino a travÃ©s de la red."),
        ("Â¿QuÃ© significa KISS en desarrollo de software?", "1. FilosofÃ­a de diseÃ±o.\n2. Respuesta directa.", "KISS significa 'Keep It Simple, Stupid' (Mantenlo simple), promoviendo que los sistemas funcionen mejor cuando son sencillos y no se sobrecomplican."),
        ("Â¿QuÃ© es un repositorio remoto?", "1. Concepto de Git distribuido.\n2. Respuesta directa.", "Un repositorio remoto es una copia del proyecto alojada en un servidor o red (como GitHub o GitLab) accesible por mÃºltiples desarrolladores."),
        ("Â¿QuÃ© es una tupla en Python?", "1. Tipo de estructura de datos.\n2. Respuesta directa.", "Una tupla en Python es una secuencia ordenada e inmutable de elementos delimitada por parÃ©ntesis `(...)`."),
    ]

    for q, thought, ans in direct_data:
        ex.append(_conv(
            _sys(),
            _human(q),
            _gpt(thought, ans, commands="")
        ))

    # =========================================================================
    # BLOQUE 2: PLANIFICACIÃ“N COGNITIVA CON <tasks> Y COMANDOS (50 ejemplos)
    # Tareas complejas, comparativas, auditorÃ­as, sincronizaciones, migraciones,
    # pipelines, anÃ¡lisis multi-etapa y refactorizaciones.
    # =========================================================================
    tasks_data = [
        # 1-10
        (
            "Necesito que analices la arquitectura de nuestro backend, compares Redis con RabbitMQ para el broker de eventos, y prepares una recomendaciÃ³n tÃ©cnica estructurada.",
            "1. PeticiÃ³n compleja con mÃºltiples fases (anÃ¡lisis, comparativa tÃ©cnica y sÃ­ntesis).\n2. Requiere descomposiciÃ³n en plan cognitivo explÃ­cito con <tasks>.\n3. Inicializo la lista de tareas y ejecuto el primer paso.",
            "- [ ] 1. Analizar requisitos de mensajerÃ­a del backend\n- [ ] 2. Comparar Redis Streams vs RabbitMQ en persistencia y entrega\n- [ ] 3. Sintetizar recomendaciÃ³n tÃ©cnica para el equipo",
            "He planificado el proceso cognitivo para evaluar el broker de eventos.",
            '/task_add "Verificar compatibilidad con stack FastAPI existente"'
        ),
        (
            "Queremos migrar nuestra base de datos SQLite a PostgreSQL en producciÃ³n. DiseÃ±a el plan completo paso a paso.",
            "1. Proceso crÃ­tico de infraestructura y migraciÃ³n de datos.\n2. Divido en plan de tareas cognitivo ordenado con <tasks>.\n3. Registro las fases de ejecuciÃ³n.",
            "- [ ] 1. Auditar esquema relacional actual y tipos de datos incompatibles\n- [ ] 2. Configurar instancia PostgreSQL de destino y pooling\n- [ ] 3. DiseÃ±ar pipeline de volcados y migraciÃ³n con pgloader\n- [ ] 4. Validar integridad referencial y tests de regresiÃ³n",
            "He estructurado el plan de tareas para la migraciÃ³n de datos hacia PostgreSQL.",
            "/task_list"
        ),
        (
            "Haz una auditorÃ­a de seguridad del mÃ³dulo de autenticaciÃ³n: verifica hashing de contraseÃ±as, expiraciÃ³n de tokens JWT y protecciÃ³n contra fuerza bruta.",
            "1. AuditorÃ­a exhaustiva de seguridad de tres vectores independientes.\n2. Declaro lista de tareas con <tasks> para no omitir ningÃºn vector.",
            "- [ ] 1. Revisar algoritmo de hashing (Argon2 / bcrypt)\n- [ ] 2. Verificar tiempo de expiraciÃ³n y rotaciÃ³n de claves en JWT\n- [ ] 3. Comprobar rate limiting y protecciÃ³n contra ataques de fuerza bruta",
            "Iniciando auditorÃ­a de seguridad del sistema de autenticaciÃ³n segÃºn la lista de tareas.",
            '/task_done "1"'
        ),
        (
            "Reorganiza la memoria wiki sobre el concepto [[Arquitectura Limpia]], extrayendo casos de uso a un concepto nuevo y actualizando las relaciones.",
            "1. RefactorizaciÃ³n estructural en la memoria Wiki.\n2. Requiere leer concepto original, crear nuevo concepto con /save y actualizar relaciones con /edit.\n3. Descompongo con <tasks>.",
            "- [ ] 1. Leer concepto actual [[Arquitectura Limpia]] con /read\n- [ ] 2. Estructurar nuevo concepto [[Casos de Uso]] con /save\n- [ ] 3. Actualizar relaciones del concepto padre con /edit",
            "",
            '/read "Arquitectura Limpia"'
        ),
        (
            "Compara las estrategias de cachÃ© Cache-Aside vs Write-Through y propÃ³n cuÃ¡l aplicar para nuestro catÃ¡logo de lectura intensiva.",
            "1. Comparativa tÃ©cnica de patrones de arquitectura.\n2. Planifico la evaluaciÃ³n y el caso de uso especÃ­fico.",
            "- [ ] 1. Detallar funcionamiento y ventajas de Cache-Aside\n- [ ] 2. Detallar funcionamiento y latencias de Write-Through\n- [ ] 3. Contrastar con el patrÃ³n de lectura intensiva y emitir veredicto",
            "Plan de evaluaciÃ³n de patrones de cachÃ© registrado.",
            "/task_list"
        ),
        (
            "DiseÃ±a una estrategia de pruebas completa para el agente: unitarias, integraciÃ³n de sockets y carga de red.",
            "1. PlanificaciÃ³n de pirÃ¡mide de testing multi-nivel.\n2. Desglose en tareas secuenciales.",
            "- [ ] 1. Definir suite unitaria para lÃ³gica de comandos y parsing\n- [ ] 2. Configurar tests de integraciÃ³n cliente-servidor con sockets TCP\n- [ ] 3. DiseÃ±ar prueba de estrÃ©s con mensajes fragmentados y clientes concurrentes",
            "Estrategia de testing descompuesta en lista de tareas.",
            '/task_add "AÃ±adir verificaciÃ³n de mocks de LLM en suite CI"'
        ),
        (
            "Audita el pipeline de CI/CD: linters, suite de tests automÃ¡ticos y empaquetado Docker multi-stage.",
            "1. AuditorÃ­a del pipeline de integraciÃ³n continua.\n2. Plan cognitivo de 3 pasos para cubrir cada fase.",
            "- [ ] 1. Revisar configuraciÃ³n de Flake8, Ruff y MyPy en pre-commit\n- [ ] 2. Auditar ejecuciÃ³n paralela de tests y cobertura mÃ­nima\n- [ ] 3. Optimizar Dockerfile con build multi-stage para reducir peso de imagen",
            "Iniciando revisiÃ³n integral del pipeline CI/CD.",
            '/task_done "1"'
        ),
        (
            "Analiza cÃ³mo implementar autenticaciÃ³n multifactor (MFA) con TOTP y prepara el flujo de enrolamiento.",
            "1. Solicitud de diseÃ±o de arquitectura de autenticaciÃ³n robusta.\n2. DescomposiciÃ³n en etapas de enrolamiento y verificaciÃ³n.",
            "- [ ] 1. Definir generaciÃ³n de secretos TOTP y cÃ³digo QR con RFC 6238\n- [ ] 2. DiseÃ±ar almacenamiento seguro cifrado de secretos en BD\n- [ ] 3. Implementar endpoint de validaciÃ³n de cÃ³digo temporal y cÃ³digos de recuperaciÃ³n",
            "He establecido el plan cognitivo para el mÃ³dulo de MFA.",
            "/task_list"
        ),
        (
            "Investiga el impacto de migrar nuestro backend a arquitectura orientada a eventos con Kafka.",
            "1. AnÃ¡lisis de viabilidad y trade-offs arquitectÃ³nicos.\n2. Plan de anÃ¡lisis cognitivo paso a paso.",
            "- [ ] 1. Evaluar casos de uso que justifiquen desacoplamiento asÃ­ncrono\n- [ ] 2. Analizar complejidad de infraestructura, particiones y retenciÃ³n\n- [ ] 3. Formular matriz de costos de mantenimiento y curva de aprendizaje",
            "Plan de anÃ¡lisis de arquitectura de eventos configurado.",
            '/task_add "Verificar compatibilidad con herramientas de observabilidad OpenTelemetry"'
        ),
        (
            "Prepara una guÃ­a para nuevos desarrolladores que incluya setup de entorno virtual, variables de entorno y primer despliegue local.",
            "1. Plan pedagÃ³gico de onboarding tÃ©cnico.\n2. EstructuraciÃ³n en tareas claras.",
            "- [ ] 1. Redactar requisitos de runtime y clonaciÃ³n de repositorio\n- [ ] 2. Detallar creaciÃ³n de virtualenv e instalaciÃ³n de dependencias\n- [ ] 3. Configurar archivo .env de ejemplo y comandos de arranque",
            "Plan de onboarding tÃ©cnico listo en la lista de tareas.",
            '/task_done "1"'
        ),

        # 11-20
        (
            "EvalÃºa la viabilidad de implementar GraphQL frente a nuestra actual API REST.",
            "1. Comparativa de protocolos de capa de transporte y presentaciÃ³n.\n2. Desglose en criterios de evaluaciÃ³n.",
            "- [ ] 1. Analizar problemas actuales de over-fetching y under-fetching\n- [ ] 2. Comparar complejidad de esquemas, resolvers y caching HTTP\n- [ ] 3. Emitir recomendaciÃ³n adaptada a la escala de nuestro equipo",
            "Plan cognitivo inicializado para la evaluaciÃ³n de GraphQL vs REST.",
            "/task_list"
        ),
        (
            "DiseÃ±a un protocolo de respaldo y recuperaciÃ³n ante desastres (Disaster Recovery) para la base de datos de producciÃ³n.",
            "1. DiseÃ±o crÃ­tico de continuidad de negocio.\n2. Estructuro en tareas de backup, replicaciÃ³n y simulacros.",
            "- [ ] 1. Definir polÃ­ticas de snapshots completos diarios e incrementales con WAL-G\n- [ ] 2. Configurar replicaciÃ³n cross-region con almacenamiento en frÃ­o S3\n- [ ] 3. Establecer simulacros periÃ³dicos de restauraciÃ³n y validaciÃ³n de RTO/RPO",
            "Plan de continuidad y Disaster Recovery establecido.",
            '/task_done "1"'
        ),
        (
            "Revisa la gestiÃ³n de conexiones a base de datos y optimiza los parÃ¡metros de Connection Pooling.",
            "1. OptimizaciÃ³n de rendimiento de capa de datos.\n2. Plan de anÃ¡lisis de pool y contenciÃ³n.",
            "- [ ] 1. Medir mÃ©tricas de conexiones activas, idle y picos de trÃ¡fico\n- [ ] 2. Configurar pool_size, max_overflow y pool_timeout en SQLAlchemy\n- [ ] 3. Validar comportamiento bajo prueba de estrÃ©s con Locust",
            "Plan de optimizaciÃ³n de pooling registrado en tareas.",
            '/task_done "1"'
        ),
        (
            "Crea una especificaciÃ³n tÃ©cnica para implementar un sistema de logs estructurados con OpenTelemetry y Loki.",
            "1. EspecificaciÃ³n de observabilidad integral.\n2. Fases de diseÃ±o de trazas, mÃ©tricas y recolecciÃ³n.",
            "- [ ] 1. Definir formato de logs JSON canÃ³nico con correlation IDs y trace_id\n- [ ] 2. Integrar instrumentaciÃ³n automÃ¡tica de FastAPI con OpenTelemetry SDK\n- [ ] 3. Configurar agente colector (Vector/Fluentbit) para exportar hacia Grafana Loki",
            "Plan de diseÃ±o de observabilidad registrado.",
            "/task_list"
        ),
        (
            "Desarrolla un plan de refactorizaciÃ³n para desacoplar el mÃ³dulo de facturaciÃ³n del monolito.",
            "1. Estrategia de desacoplamiento de arquitectura monolÃ­tica.\n2. Fases de anÃ¡lisis de dominio y extracciÃ³n gradual.",
            "- [ ] 1. Identificar lÃ­mites de contexto (Bounded Context) de facturaciÃ³n\n- [ ] 2. DiseÃ±ar interfaz de eventos de dominio para evitar dependencias directas\n- [ ] 3. Planificar migraciÃ³n con patrÃ³n Strangler Fig sin downtime",
            "Estrategia de refactorizaciÃ³n estructurada en lista de tareas cognitivas.",
            '/task_add "DiseÃ±ar esquema de base de datos dedicada para facturaciÃ³n"'
        ),
        (
            "Audita el consumo de memoria del agente e identifica posibles fugas en el bucle principal de chat.",
            "1. DiagnÃ³stico de rendimiento interno del agente.\n2. Plan de profiling y revisiÃ³n de referencias circulares.",
            "- [ ] 1. Monitorear crecimiento de ConversationHistory a lo largo de mÃºltiples turnos\n- [ ] 2. Auditar retenciÃ³n de objetos en cachÃ© de embeddings y gestor wiki\n- [ ] 3. Ejecutar pruebas con tracemalloc para verificar liberaciÃ³n de memoria",
            "Plan de profiling de memoria iniciado.",
            '/task_done "1"'
        ),
        (
            "DiseÃ±a un sistema de control de acceso basado en roles (RBAC) con permisos granulares por recurso.",
            "1. Modelado de seguridad y autorizaciÃ³n.\n2. Desglose en modelo entidad-relaciÃ³n y middleware de verificaciÃ³n.",
            "- [ ] 1. DiseÃ±ar entidades Roles, Permisos y Asignaciones de Usuario\n- [ ] 2. Implementar decorador de autorizaciÃ³n en endpoints de API\n- [ ] 3. Crear suite de tests para asegurar denegaciÃ³n por defecto (fail-secure)",
            "Plan de arquitectura de autorizaciÃ³n RBAC registrado.",
            "/task_list"
        ),
        (
            "Estudia la transiciÃ³n de polling HTTP a Server-Sent Events (SSE) para notificaciones en tiempo real en la UI.",
            "1. EvaluaciÃ³n de patrÃ³n de push unidireccional.\n2. Tareas cognitivas de anÃ¡lisis y diseÃ±o de transporte.",
            "- [ ] 1. Analizar compatibilidad con proxies inversos y timeouts de conexiÃ³n HTTP/2\n- [ ] 2. DiseÃ±ar generador de eventos asÃ­ncrono en FastAPI con StreamingResponse\n- [ ] 3. Definir reconexiÃ³n automÃ¡tica y control de Last-Event-ID en frontend",
            "Plan cognitivo de migraciÃ³n a Server-Sent Events inicializado.",
            '/task_done "1"'
        ),
        (
            "EvalÃºa incorporar un motor de bÃºsqueda semÃ¡ntica con embeddings vectoriales en la memoria wiki.",
            "1. AmpliaciÃ³n de capacidades de recuperaciÃ³n de informaciÃ³n del agente.\n2. Plan de anÃ¡lisis de modelos y almacenamiento vectorial.",
            "- [ ] 1. Evaluar modelos de embeddings locales ligeros (BGE-small, MiniLM)\n- [ ] 2. Comparar motores vectoriales embebidos (ChromaDB, SQLite-vec, FAISS)\n- [ ] 3. DiseÃ±ar bÃºsqueda hÃ­brida BM25 + similitud de coseno con re-ranking",
            "Plan de bÃºsqueda semÃ¡ntica registrado en la lista de tareas.",
            '/task_add "Medir overhead de latencia en bÃºsquedas hÃ­bridas"'
        ),
        (
            "Organiza una revisiÃ³n de dependencias para actualizar paquetes con vulnerabilidades conocidas (CVEs).",
            "1. Tarea de mantenimiento preventivo de seguridad de software.\n2. Tareas de escaneo, actualizaciÃ³n y verificaciÃ³n.",
            "- [ ] 1. Ejecutar escÃ¡ner de vulnerabilidades con `pip-audit` y `safety`\n- [ ] 2. Actualizar dependencias crÃ­ticas en poetry.lock / requirements.txt\n- [ ] 3. Ejecutar suite de integraciÃ³n completa para asegurar retrocompatibilidad",
            "Iniciando plan de saneamiento de dependencias y parches de seguridad.",
            '/task_done "1"'
        ),

        # 21-30
        (
            "DiseÃ±a un plan para dockerizar la aplicaciÃ³n en entornos de desarrollo y producciÃ³n.",
            "1. EstandarizaciÃ³n de despliegue mediante contenedores.\n2. Fases de Dockerfile multi-stage y Docker Compose.",
            "- [ ] 1. Crear Dockerfile optimizado con usuario sin privilegios y capas de cachÃ©\n- [ ] 2. Configurar docker-compose.yml para entorno de desarrollo con hot-reload\n- [ ] 3. Configurar docker-compose.prod.yml con reinicio automÃ¡tico y volÃºmenes persistentes",
            "Plan de contenerizaciÃ³n establecido en lista de tareas.",
            "/task_list"
        ),
        (
            "DiseÃ±a una polÃ­tica de gestiÃ³n de secretos para evitar credenciales hardcodeadas en repositorios.",
            "1. Seguridad preventiva y gestiÃ³n de credenciales.\n2. Tareas de detecciÃ³n, vault y rotaciÃ³n.",
            "- [ ] 1. Escanear repositorio con gitleaks para detectar credenciales expuestas\n- [ ] 2. Configurar HashiCorp Vault o AWS Secrets Manager para inyecciÃ³n en runtime\n- [ ] 3. Establecer rotaciÃ³n programada de claves y tokens de servicio",
            "Plan de gestiÃ³n de secretos registrado.",
            '/task_done "1"'
        ),
        (
            "PropÃ³n una arquitectura de micro-frontends para el panel de administraciÃ³n modular.",
            "1. Arquitectura de frontend distribuida.\n2. Fases de federaciÃ³n de mÃ³dulos y shell anfitriÃ³n.",
            "- [ ] 1. Definir framework anfitriÃ³n con Webpack Module Federation\n- [ ] 2. Establecer directrices de aislamiento de estilos CSS y estado compartido\n- [ ] 3. DiseÃ±ar pipeline independiente de compilaciÃ³n y despliegue por mÃ³dulo",
            "Plan de arquitectura de micro-frontends registrado.",
            "/task_list"
        ),
        (
            "DiseÃ±a un pipeline de procesamiento por lotes (Batch Processing) para conciliar transacciones nocturnas.",
            "1. Procesamiento masivo de datos con tolerancia a fallos.\n2. Tareas de ingestiÃ³n, validaciÃ³n y reporte.",
            "- [ ] 1. DiseÃ±ar lector de lotes con paginaciÃ³n basada en cursores para evitar sobrecarga\n- [ ] 2. Implementar lÃ³gica idempotente de conciliaciÃ³n con transacciones atÃ³micas\n- [ ] 3. Configurar alertas automÃ¡ticas en caso de transacciones no conciliadas",
            "Plan de pipeline de conciliaciÃ³n por lotes configurado.",
            '/task_add "Configurar reintentos automÃ¡ticos con backoff exponencial"'
        ),
        (
            "Realiza un anÃ¡lisis comparativo de bases de datos de series temporales: TimescaleDB vs InfluxDB.",
            "1. Comparativa tÃ©cnica de motores especializados en mÃ©tricas temporales.\n2. Tareas de anÃ¡lisis de sintaxis SQL, compresiÃ³n y ecosistema.",
            "- [ ] 1. Evaluar TimescaleDB: extensiÃ³n PostgreSQL, consultas SQL completas y joins\n- [ ] 2. Evaluar InfluxDB: compresiÃ³n nativa, motor InfluxQL/Flux y ecosistema de agentes\n- [ ] 3. Emitir recomendaciÃ³n segÃºn las capacidades de nuestro equipo en SQL",
            "Plan de comparativa de motores temporales registrado.",
            '/task_done "1"'
        ),
        (
            "DiseÃ±a una estrategia de internacionalizaciÃ³n (i18n) para soportar mÃºltiples idiomas en la plataforma.",
            "1. Soporte multilingÃ¼e en frontend y backend.\n2. Fases de extracciÃ³n de textos, almacenamiento y negociaciÃ³n de contenido.",
            "- [ ] 1. Configurar biblioteca gettext en backend y vue-i18n / i18next en frontend\n- [ ] 2. DiseÃ±ar middleware de detecciÃ³n por cabecera Accept-Language o perfil\n- [ ] 3. Establecer flujo de trabajo con archivos .po / .json para traductores",
            "Plan de internacionalizaciÃ³n inicializado.",
            "/task_list"
        ),
        (
            "Audita y optimiza el tiempo de compilaciÃ³n y empaquetado de assets de frontend.",
            "1. Rendimiento del tooling de desarrollo frontend.\n2. Tareas de profiling de dependencias y migraciÃ³n de bundler.",
            "- [ ] 1. Analizar cuellos de botella del build con webpack-bundle-analyzer\n- [ ] 2. Evaluar migraciÃ³n a Vite o esbuild para builds ultrarrÃ¡pidos\n- [ ] 3. Implementar code splitting y lazy loading en rutas secundarias",
            "Plan de optimizaciÃ³n de build de frontend registrado.",
            '/task_done "1"'
        ),
        (
            "DiseÃ±a un mecanismo de rate limiting distribuido para proteger los endpoints pÃºblicos de la API.",
            "1. ProtecciÃ³n contra abuso y saturaciÃ³n de API.\n2. Tareas cognitivas de algoritmo de ventana deslizante y almacÃ©n Redis.",
            "- [ ] 1. DiseÃ±ar algoritmo Sliding Window Counter sobre Redis con scripts Lua\n- [ ] 2. Implementar middleware HTTP retornando cabeceras 429 y Retry-After\n- [ ] 3. Crear lista blanca para clientes internos y rangos de IPs autorizados",
            "Plan de rate limiting distribuido establecido.",
            '/task_done "1"'
        ),
        (
            "Planifica la estrategia de versionado de la API pÃºblica para garantizar retrocompatibilidad durante 2 aÃ±os.",
            "1. Gobierno de interfaces y ciclo de vida de APIs.\n2. Fases de versionado por URL, deprecaciÃ³n y documentaciÃ³n.",
            "- [ ] 1. Adoptar versionado en ruta URI `/v1/`, `/v2/` con contratos inmutables\n- [ ] 2. Establecer polÃ­tica de deprecaciÃ³n formal con cabecera Sunset (RFC 8594)\n- [ ] 3. Mantener documentaciÃ³n interactiva versionada con OpenAPI/Swagger",
            "Estrategia de versionado de API pÃºblica registrada.",
            "/task_list"
        ),
        (
            "DiseÃ±a un flujo de trabajo para gestionar la documentaciÃ³n viva de arquitectura mediante Architectural Decision Records (ADRs).",
            "1. FormalizaciÃ³n de decisiones arquitectÃ³nicas del equipo.\n2. Tareas de plantilla, almacenamiento y proceso de revisiÃ³n.",
            "- [ ] 1. Adoptar plantilla canÃ³nica de ADR (Contexto, DecisiÃ³n, Consecuencias)\n- [ ] 2. Integrar herramienta `adr-tools` en el repositorio bajo carpeta `docs/adr/`\n- [ ] 3. Definir regla de pull requests donde cambios de arquitectura requieran un ADR",
            "Plan de implementaciÃ³n de ADRs estructurado en lista de tareas.",
            '/task_done "1"'
        ),

        # 31-40
        (
            "Establece una polÃ­tica de retenciÃ³n y purga automÃ¡tica de datos conforme al RGPD.",
            "1. Cumplimiento legal y saneamiento de datos personales.\n2. Fases de inventario de datos, derecho al olvido y tareas cron.",
            "- [ ] 1. Identificar tablas y campos que contienen datos personales (PII)\n- [ ] 2. Implementar servicio de anonimizaciÃ³n y borrado en cascada para derecho al olvido\n- [ ] 3. Programar job periÃ³dico de purga de logs y sesiones inactivas tras 90 dÃ­as",
            "Plan de cumplimiento RGPD registrado.",
            "/task_list"
        ),
        (
            "DiseÃ±a un sistema de colas de reintento con Dead Letter Queue (DLQ) para pagos fallidos.",
            "1. Resiliencia en operaciones financieras crÃ­ticas.\n2. Tareas de backoff exponencial, jitter y cola de mensajes muertos.",
            "- [ ] 1. Implementar reintentos automÃ¡ticos con backoff exponencial y jitter\n- [ ] 2. Enrutar mensajes persistentes a una Dead Letter Queue (DLQ) tras 5 fallos\n- [ ] 3. Crear interfaz de administraciÃ³n para inspecciÃ³n manual y reencolado de pagos",
            "Plan de resiliencia con DLQ establecido.",
            '/task_add "AÃ±adir notificaciÃ³n por webhook ante fallo definitivo en DLQ"'
        ),
        (
            "EvalÃºa la adopciÃ³n de gRPC para la comunicaciÃ³n de alta velocidad entre nuestros microservicios.",
            "1. ComunicaciÃ³n entre servicios con contratos fuertemente tipados.\n2. Comparativa de rendimiento protobuf vs JSON y complejidad de tooling.",
            "- [ ] 1. Definir archivos .proto con contratos de servicio estrictos\n- [ ] 2. Comparar rendimiento de serializaciÃ³n binaria frente a JSON en alta carga\n- [ ] 3. Analizar impacto en depuraciÃ³n, inspecciÃ³n de paquetes y balanceo de carga",
            "Plan cognitivo para evaluaciÃ³n de gRPC iniciado.",
            '/task_done "1"'
        ),
        (
            "DiseÃ±a un sistema de feature flags dinÃ¡micas para desplegar funcionalidades de forma progresiva.",
            "1. Entrega continua controlada sin redeploys.\n2. Tareas de motor de evaluaciÃ³n en memoria, sincronizaciÃ³n y toggle UI.",
            "- [ ] 1. DiseÃ±ar modelo de flags con activaciÃ³n por porcentaje de usuarios o entorno\n- [ ] 2. Implementar cliente con cachÃ© en memoria y suscripciÃ³n a eventos de cambio\n- [ ] 3. Crear interfaz web para que el equipo de producto active/desactive flags",
            "Plan de feature flags registrado en tareas.",
            "/task_list"
        ),
        (
            "Audita y optimiza el consumo de CPU durante la indexaciÃ³n de pÃ¡ginas en la memoria Wiki.",
            "1. Rendimiento interno de indexaciÃ³n de la Wiki.\n2. Tareas de anÃ¡lisis de expresiones regulares, parsing y procesamiento batch.",
            "- [ ] 1. Perfilar funciones de extracciÃ³n XML y regex con cProfile\n- [ ] 2. Optimizar compilaciÃ³n previa de patrones `re.compile` en mÃ³dulos de parsing\n- [ ] 3. Procesar indexaciÃ³n de conceptos en lotes aprovechando mÃºltiples nÃºcleos",
            "Plan de profiling de CPU en indexaciÃ³n wiki registrado.",
            '/task_done "1"'
        ),
        (
            "DiseÃ±a un plan de pruebas de carga para simular 10.000 usuarios concurrentes en la tienda online.",
            "1. Pruebas de estrÃ©s y lÃ­mites de capacidad del sistema.\n2. Tareas de diseÃ±o de escenarios, mÃ©tricas y ejecuciÃ³n con Locust/k6.",
            "- [ ] 1. Definir escenarios de usuario representativos (navegaciÃ³n, bÃºsqueda, checkout)\n- [ ] 2. Configurar infraestructura de generadores de carga distribuidos en la nube\n- [ ] 3. Analizar mÃ©tricas de saturaciÃ³n de CPU, tiempos de respuesta p99 y cuellos de botella",
            "Plan de pruebas de carga a escala registrado.",
            '/task_done "1"'
        ),
        (
            "PropÃ³n una arquitectura serverless con AWS Lambda para el procesamiento de imÃ¡genes subidas por usuarios.",
            "1. Arquitectura escalable orientada a eventos en la nube.\n2. Fases de bucket S3, trigger de Lambda y generaciÃ³n de miniaturas.",
            "- [ ] 1. Configurar trigger de subida en bucket S3 hacia funciÃ³n Lambda\n- [ ] 2. Implementar funciÃ³n con Pillow/libvips para generar variantes webp optimizadas\n- [ ] 3. Almacenar metadatos resultantes en base de datos y distribuir por CDN",
            "Plan de procesamiento serverless estructurado en tareas.",
            "/task_list"
        ),
        (
            "DiseÃ±a una polÃ­tica de gestiÃ³n de ramas y flujos de trabajo en Git adaptada a despliegues diarios (Trunk-Based Development).",
            "1. Estrategia de control de versiones Ã¡gil.\n2. Tareas de directrices de ramas de corta duraciÃ³n, feature flags y CI.",
            "- [ ] 1. Definir ciclo de vida de ramas de corta duraciÃ³n (< 24 horas) integradas a main\n- [ ] 2. Sustituir ramas de release por feature flags para cÃ³digo no finalizado\n- [ ] 3. Automatizar validaciÃ³n rigurosa de tests en cada commit directo o PR",
            "Plan de transiciÃ³n a Trunk-Based Development registrado.",
            '/task_done "1"'
        ),
        (
            "DiseÃ±a un sistema de auditorÃ­a de actividad de usuarios (Audit Logs) inmutable para cumplimiento normativo.",
            "1. Registro inmutable de trazabilidad de operaciones crÃ­ticas.\n2. Tareas de esquema de evento, firma criptogrÃ¡fica y retenciÃ³n.",
            "- [ ] 1. Definir esquema estÃ¡ndar: actor_id, acciÃ³n, recurso, timestamp y payload_diff\n- [ ] 2. Almacenar logs en base de datos append-only con encadenamiento de hashes tipo blockchain\n- [ ] 3. Exportar backups periÃ³dicos firmados criptogrÃ¡ficamente hacia almacenamiento WORM",
            "Plan de Audit Logs inmutables registrado en tareas.",
            "/task_list"
        ),
        (
            "Planifica la modernizaciÃ³n de nuestro frontend migrando de componentes de clase a hooks funcionales.",
            "1. RefactorizaciÃ³n tÃ©cnica progresiva de base de cÃ³digo frontend.\n2. Fases de identificaciÃ³n de componentes, refactorizaciÃ³n y verificaciÃ³n.",
            "- [ ] 1. Identificar componentes legacy de clase con mayor deuda tÃ©cnica o complejidad\n- [ ] 2. Refactorizar a componentes funcionales con hooks estÃ¡ndar (useState, useEffect, custom hooks)\n- [ ] 3. Ejecutar tests unitarios con React Testing Library para garantizar equivalencia funcional",
            "Plan de modernizaciÃ³n a hooks funcionales configurado.",
            '/task_done "1"'
        ),

        # 41-50
        (
            "DiseÃ±a un middleware para correlaciÃ³n de peticiones distribuidas mediante Request IDs en microservicios.",
            "1. Trazabilidad de peticiones de extremo a extremo.\n2. Tareas de inyecciÃ³n de cabecera X-Request-ID, propagaciÃ³n en contexto y logs.",
            "- [ ] 1. Implementar middleware que genere o propague la cabecera `X-Request-ID`\n- [ ] 2. Almacenar el ID en variables de contexto (`contextvars`) de Python por solicitud\n- [ ] 3. Inyectar automÃ¡ticamente el Request ID en todos los logs y llamadas HTTP salientes",
            "Plan de correlaciÃ³n con Request IDs establecido.",
            "/task_list"
        ),
        (
            "DiseÃ±a una arquitectura de Webhooks para que plataformas externas reciban notificaciones de eventos en nuestra API.",
            "1. IntegraciÃ³n asÃ­ncrona hacia terceros.\n2. Tareas de registro de suscripciones, entrega con reintentos y firma HMAC.",
            "- [ ] 1. DiseÃ±ar tabla de suscripciones con URL de callback y secreto compartido\n- [ ] 2. Firmar payload con HMAC-SHA256 en la cabecera `X-Signature`\n- [ ] 3. Despachar envÃ­os en workers en segundo plano con reintentos y deshabilitaciÃ³n tras fallos reiterados",
            "Plan de arquitectura de Webhooks salientes configurado.",
            '/task_done "1"'
        ),
        (
            "DiseÃ±a un plan de migraciÃ³n hacia infraestructura como cÃ³digo (IaC) utilizando Terraform.",
            "1. AutomatizaciÃ³n y versionado de infraestructura en la nube.\n2. Fases de auditorÃ­a de recursos manuales, importaciÃ³n y validaciÃ³n.",
            "- [ ] 1. Realizar inventario de servidores, redes y bases de datos creados manualmente\n- [ ] 2. Escribir mÃ³dulos de Terraform e importar estado existente con `terraform import`\n- [ ] 3. Integrar pipeline de `terraform plan` en PRs y `apply` automatizado en main",
            "Plan de adopciÃ³n de Terraform estructurado en lista de tareas.",
            "/task_list"
        ),
        (
            "EvalÃºa la implementaciÃ³n de canary releases para mitigar riesgos en nuevos despliegues de producciÃ³n.",
            "1. Estrategia de entrega progresiva y monitorizaciÃ³n de errores.\n2. Tareas de enrutamiento por porcentaje, monitorizaciÃ³n y rollback automÃ¡tico.",
            "- [ ] 1. Configurar ingress controller / service mesh para desviar el 5% del trÃ¡fico a la nueva versiÃ³n\n- [ ] 2. Monitorizar mÃ©tricas clave en tiempo real: tasa de errores 5xx, latencia y CPU\n- [ ] 3. Automatizar promociÃ³n al 100% si las mÃ©tricas son estables o rollback instantÃ¡neo ante anomalÃ­as",
            "Plan de despliegues canary configurado en tareas.",
            '/task_done "1"'
        ),
        (
            "DiseÃ±a un esquema de particionamiento de tablas (Table Partitioning) para manejar millones de registros histÃ³ricos.",
            "1. Escalabilidad horizontal de tablas relacionales masivas.\n2. Tareas de particionamiento declarativo por rango de fechas y mantenimiento.",
            "- [ ] 1. Definir particionamiento declarativo en PostgreSQL por rango mensual en `created_at`\n- [ ] 2. Crear script automatizado para precrear particiones futuras y archivar las antiguas\n- [ ] 3. Verificar optimizaciÃ³n de consultas confirmando partition pruning en `EXPLAIN`",
            "Plan de particionamiento de tablas registrado en lista de tareas.",
            "/task_list"
        ),
        (
            "DiseÃ±a una polÃ­tica de gestiÃ³n y rotaciÃ³n de certificados SSL/TLS con Let's Encrypt y Certbot.",
            "1. Seguridad en comunicaciones web y renovaciÃ³n desatendida.\n2. Tareas de validaciÃ³n DNS/HTTP, automatizaciÃ³n cron y recarga de servidores.",
            "- [ ] 1. Instalar Certbot con plugin para validaciÃ³n automÃ¡tica mediante API de DNS\n- [ ] 2. Configurar cronjob semanal para renovaciÃ³n automÃ¡tica de certificados prÃ³ximos a expirar\n- [ ] 3. AÃ±adir hook de recarga automÃ¡tica (`deploy-hook`) para Nginx / Traefik tras renovaciÃ³n",
            "Plan de gestiÃ³n automatizada de certificados TLS registrado.",
            '/task_done "1"'
        ),
        (
            "DiseÃ±a un catÃ¡logo de servicios para registrar endpoints, propietarios y contratos de APIs en el ecosistema de la empresa.",
            "1. Gobernanza de servicios y reducciÃ³n de fricciÃ³n entre equipos.\n2. Tareas de recolecciÃ³n de especificaciones, portal y automatizaciÃ³n.",
            "- [ ] 1. Adoptar Backstage de Spotify o portal interno como plataforma central de catÃ¡logo\n- [ ] 2. Definir descriptor `catalog-info.yaml` en la raÃ­z de cada repositorio de servicio\n- [ ] 3. Automatizar sincronizaciÃ³n de documentaciÃ³n OpenAPI y contactos de guardia",
            "Plan de catÃ¡logo de servicios empresariales configurado en tareas.",
            "/task_list"
        ),
        (
            "DiseÃ±a un protocolo de pruebas de caos (Chaos Engineering) para verificar la auto-recuperaciÃ³n de nuestros servicios.",
            "1. VerificaciÃ³n empÃ­rica de resiliencia en sistemas distribuidos.\n2. Tareas de hipÃ³tesis, inyecciÃ³n controlada de fallos y observabilidad.",
            "- [ ] 1. Formular hipÃ³tesis de estado estacionario (Steady State) en mÃ©tricas de negocio\n- [ ] 2. Inyectar fallos controlados en entorno staging: caÃ­da de nodos, latencia de red y pÃ©rdida de paquetes\n- [ ] 3. Verificar que los circuit breakers y rÃ©plicas conmuten sin impacto en el usuario",
            "Plan de Chaos Engineering registrado en lista de tareas.",
            '/task_done "1"'
        ),
        (
            "Planifica la implementaciÃ³n de soporte HTTP/3 (QUIC) en nuestros proxies inversos para optimizar la navegaciÃ³n mÃ³vil.",
            "1. OptimizaciÃ³n de capa de transporte para redes con fluctuaciÃ³n y pÃ©rdida de paquetes.\n2. Tareas de compilaciÃ³n con soporte quiche, cabeceras Alt-Svc y fallback UDP.",
            "- [ ] 1. Habilitar mÃ³dulo QUIC / HTTP/3 en servidores Nginx / Caddy sobre puerto 443 UDP\n- [ ] 2. Inyectar cabecera `Alt-Svc` para notificar a clientes navegadores la disponibilidad de HTTP/3\n- [ ] 3. Verificar enrutamiento y apertura de puertos UDP en firewalls perimetrales",
            "Plan de adopciÃ³n de HTTP/3 configurado en tareas.",
            "/task_list"
        ),
        (
            "DiseÃ±a una estrategia para migrar de una arquitectura sÃ­ncrona a un modelo CQRS (Command Query Responsibility Segregation).",
            "1. Desacoplamiento de operaciones de lectura y escritura para alta escala.\n2. Tareas cognitivas de separaciÃ³n de modelos, sincronizaciÃ³n de proyecciones y consistencia eventual.",
            "- [ ] 1. Separar modelos de comandos (mutaciones en PostgreSQL) de modelos de consulta\n- [ ] 2. Configurar almacÃ©n optimizado de lectura (Elasticsearch / Redis) alimentado por eventos\n- [ ] 3. Gestionar consistencia eventual y asegurar idempotencia en la proyecciÃ³n de datos",
            "Plan de arquitectura CQRS establecido en lista de tareas.",
            '/task_add "Definir mecanismo de reconciliaciÃ³n en caso de desincronizaciÃ³n de proyecciones"'
        ),
    ]

    for q, thought, tasks, resp, cmds in tasks_data:
        ex.append(_conv(
            _sys(),
            _human(q),
            _gpt(thought, resp, commands=cmds, tasks=tasks)
        ))

    # Multi-source: conversiones de agente remitente
    _ms_apply(ex, [
        (50, 'Tarea multi-etapa delegada. Requiero descomposicion con <tasks>.'),
        (51, 'Tarea de migracion delegada. Plan multi-paso.'),
        (53, 'Tarea de reorganizacion wiki delegada.'),
        (55, 'Tarea de diseno de estrategia de tests delegada.'),
        (56, 'Tarea de auditoria CI/CD delegada.'),
        (58, 'Tarea de investigacion arquitectonica delegada.'),
        (61, 'Tarea de analisis de rendimiento delegada.'),
        (63, 'Tarea de revision de contratos API delegada.'),
        (65, 'Tarea de consolidacion de conceptos delegada.'),
        (67, 'Tarea de planificacion de sprint delegada.'),
        (70, 'Tarea de diseno de modelo delegada.'),
        (73, 'Tarea de optimizacion de indices delegada.'),
        (76, 'Tarea de revision de seguridad delegada.'),
        (79, 'Tarea de documentacion tecnica delegada.'),
        (82, 'Tarea de analisis de logs delegada.'),
        (85, 'Tarea de integracion de sistemas delegada.'),
        (88, 'Tarea de refactorizacion delegada.'),
    ])
    return ex


def main():
    root = Path(__file__).resolve().parent
    out_dir = root / "data" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "dataset_ft5_tasklist.jsonl"

    examples = create_examples()
    with open(out_file, "w", encoding="utf-8") as f:
        for item in examples:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"[OK] Dataset FT5 generado: {out_file} ({len(examples)} ejemplos)")


if __name__ == "__main__":
    main()

