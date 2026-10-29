"""Generador de Dataset FT3: Patrones de Guardado Correcto y Correccion de Fallos.

Entrena al modelo en:
  A - No emitir frases de intencion en <response> al usar /save o /edit
  B - No mezclar XML de relaciones en texto narrativo libre
  C - No usar /search cuando el concepto ya esta en la MEMORIA WIKI inyectada
  D - Recuperarse correctamente tras rechazo del sistema validador
  E - Usar /read (no /search) para profundizar en conceptos conocidos por nombre
  F - No usar /save en respuestas a consultas puramente informativas
  G - Ciclo /search -> /edit con definicion estructurada inmediata
  H - Casos edge adicionales

Formato: ShareGPT. Integracion: build_cumulative_dataset.py como FT3.
"""
import json
from pathlib import Path

OUTPUT_DIR = Path("data/exports")
OUTPUT_FILE = OUTPUT_DIR / "dataset_ft3_structured_saves.jsonl"

_WIKI_H = "--- MEMORIA WIKI: INFORMACION RECUPERADA INICIALMENTE ---"
_WIKI_F = "--- FIN DE MEMORIA WIKI ---"


def _sys(extra=""):
    v = "<MODO: AGENTE>"
    if extra:
        v += "\n" + extra
    return {"from": "system", "value": v}


def _wiki(content):
    return {"from": "system", "value": f"<MODO: AGENTE>\n{_WIKI_H}\n{content}\n{_WIKI_F}"}


def _human(text):
    return {"from": "human", "value": text}


def _gpt(thought, response, commands=""):
    return {"from": "gpt", "value": "\n".join([
        f"<thought>\n{thought.strip()}\n</thought>",
        f"<response>\n{response.strip()}\n</response>",
        f"<commands>\n{commands.strip()}\n</commands>",
    ])}


def _conv(*turns):
    return {"conversations": list(turns)}


def create_examples():
    ex = []

    # =====================================================================
    # BLOQUE A: NUNCA frases de intencion ("Voy a...") en /save o /edit
    # =====================================================================

    ex.append(_conv(
        _sys(),
        _human("Registra el concepto de 'Inteligencia Artificial' en la wiki."),
        _gpt(
            thought=(
                "1. El usuario pide EXPLICITAMENTE registrar 'Inteligencia Artificial'.\n"
                "2. Redacto la definicion tecnica completa AHORA dentro de <definition>.\n"
                "3. PROHIBIDO frases como 'Voy a registrar...' en <response>.\n"
                "4. /save con contenido estructurado completo."
            ),
            response=(
                "<definition>\n"
                "La Inteligencia Artificial (IA) es la disciplina de la informatica que desarrolla\n"
                "sistemas capaces de realizar tareas que normalmente requieren inteligencia humana:\n"
                "razonamiento, aprendizaje, percepcion y toma de decisiones.\n"
                "</definition>\n"
                "<sections>\n"
                "  <section name=\"Ramas principales\">Machine Learning, Deep Learning,\n"
                "  Procesamiento del Lenguaje Natural (NLP), Vision por Computador.</section>\n"
                "</sections>\n"
                "<relations>\n"
                "  <relation type=\"relates_to\" target=\"Machine Learning\">El ML es la tecnica\n"
                "  mas usada para implementar IA.</relation>\n"
                "</relations>"
            ),
            commands='/save "Inteligencia Artificial"',
        )
    ))

    ex.append(_conv(
        _sys(),
        _human("Actualiza la pagina de 'Python' anadiendo que es interpretado y de tipado dinamico."),
        _gpt(
            thought=(
                "1. El usuario pide actualizar 'Python' con datos nuevos.\n"
                "2. Escribo la definicion completa en <definition> INMEDIATAMENTE.\n"
                "3. Prohibido 'Voy a actualizar...', 'Procedo a...' en <response>.\n"
                "4. Uso /edit."
            ),
            response=(
                "<definition>\n"
                "Python es un lenguaje de programacion de alto nivel, interpretado, de tipado\n"
                "dinamico y proposito general, disenado con enfasis en la legibilidad del codigo.\n"
                "Creado por Guido van Rossum, lanzado en 1991.\n"
                "</definition>\n"
                "<sections>\n"
                "  <section name=\"Caracteristicas clave\">Interpretado (sin compilacion previa),\n"
                "  tipado dinamico (tipos inferidos en tiempo de ejecucion), multiplataforma.</section>\n"
                "</sections>\n"
                "<relations>\n"
                "  <relation type=\"relates_to\" target=\"Machine Learning\">Lenguaje dominante\n"
                "  en proyectos de ML y ciencia de datos.</relation>\n"
                "</relations>"
            ),
            commands='/edit "Python"',
        )
    ))

    ex.append(_conv(
        _sys(),
        _human("Scrum tiene tres pilares: transparencia, inspeccion y adaptacion. Guardalo."),
        _gpt(
            thought=(
                "1. El usuario aporta datos concretos y pide explicitamente guardarlos.\n"
                "2. Redacto la definicion completa en <definition> + <sections>.\n"
                "3. El <response> contiene SOLO el XML estructurado, sin frases de anuncio."
            ),
            response=(
                "<definition>\n"
                "Scrum es un marco de trabajo agil iterativo sustentado en tres pilares:\n"
                "transparencia, inspeccion y adaptacion.\n"
                "</definition>\n"
                "<sections>\n"
                "  <section name=\"Tres pilares\">1. Transparencia: visibilidad total del proceso.\n"
                "2. Inspeccion: revision continua del progreso y artefactos.\n"
                "3. Adaptacion: ajuste ante desviaciones detectadas.</section>\n"
                "</sections>\n"
                "<relations>\n"
                "  <relation type=\"is_a\" target=\"Metodologia Agil\">Marco agil mas extendido.</relation>\n"
                "  <relation type=\"part_of\" target=\"Gestion de Proyectos\">Enfoque iterativo de PM.</relation>\n"
                "</relations>"
            ),
            commands='/save "Scrum"',
        )
    ))

    # =====================================================================
    # BLOQUE B: NO mezclar XML en texto narrativo
    # =====================================================================

    ex.append(_conv(
        _wiki("[[Scrum]]: Marco agil. Pilares: transparencia, inspeccion, adaptacion."),
        _human("Explicame los pilares de Scrum."),
        _gpt(
            thought=(
                "1. Consulta informativa sobre Scrum.\n"
                "2. La informacion ya esta en MEMORIA WIKI bajo [[Scrum]].\n"
                "3. Respondo en lenguaje natural, SIN etiquetas XML en el texto.\n"
                "4. PROHIBIDO <relation...> en el texto de respuesta.\n"
                "5. PROHIBIDO /save — es consulta, no aportacion nueva."
            ),
            response=(
                "El [[Scrum]] se sustenta en tres pilares fundamentales:\n\n"
                "1. **Transparencia**: todos los aspectos del proceso son visibles.\n"
                "2. **Inspeccion**: los artefactos y el progreso se examinan con frecuencia.\n"
                "3. **Adaptacion**: el proceso se ajusta cuando hay desviaciones.\n\n"
                "Quieres que profundice en alguno de ellos?"
            ),
            commands="",
        )
    ))

    ex.append(_conv(
        _sys(),
        _human("Registra 'Gestion de Empresas'. Es un campo que usa Gestion de Proyectos como herramienta."),
        _gpt(
            thought=(
                "1. El usuario pide registrar 'Gestion de Empresas'.\n"
                "2. La relacion va en el bloque <relations>, NO incrustada en el texto.\n"
                "3. PROHIBIDO escribir '<relation target=...>' dentro del texto narrativo."
            ),
            response=(
                "<definition>\n"
                "La Gestion de Empresas es el conjunto de disciplinas orientadas a planificar,\n"
                "organizar, dirigir y controlar los recursos de una organizacion para alcanzar\n"
                "objetivos estrategicos de forma eficiente.\n"
                "</definition>\n"
                "<relations>\n"
                "  <relation type=\"relates_to\" target=\"Gestion de Proyectos\">La gestion de\n"
                "  proyectos es una herramienta operativa clave dentro de la gestion empresarial.</relation>\n"
                "  <relation type=\"relates_to\" target=\"Estrategia Empresarial\">Define el rumbo\n"
                "  y los objetivos de largo plazo de la organizacion.</relation>\n"
                "</relations>"
            ),
            commands='/save "Gestion de Empresas"',
        )
    ))

    # =====================================================================
    # BLOQUE C: NO /search cuando la info ya esta en la memoria inyectada
    # =====================================================================

    ex.append(_conv(
        _wiki(
            "[[Kanban]]: Metodo de gestion visual del flujo de trabajo basado en tableros.\n"
            "Practicas: WIP limits, visualizacion, metricas Lead Time y Cycle Time.\n"
            "Relaciones: relates_to Scrum, part_of Metodologia Agil."
        ),
        _human("Que es Kanban y como funciona?"),
        _gpt(
            thought=(
                "1. El usuario pregunta por Kanban.\n"
                "2. La MEMORIA WIKI ya contiene [[Kanban]] con sus practicas completas.\n"
                "3. TERMINANTEMENTE PROHIBIDO usar /search sobre conceptos ya en la memoria.\n"
                "4. Respondo directamente sintetizando el conocimiento de la wiki."
            ),
            response=(
                "[[Kanban]] es un metodo de gestion visual del flujo de trabajo. Funciona mediante\n"
                "tableros donde cada columna representa una fase del proceso.\n\n"
                "Sus practicas fundamentales:\n"
                "- **WIP Limits**: limitar el trabajo en curso para evitar saturacion.\n"
                "- **Visualizacion del flujo**: hacer visible el estado de cada tarea.\n"
                "- **Metricas**: Lead Time (tiempo total) y Cycle Time (tiempo activo).\n\n"
                "A diferencia de Scrum, el flujo es continuo sin iteraciones fijas."
            ),
            commands="",
        )
    ))

    ex.append(_conv(
        _wiki("[[Docker]]: Plataforma de contenedores para empaquetar aplicaciones con sus dependencias."),
        _human("Cual es la diferencia entre Docker y Kubernetes?"),
        _gpt(
            thought=(
                "1. El usuario pregunta por Docker y Kubernetes.\n"
                "2. La memoria wiki tiene [[Docker]] pero NO Kubernetes.\n"
                "3. Solo busco lo que NO esta en memoria: /search 'Kubernetes'.\n"
                "4. NO repito la busqueda de Docker — ya lo tengo en el contexto."
            ),
            response="Tengo informacion sobre [[Docker]] en memoria. Busco Kubernetes para la comparativa.",
            commands='/search "Kubernetes"',
        )
    ))

    ex.append(_conv(
        _wiki(
            "[[Metodologia Agil]]: Enfoque iterativo y flexible.\n"
            "  Marcos: Scrum (sprints 1-4 semanas), Kanban (flujo continuo).\n"
            "  Principios: entrega continua, adaptacion al cambio, colaboracion."
        ),
        _human("Cuales son los marcos agiles mas comunes?"),
        _gpt(
            thought=(
                "1. Consulta sobre marcos agiles.\n"
                "2. La memoria wiki tiene [[Metodologia Agil]] con Scrum y Kanban listados.\n"
                "3. PROHIBIDO /search — tengo la informacion completa con sus marcos.\n"
                "4. Respondo directamente."
            ),
            response=(
                "Los marcos de [[Metodologia Agil]] mas extendidos son:\n\n"
                "- **Scrum**: sprints de 1 a 4 semanas con roles fijos.\n"
                "- **Kanban**: gestion visual continua sin iteraciones fijas, con WIP limits.\n\n"
                "Ambos comparten los principios de entrega continua y adaptacion al cambio."
            ),
            commands="",
        )
    ))

    # =====================================================================
    # BLOQUE D: RECUPERACION CORRECTA TRAS RECHAZO DEL SISTEMA VALIDADOR
    # =====================================================================

    ex.append(_conv(
        _sys(),
        _human("Guarda el concepto de 'DevOps' en la wiki."),
        _gpt(
            thought=(
                "1. El usuario pide guardar DevOps.\n"
                "2. Redacto la definicion tecnica completa en <definition> DIRECTAMENTE.\n"
                "3. NUNCA frases de intencion en <response>."
            ),
            response=(
                "<definition>\n"
                "DevOps es un conjunto de practicas culturales y tecnicas que unifican el desarrollo\n"
                "de software (Dev) y las operaciones de infraestructura (Ops), con el objetivo de\n"
                "acortar el ciclo de vida del desarrollo y entregar software de alta calidad continuamente.\n"
                "</definition>\n"
                "<sections>\n"
                "  <section name=\"Pilares\">Integracion Continua (CI), Entrega Continua (CD),\n"
                "  Infraestructura como Codigo (IaC), monitorizacion y observabilidad.</section>\n"
                "</sections>\n"
                "<relations>\n"
                "  <relation type=\"relates_to\" target=\"CI/CD\">CI/CD es la practica tecnica\n"
                "  central de DevOps.</relation>\n"
                "  <relation type=\"relates_to\" target=\"Metodologia Agil\">DevOps complementa las\n"
                "  metodologias agiles extendiendo la entrega hasta produccion.</relation>\n"
                "</relations>"
            ),
            commands='/save "DevOps"',
        )
    ))

    # D2: ciclo rechazo -> correccion para /save
    ex.append(_conv(
        _sys(),
        _human("Crea el concepto de 'Microservicios' en la wiki."),
        _gpt(
            thought=(
                "1. El usuario pide crear 'Microservicios'.\n"
                "2. Redacto la definicion tecnica completa."
            ),
            response="Voy a registrar la arquitectura de Microservicios en la wiki.",
            commands='/save "Microservicios"',
        ),
        _human(
            "[RESULTADO COMANDO /save \"Microservicios\"]\n"
            "Error: No se ha guardado el concepto '[[Microservicios]]'. El contenido en <response>\n"
            "parece ser una frase transitoria (\"Voy a registrar...\") en lugar de una definicion real.\n"
            "Instruccion: Proporciona el contenido estructurado completo dentro de <definition>."
        ),
        _gpt(
            thought=(
                "1. El sistema rechazo /save porque emiti 'Voy a registrar...' — frase de intencion.\n"
                "2. Corrijo INMEDIATAMENTE: definicion tecnica completa en <definition>.\n"
                "3. Vuelvo a emitir /save con el contenido valido."
            ),
            response=(
                "<definition>\n"
                "La arquitectura de Microservicios estructura una aplicacion como una coleccion de\n"
                "servicios pequenos, autonomos y desplegables de forma independiente, cada uno\n"
                "responsable de una capacidad de negocio especifica, comunicandose mediante APIs.\n"
                "</definition>\n"
                "<sections>\n"
                "  <section name=\"Ventajas\">Escalabilidad independiente, despliegue continuo sin\n"
                "  afectar al sistema completo, tolerancia a fallos aislada.</section>\n"
                "  <section name=\"Desventajas\">Complejidad operativa elevada, latencia entre\n"
                "  servicios, necesidad de orquestacion como Kubernetes.</section>\n"
                "</sections>\n"
                "<relations>\n"
                "  <relation type=\"relates_to\" target=\"Kubernetes\">Plataforma de orquestacion\n"
                "  estandar para microservicios.</relation>\n"
                "  <relation type=\"relates_to\" target=\"DevOps\">Los microservicios se gestionan\n"
                "  mejor con practicas DevOps y CI/CD.</relation>\n"
                "</relations>"
            ),
            commands='/save "Microservicios"',
        )
    ))

    # D3: ciclo rechazo -> correccion para /edit
    ex.append(_conv(
        _sys(),
        _human("Actualiza 'Gestion de Empresas' anadiendo la relacion con Recursos Humanos."),
        _gpt(
            thought=(
                "1. Actualizacion de 'Gestion de Empresas' con nueva relacion.\n"
                "2. Uso /edit con la definicion completa."
            ),
            response="Voy a profundizar en Gestion de Empresas para anadir la relacion con RR.HH.",
            commands='/edit "Gestion de Empresas"',
        ),
        _human(
            "[RESULTADO COMANDO /edit \"Gestion de Empresas\"]\n"
            "Error: Frase de intencion detectada ('Voy a profundizar en...').\n"
            "Proporciona el contenido dentro de <definition>.</definition>"
        ),
        _gpt(
            thought=(
                "1. Sistema rechazo /edit por 'Voy a profundizar...' — frase de intencion.\n"
                "2. Corrijo INMEDIATAMENTE con definicion enciclopedica completa en <definition>.\n"
                "3. Anado la relacion 'relates_to Recursos Humanos' en <relations>."
            ),
            response=(
                "<definition>\n"
                "La Gestion de Empresas es el conjunto de disciplinas orientadas a planificar,\n"
                "organizar, dirigir y controlar los recursos de una organizacion para alcanzar\n"
                "objetivos estrategicos de forma eficiente y sostenible.\n"
                "</definition>\n"
                "<relations>\n"
                "  <relation type=\"relates_to\" target=\"Gestion de Proyectos\">Herramienta\n"
                "  operativa dentro de la gestion empresarial.</relation>\n"
                "  <relation type=\"relates_to\" target=\"Recursos Humanos\">La gestion de personas\n"
                "  es una dimension critica de toda empresa.</relation>\n"
                "  <relation type=\"relates_to\" target=\"Estrategia Empresarial\">Define el rumbo\n"
                "  y los objetivos de largo plazo.</relation>\n"
                "</relations>"
            ),
            commands='/edit "Gestion de Empresas"',
        )
    ))

    # =====================================================================
    # BLOQUE E: /read PARA PROFUNDIZAR (no /search cuando conoces el nombre)
    # =====================================================================

    ex.append(_conv(
        _wiki(
            "[[Arquitectura Hexagonal]]: Patron de puertos y adaptadores que aisla la logica de dominio.\n"
            "Relacionado con: DDD, Clean Architecture."
        ),
        _human("Necesito los detalles completos de la Arquitectura Hexagonal: capas, reglas, dependencias."),
        _gpt(
            thought=(
                "1. Tengo [[Arquitectura Hexagonal]] en memoria pero solo resumida.\n"
                "2. El usuario pide detalles COMPLETOS: capas, reglas.\n"
                "3. Uso /read — ya se el nombre exacto, no necesito /search.\n"
                "4. /read devuelve el contenido completo incluyendo todas las secciones."
            ),
            response="Tengo el concepto registrado. Leo su contenido completo para los detalles.",
            commands='/read "Arquitectura Hexagonal"',
        )
    ))

    ex.append(_conv(
        _sys(),
        _human("Como se relacionan DDD y la Arquitectura Hexagonal?"),
        _gpt(
            thought=(
                "1. Pregunta sobre relacion entre DDD y Arquitectura Hexagonal.\n"
                "2. No tengo ninguno en memoria — busco ambos."
            ),
            response="Buscando ambos conceptos para darte una respuesta precisa.",
            commands='/search "Domain Driven Design"\n/search "Arquitectura Hexagonal"',
        ),
        _human(
            "[RESULTADO COMANDO /search \"Domain Driven Design\"]\n"
            "[[Domain Driven Design (DDD)]]: Metodologia de diseno centrada en el modelo de dominio.\n"
            "Creada por Eric Evans.\n\n"
            "[RESULTADO COMANDO /search \"Arquitectura Hexagonal\"]\n"
            "[[Arquitectura Hexagonal]]: Patron de puertos y adaptadores que aisla la logica de dominio.\n"
            "Creada por Alistair Cockburn."
        ),
        _gpt(
            thought=(
                "1. Tengo resultados para ambos conceptos.\n"
                "2. Informacion suficiente para explicar la relacion.\n"
                "3. Respondo directamente. PROHIBIDO /save — es consulta informativa."
            ),
            response=(
                "[[Domain Driven Design (DDD)]] y [[Arquitectura Hexagonal]] son complementarios:\n\n"
                "- **DDD** proporciona el *que*: como modelar el dominio del negocio.\n"
                "- **Arquitectura Hexagonal** proporciona el *como estructurarlo*: aisla ese dominio\n"
                "  de las dependencias externas mediante puertos y adaptadores.\n\n"
                "En la practica, DDD define el corazon del sistema y la Arquitectura Hexagonal\n"
                "garantiza que no dependa de detalles de infraestructura."
            ),
            commands="",
        )
    ))

    # =====================================================================
    # BLOQUE F: PROHIBICION DE /save EN CONSULTAS INFORMATIVAS
    # =====================================================================

    ex.append(_conv(
        _wiki("[[Fotosintesis]]: Proceso por el que las plantas convierten luz solar en glucosa."),
        _human("Que es la fotosintesis?"),
        _gpt(
            thought=(
                "1. Consulta informativa sobre la fotosintesis.\n"
                "2. Informacion completa en memoria wiki bajo [[Fotosintesis]].\n"
                "3. TERMINANTEMENTE PROHIBIDO /save en consultas informativas.\n"
                "4. Respondo directamente, <commands> vacio."
            ),
            response=(
                "La [[Fotosintesis]] es el proceso mediante el cual las plantas convierten la energia\n"
                "de la luz solar en glucosa, utilizando CO2 y agua.\n\n"
                "Reaccion simplificada: **6CO2 + 6H2O + luz -> C6H12O6 + 6O2**\n\n"
                "Es la base de casi toda la cadena alimentaria en la Tierra."
            ),
            commands="",
        )
    ))

    ex.append(_conv(
        _sys(),
        _human("Explicame que es el Principio de Responsabilidad Unica (SRP)."),
        _gpt(
            thought=(
                "1. El usuario pide una explicacion — consulta informativa.\n"
                "2. No esta en memoria pero conozco el concepto.\n"
                "3. PROHIBIDO /save: el usuario no pidio registrar nada.\n"
                "4. Solo respondo de forma clara y asertiva."
            ),
            response=(
                "El **Principio de Responsabilidad Unica (SRP)** establece que una clase debe tener\n"
                "**una unica razon para cambiar**.\n\n"
                "**Ejemplo**: Una clase `Factura` no deberia calcular el total, formatear el PDF y\n"
                "enviar el email a la vez. Cada responsabilidad va en su propia clase.\n\n"
                "Seguir el SRP hace el codigo mas mantenible y testeable. Quieres que lo registre?"
            ),
            commands="",
        )
    ))

    # =====================================================================
    # BLOQUE G: CICLO /search -> /edit CON DEFINICION ESTRUCTURADA INMEDIATA
    # =====================================================================

    ex.append(_conv(
        _sys(),
        _human("Anade al concepto de 'Blockchain' que es inmutable y descentralizado."),
        _gpt(
            thought=(
                "1. El usuario quiere anadir info a 'Blockchain' — no esta en memoria.\n"
                "2. Busco primero para no perder la definicion existente."
            ),
            response="Buscando el concepto 'Blockchain' antes de actualizarlo.",
            commands='/search "Blockchain"',
        ),
        _human(
            "[RESULTADO COMANDO /search \"Blockchain\"]\n"
            "[[Blockchain]]: Tecnologia de registro distribuido (DLT) que almacena transacciones\n"
            "en bloques enlazados criptograficamente. Usada en criptomonedas como Bitcoin."
        ),
        _gpt(
            thought=(
                "1. Tengo la definicion actual de [[Blockchain]].\n"
                "2. El usuario quiere anadir: inmutable y descentralizado.\n"
                "3. Redacto la definicion enriquecida en <definition>.\n"
                "4. PROHIBIDO frases de intencion. El <response> es el contenido estructurado directo."
            ),
            response=(
                "<definition>\n"
                "Blockchain es una tecnologia de registro distribuido (DLT) que almacena datos en\n"
                "bloques enlazados criptograficamente. Sus propiedades clave son la **inmutabilidad**\n"
                "(los datos no pueden modificarse retroactivamente) y la **descentralizacion**\n"
                "(sin autoridad central que controle el registro).\n"
                "</definition>\n"
                "<relations>\n"
                "  <relation type=\"relates_to\" target=\"Bitcoin\">Bitcoin fue la primera aplicacion\n"
                "  masiva de blockchain.</relation>\n"
                "  <relation type=\"relates_to\" target=\"Smart Contracts\">Los contratos inteligentes\n"
                "  se ejecutan sobre blockchains programables como Ethereum.</relation>\n"
                "</relations>"
            ),
            commands='/edit "Blockchain"',
        )
    ))

    # =====================================================================
    # BLOQUE H: CASOS EDGE ADICIONALES
    # =====================================================================

    # H1: busqueda -> respuesta sin /save (no hay datos nuevos)
    ex.append(_conv(
        _sys(),
        _human("Tienes informacion sobre Git en la wiki?"),
        _gpt(
            thought=(
                "1. Consulta sobre Git — no esta en memoria.\n"
                "2. Busco antes de responder."
            ),
            response="Buscando en la wiki que tenemos sobre Git.",
            commands='/search "Git"',
        ),
        _human(
            "[RESULTADO COMANDO /search \"Git\"]\n"
            "[[Git]]: Sistema de control de versiones distribuido. Creado por Linus Torvalds en 2005.\n"
            "Comandos clave: commit, push, pull, branch, merge."
        ),
        _gpt(
            thought=(
                "1. La busqueda devolvio [[Git]] con informacion completa.\n"
                "2. El usuario solo pregunto si tenia info — no pidio guardar nada nuevo.\n"
                "3. PROHIBIDO /save — no hay datos nuevos que registrar."
            ),
            response=(
                "Si, tengo [[Git]] registrado. Es el sistema de control de versiones distribuido\n"
                "creado por Linus Torvalds en 2005, con comandos: commit, push, pull, branch y merge.\n\n"
                "Quieres que anada mas informacion?"
            ),
            commands="",
        )
    ))

    # H2: datos nuevos del usuario sobre concepto existente -> /edit justificado
    ex.append(_conv(
        _wiki("[[Git]]: Sistema de control de versiones distribuido. Creado por Linus Torvalds en 2005."),
        _human("Anade que Git usa ramas (branching) como flujo principal y que GitHub es su hosting mas popular."),
        _gpt(
            thought=(
                "1. El usuario aporta datos nuevos sobre Git: branching y GitHub.\n"
                "2. Es una peticion explicita de actualizacion — /edit justificado.\n"
                "3. Redacto la definicion enriquecida con la info existente mas la nueva.\n"
                "4. Contenido estructurado directo en <definition>, sin frases de anuncio."
            ),
            response=(
                "<definition>\n"
                "Git es un sistema de control de versiones distribuido (DVCS) creado por Linus Torvalds\n"
                "en 2005. Usa el **modelo de ramas (branching)** como flujo de trabajo principal,\n"
                "permitiendo desarrollar funcionalidades de forma aislada.\n"
                "</definition>\n"
                "<sections>\n"
                "  <section name=\"Flujo de trabajo\">El branching model permite ramas independientes\n"
                "  por feature, bugfix o release. Flujos comunes: Git Flow y GitHub Flow.</section>\n"
                "</sections>\n"
                "<relations>\n"
                "  <relation type=\"relates_to\" target=\"GitHub\">GitHub es la plataforma de hosting\n"
                "  mas popular para repositorios Git.</relation>\n"
                "  <relation type=\"relates_to\" target=\"CI/CD\">Git es el punto de partida de\n"
                "  cualquier pipeline de integracion continua.</relation>\n"
                "</relations>"
            ),
            commands='/edit "Git"',
        )
    ))

    # H3: /read vs /search — usar /read cuando se conoce el nombre exacto
    ex.append(_conv(
        _wiki(
            "[[Clean Architecture]]: Patron que separa el sistema en capas concentricas con\n"
            "dependencias hacia el interior (dominio)."
        ),
        _human("Necesito los detalles completos de Clean Architecture: capas, reglas y dependencias."),
        _gpt(
            thought=(
                "1. Tengo [[Clean Architecture]] pero solo resumida en memoria.\n"
                "2. El usuario pide detalles COMPLETOS.\n"
                "3. Uso /read — ya se el nombre exacto del concepto, no necesito /search."
            ),
            response="Leyendo el contenido completo de Clean Architecture para los detalles.",
            commands='/read "Clean Architecture"',
        )
    ))

    # H4: multiples conceptos nuevos en un turno — guardar todos
    ex.append(_conv(
        _sys(),
        _human(
            "Registra: TCP/IP es el protocolo base de internet. "
            "HTTP es el protocolo de hipertexto que usa TCP/IP."
        ),
        _gpt(
            thought=(
                "1. El usuario aporta dos conceptos nuevos relacionados: TCP/IP y HTTP.\n"
                "2. Guardo ambos con /save en el mismo turno.\n"
                "3. Definiciones estructuradas completas para cada uno en <response>."
            ),
            response=(
                "**TCP/IP**\n"
                "<definition>\n"
                "TCP/IP es el conjunto de protocolos de comunicacion que forma la base de Internet.\n"
                "TCP garantiza la entrega ordenada de paquetes; IP gestiona el direccionamiento.\n"
                "</definition>\n\n"
                "**HTTP**\n"
                "<definition>\n"
                "HTTP (HyperText Transfer Protocol) es el protocolo de comunicacion sin estado para\n"
                "la transferencia de documentos en la Web. Opera sobre TCP/IP mediante el modelo\n"
                "solicitud-respuesta entre cliente y servidor.\n"
                "</definition>\n"
                "<relations>\n"
                "  <relation type=\"depends_on\" target=\"TCP/IP\">HTTP opera sobre la capa de\n"
                "  transporte que provee TCP/IP.</relation>\n"
                "</relations>"
            ),
            commands='/save "TCP/IP"\n/save "HTTP"',
        )
    ))

    return ex


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    examples = create_examples()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in examples:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    total = len(examples)
    bloques = {"A (no frases intencion /save//edit)": 3, "B (no XML en narrativa)": 2,
               "C (no /search si ya en memoria)": 3, "D (recuperacion tras rechazo)": 3,
               "E (uso correcto /read)": 2, "F (prohibir /save en consultas)": 2,
               "G (ciclo /search->/edit)": 1, "H (casos edge)": 4}
    print(f"[FT3] Dataset: {OUTPUT_FILE} | Total: {total} ejemplos")
    for b, c in bloques.items():
        print(f"  Bloque {b}: {c}")


if __name__ == "__main__":
    main()
