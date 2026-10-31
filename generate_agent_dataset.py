import ft2_extra
import json
from pathlib import Path



# ----------------------------------------------------------------
# Utilidades multi-fuente (añadidas automáticamente)
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
    examples = []

    # =========================================================================
    # MODO 1: <MODO: AGENTE> — Comportamiento ReAct (Reasoning + Acting)
    # Cada respuesta del agente sigue el patrón:
    #   <thought> razonamiento paso a paso </thought>
    #   <response> texto para el usuario / contenido del concepto </response>
    #   <commands> comandos a ejecutar (vacío si respuesta final) </commands>
    # =========================================================================

    # 1. Saludo inicial — sin comandos necesarios
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Hola, ¿qué puedes hacer?"},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario me saluda y pregunta por mis capacidades.\n"
            "2. No necesito buscar en la wiki para esto.\n"
            "3. Me presentaré y explicaré mis herramientas disponibles.\n"
            "</thought>\n"
            "<response>\n"
            "Hola. Soy un agente de IA con memoria conceptual persistente. Puedo:\n"
            "- Buscar conceptos en mi base de conocimientos (/search)\n"
            "- Guardar o actualizar conceptos con relaciones semánticas (/save, /edit)\n"
            "- Eliminar entradas obsoletas (/delete)\n"
            "- Planificar procesos cognitivos por tareas (/task_add, /task_done, /task_list)\n"
            "- Identificarme como agente en red (/identify)\n"
            "¿De qué quieres hablar o qué información quieres registrar?\n"
            "</response>\n"
            "<commands>\n"
            "</commands>"
        )}
    ]})

    # 2. Búsqueda — necesita herramienta antes de responder
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "¿Qué información tienes sobre el Cambio Climático?"},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario pregunta por 'Cambio Climático'.\n"
            "2. No tengo el contexto en memoria ahora mismo.\n"
            "3. Debo usar /search antes de poder dar una respuesta informada.\n"
            "</thought>\n"
            "<response>\n"
            "Voy a buscar en la wiki qué tenemos registrado sobre el Cambio Climático.\n"
            "</response>\n"
            "<commands>\n"
            "/search \"Cambio Climático\"\n"
            "</commands>"
        )}
    ]})

    # 3. Guardar concepto simple
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Registra que el agua hierve a 100 grados Celsius a nivel del mar."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario me pide registrar un dato concreto: el punto de ebullición del agua.\n"
            "2. Es una instrucción explícita de guardado, usaré /save.\n"
            "3. Formateré el dato dentro de <definition>.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "El punto de ebullición del agua es de 100 grados Celsius (212 °F) a una atmósfera de presión (nivel del mar).\n"
            "</definition>\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Punto de ebullición del agua\"\n"
            "</commands>"
        )}
    ]})

    # 4. Guardar concepto con secciones y relaciones
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Crea una página sobre 'Machine Learning'. Es una rama de la IA. Ejemplos: redes neuronales y árboles de decisión."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Debo crear el concepto 'Machine Learning'.\n"
            "2. Identifico: definición, ejemplos (-> sección), relación 'is_a' con Inteligencia Artificial.\n"
            "3. Usaré el micro-formato XML completo y luego /save.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "Machine Learning (Aprendizaje Automático) es una rama de la Inteligencia Artificial que usa datos y algoritmos para que los sistemas aprendan y mejoren automáticamente.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Algoritmos típicos\">Redes neuronales, árboles de decisión, SVM, regresión lineal.</section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Inteligencia Artificial\">Es una subdisciplina central de la IA.</relation>\n"
            "</relations>\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Machine Learning\"\n"
            "</commands>"
        )}
    ]})

    # 5. Editar un concepto existente
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Añade a la página de React que fue creado por Facebook en 2013."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario quiere actualizar la página de 'React' añadiendo datos históricos.\n"
            "2. Usaré /edit para no borrar lo que ya existe, sino enriquecerlo.\n"
            "3. Añadiré una sección 'Historia'.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "React es una biblioteca de JavaScript de código abierto para construir interfaces de usuario basadas en componentes reutilizables.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Historia\">Fue creado por Facebook (ahora Meta) y publicado como open source en 2013.</section>\n"
            "</sections>\n"
            "</response>\n"
            "<commands>\n"
            "/edit \"React\"\n"
            "</commands>"
        )}
    ]})

    # 6. Eliminar un concepto
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Borra la página 'Test_Concept_123', ya no la necesitamos."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Instrucción de borrado explícita sobre 'Test_Concept_123'.\n"
            "2. Emitiré /delete directamente.\n"
            "</thought>\n"
            "<response>\n"
            "Eliminando el concepto 'Test_Concept_123' de la wiki.\n"
            "</response>\n"
            "<commands>\n"
            "/delete \"Test_Concept_123\"\n"
            "</commands>"
        )}
    ]})

    # 7. Respuesta desde contexto wiki inyectado
    examples.append({"conversations": [
        {"from": "system", "value": (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Gravedad]]: Fuerza física fundamental que atrae los cuerpos con masa entre sí.\n"
            "--- FIN DE MEMORIA WIKI ---"
        )},
        {"from": "human", "value": "¿Qué es la gravedad?"},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario pregunta por la gravedad.\n"
            "2. Mi memoria wiki ya contiene la definición exacta de [[Gravedad]].\n"
            "3. Responderé directamente usando ese contexto, sin necesidad de búsqueda adicional.\n"
            "</thought>\n"
            "<response>\n"
            "La gravedad es una fuerza física fundamental que atrae a los cuerpos que tienen masa entre sí. Está documentada en nuestra memoria bajo el concepto [[Gravedad]].\n"
            "</response>\n"
            "<commands>\n"
            "</commands>"
        )}
    ]})

    # 8. Dato desconocido — guardar proactivamente
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "¿Quién pintó la Mona Lisa?"},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Pregunta sobre la Mona Lisa.\n"
            "2. No está en la memoria wiki.\n"
            "3. Conozco la respuesta por mi entrenamiento base: Leonardo da Vinci.\n"
            "4. Responderé y guardaré el dato proactivamente para enriquecer la wiki.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "La Mona Lisa (también llamada La Gioconda) es una pintura al óleo sobre tabla de álamo realizada por Leonardo da Vinci entre 1503 y 1519. Es considerada la obra de arte más famosa del mundo.\n"
            "</definition>\n"
            "La Mona Lisa fue pintada por Leonardo da Vinci. He aprovechado para guardarlo en la wiki.\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Mona Lisa\"\n"
            "</commands>"
        )}
    ]})

    # 9. Sintetizar resultado de búsqueda (turno multi-ciclo)
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": (
            "[ENTRADA HUMANA]\n"
            "Busca sobre la Antártida.\n\n"
            "[RESULTADO COMANDO /search \"Antártida\"]\n"
            "Resultados de búsqueda:\n"
            "- [[Antártida]]: Continente más austral de la Tierra, contiene el Polo Sur geográfico."
        )},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Tengo el resultado de la búsqueda sobre la Antártida.\n"
            "2. Ya hay información suficiente para responder al usuario.\n"
            "3. Sintetizaré el resultado y dejaré <commands> vacío.\n"
            "</thought>\n"
            "<response>\n"
            "He encontrado la información. La [[Antártida]] es el continente más austral de la Tierra y alberga el Polo Sur geográfico. ¿Quieres que busque más detalles sobre su clima o fauna?\n"
            "</response>\n"
            "<commands>\n"
            "</commands>"
        )}
    ]})

    # 10. Múltiples relaciones semánticas complejas
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Define el Sol. Es una estrella, el centro del sistema solar, y la Tierra orbita a su alrededor."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario aporta una definición del Sol con tres relaciones: is_a (Estrella), part_of (Sistema Solar), relates_to (Tierra).\n"
            "2. Construiré el XML completo con <definition> y <relations>.\n"
            "3. Guardaré con /save.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "El Sol es la estrella en el centro del Sistema Solar. Es una esfera de plasma caliente cuya energía proviene de reacciones de fusión nuclear en su núcleo.\n"
            "</definition>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Estrella\">Es una estrella de tipo espectral G2V (enana amarilla).</relation>\n"
            "  <relation type=\"part_of\" target=\"Sistema Solar\">Es el centro gravitacional del sistema.</relation>\n"
            "  <relation type=\"relates_to\" target=\"Tierra\">La Tierra orbita el Sol y depende de su energía para la vida.</relation>\n"
            "</relations>\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Sol\"\n"
            "</commands>"
        )}
    ]})

    # 11. Búsqueda de múltiples conceptos en paralelo
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "¿Cuál es la diferencia entre Docker y Kubernetes?"},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Se me pide comparar Docker y Kubernetes.\n"
            "2. No tengo el contexto de ninguno de los dos en memoria.\n"
            "3. Buscaré ambos simultáneamente con dos comandos /search para obtener información antes de responder.\n"
            "</thought>\n"
            "<response>\n"
            "Voy a buscar información sobre ambas tecnologías en la wiki para darte una comparativa precisa.\n"
            "</response>\n"
            "<commands>\n"
            "/search \"Docker\"\n"
            "/search \"Kubernetes\"\n"
            "</commands>"
        )}
    ]})

    # 12. Relaciones depends_on y precedes
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Edita 'CI/CD' indicando que depende de Git y que la Integración Continua precede al Despliegue Continuo."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Actualización sobre CI/CD con relaciones específicas de tipo 'depends_on' y 'precedes'.\n"
            "2. Usaré /edit con el XML de relaciones correspondiente.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "CI/CD (Continuous Integration / Continuous Deployment) automatiza las fases de integración, prueba y despliegue del software.\n"
            "</definition>\n"
            "<relations>\n"
            "  <relation type=\"depends_on\" target=\"Git\">El pipeline requiere un sistema de control de versiones como Git.</relation>\n"
            "  <relation type=\"precedes\" target=\"Despliegue Continuo\">La Integración Continua (CI) siempre precede al Despliegue Continuo (CD).</relation>\n"
            "</relations>\n"
            "</response>\n"
            "<commands>\n"
            "/edit \"CI/CD\"\n"
            "</commands>"
        )}
    ]})

    # 13. Corrección del usuario — relación contradicts
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "El patrón Singleton contradice los principios SOLID porque crea acoplamiento global."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario aporta una crítica válida sobre el Patrón Singleton.\n"
            "2. Debo actualizar la definición para reflejar que es considerado un anti-patrón y añadir la relación 'contradicts'.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "El patrón Singleton garantiza que una clase tenga una única instancia. Aunque ofrece acceso global, frecuentemente se considera un anti-patrón por introducir estado global y acoplamiento fuerte.\n"
            "</definition>\n"
            "<relations>\n"
            "  <relation type=\"contradicts\" target=\"Principios SOLID\">Viola el Principio de Responsabilidad Única y dificulta las pruebas unitarias.</relation>\n"
            "</relations>\n"
            "</response>\n"
            "<commands>\n"
            "/edit \"Patrón Singleton\"\n"
            "</commands>"
        )}
    ]})

    # 14. Búsqueda sin resultados — ofrecer crear
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": (
            "[ENTRADA HUMANA]\n"
            "¿Tenemos algo sobre Termodinámica?\n\n"
            "[RESULTADO COMANDO /search \"Termodinámica\"]\n"
            "Sin resultados para la búsqueda 'Termodinámica'."
        )},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. La búsqueda de 'Termodinámica' no devolvió resultados.\n"
            "2. El concepto no está en la wiki aún.\n"
            "3. Informaré al usuario y le ofreceré crear el concepto, sin actuar sin su confirmación.\n"
            "</thought>\n"
            "<response>\n"
            "No tenemos nada sobre Termodinámica en la wiki. Es la rama de la física que estudia el calor, la energía y sus transformaciones. ¿Quieres que la cree?\n"
            "</response>\n"
            "<commands>\n"
            "</commands>"
        )}
    ]})

    # 15. Usuario confirma — crear concepto completo
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Sí, créala con sus cuatro leyes principales."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Confirmación del usuario para crear 'Termodinámica'.\n"
            "2. Generaré la definición y una sección con las cuatro leyes.\n"
            "3. Usaré /save.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "La Termodinámica es la rama de la física que estudia la energía, el calor y sus transformaciones en sistemas macroscópicos.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Las cuatro leyes\">\n"
            "- Ley Cero: Si dos sistemas están en equilibrio térmico con un tercero, están en equilibrio entre sí.\n"
            "- Primera Ley: La energía no se crea ni se destruye, solo se transforma.\n"
            "- Segunda Ley: La entropía de un sistema aislado siempre tiende a aumentar.\n"
            "- Tercera Ley: La entropía de un cristal perfecto a 0 K es cero.\n"
            "  </section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Física\">Es una rama fundamental de la Física Clásica.</relation>\n"
            "</relations>\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Termodinámica\"\n"
            "</commands>"
        )}
    ]})

    # 16. Respuesta asertiva usando contexto inyectado
    examples.append({"conversations": [
        {"from": "system", "value": (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Proyecto Alpha]]: Iniciativa de marketing Q3 2024. Presupuesto: 50k. Estado: Bloqueado.\n"
            "--- FIN DE MEMORIA WIKI ---"
        )},
        {"from": "human", "value": "¿Cómo va el Proyecto Alpha?"},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Pregunta sobre el Proyecto Alpha.\n"
            "2. La memoria wiki ya contiene la información completa y actualizada.\n"
            "3. Responderé directamente sin hacer búsquedas adicionales.\n"
            "</thought>\n"
            "<response>\n"
            "El [[Proyecto Alpha]] es la iniciativa de marketing del Q3 2024. Presupuesto: 50k. Estado actual: Bloqueado. ¿Quieres que actualice su estado o añadamos detalles sobre el bloqueo?\n"
            "</response>\n"
            "<commands>\n"
            "</commands>"
        )}
    ]})

    # 17. Borrado de múltiples conceptos
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Elimina 'Borrador 1' y 'Borrador 2' de la wiki."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Se me pide borrar dos páginas simultáneamente.\n"
            "2. Puedo emitir dos comandos /delete en la misma respuesta.\n"
            "</thought>\n"
            "<response>\n"
            "Eliminando ambos borradores obsoletos de la base de conocimiento.\n"
            "</response>\n"
            "<commands>\n"
            "/delete \"Borrador 1\"\n"
            "/delete \"Borrador 2\"\n"
            "</commands>"
        )}
    ]})

    # 18. Actualización técnica con sección y relación
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Edita TypeScript: usa tipado estático opcional y transpila a JavaScript."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Actualización sobre TypeScript con dos datos clave: tipado estático y transpilación.\n"
            "2. El tipado irá en la definición y la transpilación en una sección de funcionamiento.\n"
            "3. Añadiré relación 'depends_on' con JavaScript.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "TypeScript es un superconjunto de JavaScript desarrollado por Microsoft que añade tipado estático opcional y características de POO.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Funcionamiento\">El código TypeScript se transpila a JavaScript puro antes de ejecutarse en el navegador o Node.js.</section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"depends_on\" target=\"JavaScript\">Es un superconjunto de JS y transpila a JS estándar.</relation>\n"
            "</relations>\n"
            "</response>\n"
            "<commands>\n"
            "/edit \"TypeScript\"\n"
            "</commands>"
        )}
    ]})

    # 19. Consulta ambigua — pedir aclaración
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Guarda eso nuevo que dijimos ayer."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario usa pronombres vagos: 'eso nuevo'.\n"
            "2. No tengo contexto suficiente para saber qué debo guardar.\n"
            "3. No debo actuar a ciegas. Debo pedir aclaración.\n"
            "</thought>\n"
            "<response>\n"
            "No estoy seguro de a qué te refieres con 'eso nuevo'. ¿Puedes indicarme el concepto concreto que quieres que guarde?\n"
            "</response>\n"
            "<commands>\n"
            "</commands>"
        )}
    ]})

    # 20. Mapeo top-down de un dominio
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Vamos a mapear Biología."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario quiere iniciar el mapeo de Biología.\n"
            "2. Debo empezar por el concepto raíz con sus principales ramas.\n"
            "3. Enfoque top-down: crear primero el concepto general.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "La Biología es la ciencia que estudia los seres vivos, su estructura, función, crecimiento, origen, evolución y distribución.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Ramas principales\">Zoología, Botánica, Microbiología, Genética, Ecología, Bioquímica.</section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Ciencia Natural\">Es una de las ciencias naturales fundamentales.</relation>\n"
            "</relations>\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Biología\"\n"
            "</commands>"
        )}
    ]})

    # 21. Proactividad: dato mencionado de pasada
    examples.append({"conversations": [
        {"from": "system", "value": (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Juan Pérez]]: Desarrollador en el equipo Backend.\n"
            "--- FIN DE MEMORIA WIKI ---"
        )},
        {"from": "human", "value": "Hablé con Juan Pérez, que por cierto lo acaban de ascender a Tech Lead, y me dijo que revisáramos la base de datos."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario menciona casualmente que Juan Pérez fue ascendido a Tech Lead.\n"
            "2. Es un cambio sobre un concepto existente. Debo actualizar su ficha proactivamente.\n"
            "3. También debo responder sobre la base de datos que menciona.\n"
            "</thought>\n"
            "<response>\n"
            "Anotado el ascenso de Juan Pérez a Tech Lead — he actualizado su perfil en la wiki. Respecto a la base de datos, ¿qué necesitas revisar?\n"
            "</response>\n"
            "<commands>\n"
            "/edit \"Juan Pérez\"\n"
            "</commands>"
        )}
    ]})

    # 22. Proactividad: hallazgo técnico del usuario
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Descubrí que usando Redis como caché para el endpoint de usuarios, los tiempos bajan un 40%."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario comparte un hallazgo de optimización importante.\n"
            "2. Es un dato técnico valioso que merece ser documentado proactivamente.\n"
            "3. Crearé un concepto llamado 'Optimización Endpoint Usuarios' con la relación a Redis.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "El uso de Redis como capa de caché para el endpoint de usuarios reduce los tiempos de respuesta en aproximadamente un 40%.\n"
            "</definition>\n"
            "<relations>\n"
            "  <relation type=\"relates_to\" target=\"Redis\">Redis actúa como capa de caché que optimiza este endpoint.</relation>\n"
            "</relations>\n"
            "Hallazgo documentado. He creado el concepto 'Optimización Endpoint Usuarios' en la wiki.\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Optimización Endpoint Usuarios\"\n"
            "</commands>"
        )}
    ]})

    # 23. Proactividad: migración de infraestructura
    examples.append({"conversations": [
        {"from": "system", "value": (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Servidor Web]]: Alojado en AWS us-east-1.\n"
            "--- FIN DE MEMORIA WIKI ---"
        )},
        {"from": "human", "value": "Ayer migramos el Servidor Web a eu-west-1 por latencia."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario informa de una migración de infraestructura.\n"
            "2. El concepto [[Servidor Web]] existe pero tiene la región antigua (us-east-1).\n"
            "3. Actualizaré el concepto con /edit para reflejar la nueva región.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "Servidor Web de la aplicación. Alojado en AWS eu-west-1, migrado desde us-east-1 para reducir la latencia.\n"
            "</definition>\n"
            "¡Anotado! He actualizado [[Servidor Web]] a la región eu-west-1.\n"
            "</response>\n"
            "<commands>\n"
            "/edit \"Servidor Web\"\n"
            "</commands>"
        )}
    ]})

    # 24. Proactividad: acrónimo nuevo detectado
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Para el nuevo proyecto vamos a implementar RAG (Retrieval-Augmented Generation)."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario introduce un acrónimo técnico (RAG) con su definición entre paréntesis.\n"
            "2. Es un concepto nuevo que merece ser documentado.\n"
            "3. Crearé el concepto proactivamente.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "RAG (Retrieval-Augmented Generation) es una arquitectura de IA que combina modelos generativos con recuperación de información externa para producir respuestas más precisas y fundamentadas.\n"
            "</definition>\n"
            "<relations>\n"
            "  <relation type=\"is_a\" target=\"Arquitectura de IA\">Es un patrón arquitectónico de sistemas de IA generativa.</relation>\n"
            "</relations>\n"
            "Dado que mencionaste RAG, lo he documentado en la wiki para tenerlo como referencia del proyecto.\n"
            "</response>\n"
            "<commands>\n"
            "/save \"RAG\"\n"
            "</commands>"
        )}
    ]})

    # 25. Proactividad: lista de tareas del sprint
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Para el Sprint 4: login social, refactorizar la BD y actualizar dependencias."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario lista los objetivos del Sprint 4.\n"
            "2. Lo guardaré estructurado como un concepto con sección de tareas.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "Sprint 4: iteración de desarrollo con tres objetivos principales acordados.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Tareas\">\n"
            "- Implementar login social.\n"
            "- Refactorizar la base de datos.\n"
            "- Actualizar dependencias del proyecto.\n"
            "  </section>\n"
            "</sections>\n"
            "He registrado los objetivos del Sprint 4 en la wiki.\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Sprint 4\"\n"
            "</commands>"
        )}
    ]})

    # 26. Documentar dependencia de sistema descubierta por fallo
    examples.append({"conversations": [
        {"from": "system", "value": (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Script de Backup]]: Script bash que comprime /var/www.\n"
            "--- FIN DE MEMORIA WIKI ---"
        )},
        {"from": "human", "value": "El Script de Backup falló porque no había 'tar' instalado en el servidor nuevo."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Un fallo ha revelado una dependencia no documentada: el paquete 'tar'.\n"
            "2. Actualizaré el concepto para registrar formalmente esta dependencia con /edit.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "Script bash que comprime el directorio /var/www para generar copias de seguridad del servidor.\n"
            "</definition>\n"
            "<relations>\n"
            "  <relation type=\"depends_on\" target=\"tar\">Requiere el paquete del sistema 'tar' para ejecutar la compresión.</relation>\n"
            "</relations>\n"
            "He añadido la dependencia de 'tar' al [[Script de Backup]] para que no se repita en futuros servidores.\n"
            "</response>\n"
            "<commands>\n"
            "/edit \"Script de Backup\"\n"
            "</commands>"
        )}
    ]})

    # 27. Enriquecer concepto incompleto detectado en wiki
    examples.append({"conversations": [
        {"from": "system", "value": (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Microservicios]]: Arquitectura de software.\n"
            "--- FIN DE MEMORIA WIKI ---"
        )},
        {"from": "human", "value": "Dime qué tenemos sobre microservicios."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. La wiki tiene 'Microservicios' pero la definición es demasiado escueta.\n"
            "2. Puedo enriquecerla con mi conocimiento y actualizarla antes de responder.\n"
            "3. Usaré /edit para mejorar la entrada.\n"
            "</thought>\n"
            "<response>\n"
            "Nuestra entrada está incompleta. La amplío ahora mismo:\n"
            "<definition>\n"
            "Arquitectura de Microservicios: patrón de diseño donde una aplicación se construye como un conjunto de servicios pequeños, autónomos y débilmente acoplados que se comunican vía APIs.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Ventajas\">Escalabilidad independiente, despliegue continuo, tolerancia a fallos.</section>\n"
            "  <section name=\"Desventajas\">Mayor complejidad operativa, necesidad de orquestación (ej: Kubernetes).</section>\n"
            "</sections>\n"
            "</response>\n"
            "<commands>\n"
            "/edit \"Microservicios\"\n"
            "</commands>"
        )}
    ]})

    # 28. Cambio de herramienta oficial — relación contradicts
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "A partir de ahora usamos Figma para los diseños, en vez de Sketch."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. Cambio de herramienta de diseño: Figma reemplaza a Sketch.\n"
            "2. Crearé el concepto de Figma con una relación 'contradicts' hacia Sketch.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "Figma es la herramienta oficial de diseño y prototipado colaborativo del equipo, accesible desde el navegador.\n"
            "</definition>\n"
            "<relations>\n"
            "  <relation type=\"precedes\" target=\"Desarrollo Frontend\">El diseño en Figma precede a la implementación visual.</relation>\n"
            "  <relation type=\"contradicts\" target=\"Sketch\">Figma ha reemplazado a Sketch como herramienta oficial.</relation>\n"
            "</relations>\n"
            "Entendido. He registrado Figma y documentado el reemplazo de Sketch.\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Figma\"\n"
            "</commands>"
        )}
    ]})

    # 29. Corrección de horario
    examples.append({"conversations": [
        {"from": "system", "value": (
            "<MODO: AGENTE>\n"
            "--- MEMORIA WIKI: INFORMACIÓN RECUPERADA INICIALMENTE ---\n"
            "[[Reunión Semanal]]: Se realiza los jueves a las 10:00 AM.\n"
            "--- FIN DE MEMORIA WIKI ---"
        )},
        {"from": "human", "value": "Las reuniones semanales pasan a ser los viernes a las 12:00."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario corrige directamente el horario de la Reunión Semanal.\n"
            "2. Actualizaré el concepto con la nueva fecha y hora.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "La reunión de sincronización del equipo se realiza todos los viernes a las 12:00 PM.\n"
            "</definition>\n"
            "Actualizado. La [[Reunión Semanal]] ya está registrada los viernes a las 12:00.\n"
            "</response>\n"
            "<commands>\n"
            "/edit \"Reunión Semanal\"\n"
            "</commands>"
        )}
    ]})

    # 30. Documentación técnica de API
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "La API de pagos necesita los campos 'amount', 'currency' y 'user_id'."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario especifica los campos requeridos de la API de pagos.\n"
            "2. Es una especificación técnica importante. La documentaré como concepto.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "Endpoint de la API de Pagos para procesar transacciones.\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Campos requeridos\">\n"
            "- `amount`: Monto de la transacción.\n"
            "- `currency`: Código de moneda (ej: EUR, USD).\n"
            "- `user_id`: Identificador único del usuario.\n"
            "  </section>\n"
            "</sections>\n"
            "He documentado los campos requeridos de la 'API de Pagos' en la wiki.\n"
            "</response>\n"
            "<commands>\n"
            "/save \"API de Pagos\"\n"
            "</commands>"
        )}
    ]})

    # 31. Recuperación tras error de validación en /save (frase de intención rechazada)
    examples.append({"conversations": [
        {"from": "system", "value": "<MODO: AGENTE>"},
        {"from": "human", "value": "Crea el concepto de Kanban en la wiki."},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El usuario pide crear el concepto de Kanban.\n"
            "2. Debo redactar su definición técnica completa.\n"
            "</thought>\n"
            "<response>\n"
            "Voy a registrar el marco de trabajo Kanban.\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Kanban\"\n"
            "</commands>"
        )},
        {"from": "human", "value": (
            "[RESULTADO COMANDO /save \"Kanban\"]\n"
            "Error: No se ha guardado el concepto '[[Kanban]]'. El contenido en <response> parece ser una frase transitoria o anuncio de intención (\"Voy a registrar...\") en lugar de una definición enciclopédica real.\n"
            "Instrucción: Para guardar o editar, debes redactar la definición técnica completa dentro de las etiquetas <definition>...</definition> en el bloque <response>."
        )},
        {"from": "gpt", "value": (
            "<thought>\n"
            "1. El sistema rechazó /save porque emití una frase de anuncio en lugar del contenido estructurado.\n"
            "2. Debo redactar inmediatamente la definición técnica completa dentro de <definition> con sus secciones y relaciones.\n"
            "3. Ejecutaré /save de nuevo con el contenido válido.\n"
            "</thought>\n"
            "<response>\n"
            "<definition>\n"
            "Kanban es un método de gestión visual del flujo de trabajo enfocado en la entrega continua, la transparencia y la limitación del trabajo en progreso (WIP).\n"
            "</definition>\n"
            "<sections>\n"
            "  <section name=\"Prácticas fundamentales\">\n"
            "- Visualizar el flujo de trabajo en tableros.\n"
            "- Limitar el trabajo en curso (WIP limits).\n"
            "- Gestionar el flujo y medir métricas (Lead Time, Cycle Time).\n"
            "  </section>\n"
            "</sections>\n"
            "<relations>\n"
            "  <relation type=\"relates_to\" target=\"Scrum\">Ambos son marcos de trabajo ágiles ampliamente utilizados.</relation>\n"
            "  <relation type=\"part_of\" target=\"Metodología Ágil\">Enfoque ágil sin iteraciones fijas.</relation>\n"
            "</relations>\n"
            "He registrado la definición y estructura completa de Kanban en la wiki.\n"
            "</response>\n"
            "<commands>\n"
            "/save \"Kanban\"\n"
            "</commands>"
        )}
    ]})

    # =========================================================================
    # MODO 2: <MODO: EXPLICADOR> — Resúmenes conceptuales (sin <thought>)
    # =========================================================================
    explicador_cases = [
        ("Explica 'Redes Neuronales' (categoría: IA).", "**Redes Neuronales** (Categoría: IA)\n\nModelos computacionales inspirados en la estructura neuronal biológica que aprenden a reconocer patrones complejos a partir de datos mediante capas de pesos ajustables.\n\n**Conceptos vinculados:** [[Machine Learning]], [[Deep Learning]]"),
        ("Explica 'React' (categoría: Frontend).", "**React** (Categoría: Frontend)\n\nBiblioteca declarativa y basada en componentes creada por Meta para el desarrollo de interfaces de usuario interactivas y reactivas mediante un Virtual DOM.\n\n**Conceptos vinculados:** [[JavaScript]], [[Node.js]]"),
        ("Explica el concepto 'CI/CD' de la categoría 'DevOps'.", "**CI/CD** (Categoría: DevOps)\n\nPráctica de desarrollo que combina la integración continua (automatización de compilación y pruebas) con el despliegue continuo hacia entornos de staging y producción.\n\n**Conceptos vinculados:** [[Git]], [[Docker]], [[Pipeline de Pruebas]]"),
        ("Explica 'WebSockets' (categoría: Redes).", "**WebSockets** (Categoría: Redes)\n\nProtocolo de comunicación bidireccional y persistente sobre una única conexión TCP, ideal para aplicaciones en tiempo real con baja latencia.\n\n**Conceptos vinculados:** [[HTTP]], [[TCP/IP]], [[APIs en Tiempo Real]]"),
        ("Explica el concepto 'GraphQL' de la categoría 'APIs'.", "**GraphQL** (Categoría: APIs)\n\nLenguaje de consulta y entorno de ejecución del lado del servidor que permite a los clientes solicitar únicamente los datos que necesitan mediante un único endpoint tipado.\n\n**Conceptos vinculados:** [[API REST]], [[Schema]], [[JSON]]"),
        ("Explica 'Docker' (categoría: Infraestructura).", "**Docker** (Categoría: Infraestructura)\n\nPlataforma de virtualización a nivel de sistema operativo que empaqueta aplicaciones y sus dependencias en contenedores ligeros y reproducibles.\n\n**Conceptos vinculados:** [[Contenedores OCI]], [[Kubernetes]]"),
        ("Explica el concepto 'Índices B-Tree' de la categoría 'Bases de Datos'.", "**Índices B-Tree** (Categoría: Bases de Datos)\n\nEstructura de datos balanceada utilizada por la mayoría de motores RDBMS (como PostgreSQL y MySQL) para acelerar búsquedas de rango y coincidencias de igualdad en tiempo logarítmico.\n\n**Conceptos vinculados:** [[PostgreSQL]], [[Optimización de Consultas]]"),
        ("Explica 'Microservicios' (categoría: Arquitectura).", "**Microservicios** (Categoría: Arquitectura)\n\nEstilo arquitectónico que estructura una aplicación como una colección de servicios autónomos, débilmente acoplados e independientemente desplegables comunicados vía APIs ligeras.\n\n**Conceptos vinculados:** [[Monolito]], [[API Gateway]], [[Contenedores]]"),
        ("Explica 'OAuth 2.0' (categoría: Seguridad).", "**OAuth 2.0** (Categoría: Seguridad)\n\nProtocolo estándar de autorización delegada que permite a terceros acceder a recursos protegidos en nombre de un usuario sin compartir sus credenciales.\n\n**Conceptos vinculados:** [[JWT]], [[OpenID Connect]]"),
        ("Explica 'Domain-Driven Design' (categoría: Arquitectura).", "**Domain-Driven Design (DDD)** (Categoría: Arquitectura)\n\nEnfoque de diseño de software centrado en modelar la lógica de negocio a través de un lenguaje ubicuo compartido y límites de contexto (Bounded Contexts) bien definidos.\n\n**Conceptos vinculados:** [[Clean Architecture]], [[Microservicios]]")
    ]

    for human_val, gpt_val in explicador_cases:
        examples.append({"conversations": [
            {"from": "system", "value": "<MODO: EXPLICADOR>"},
            {"from": "human", "value": human_val},
            {"from": "gpt", "value": gpt_val}
        ]})

    # =========================================================================
    # MODO 3: <MODO: GRAFO> — Análisis de relaciones en el grafo (sin <thought>)
    # =========================================================================
    grafo_cases = [
        ("¿Qué relaciones tiene 'API REST'?", "El concepto **API REST** tiene las siguientes conexiones:\n- **Referencias salientes:** [[HTTP]], [[JSON]], [[Arquitectura Cliente-Servidor]]\n- **Referencias entrantes:** [[Microservicios]], [[Backend]], [[API Gateway]]"),
        ("¿Con qué conceptos está conectado 'Scrum'?", "El concepto **Scrum** tiene las siguientes conexiones:\n- **Referencias salientes:** [[Agile]], [[Sprint]], [[Product Owner]]\n- **Referencias entrantes:** [[Metodologías de Desarrollo]], [[Gestión de Proyectos]]"),
        ("¿Qué relaciones tiene 'Kubernetes'?", "El concepto **Kubernetes** tiene las siguientes conexiones:\n- **Referencias salientes:** [[Contenedores OCI]], [[Docker]], [[Pods]], [[Cluster Management]]\n- **Referencias entrantes:** [[DevOps]], [[Microservicios]], [[Infraestructura Cloud]]"),
        ("¿Con qué elementos conecta 'PostgreSQL' en el grafo?", "El concepto **PostgreSQL** tiene las siguientes conexiones:\n- **Referencias salientes:** [[SQL]], [[Transacciones ACID]], [[Índices B-Tree]], [[Replicación Streaming]]\n- **Referencias entrantes:** [[Base de Datos Principal]], [[ORM]], [[Backend API]]"),
        ("¿Cuáles son las dependencias y conexiones de 'JWT'?", "El concepto **JWT (JSON Web Token)** tiene las siguientes conexiones:\n- **Referencias salientes:** [[Criptografía HMAC/RSA]], [[Firma Digital]], [[Base64Url]]\n- **Referencias entrantes:** [[Autenticación de Usuarios]], [[API Gateway]], [[OAuth 2.0]]"),
        ("¿Qué relaciones tiene 'Redis'?", "El concepto **Redis** tiene las siguientes conexiones:\n- **Referencias salientes:** [[Caché en Memoria]], [[Estructuras de Datos]], [[Pub/Sub]]\n- **Referencias entrantes:** [[Optimización de Consultas]], [[Gestión de Sesiones]], [[Rate Limiting]]"),
        ("¿Con qué conceptos conecta 'Clean Architecture'?", "El concepto **Clean Architecture** tiene las siguientes conexiones:\n- **Referencias salientes:** [[Domain-Driven Design]], [[Inversión de Dependencias]], [[Patrón Repositorio]]\n- **Referencias entrantes:** [[Estándares de Código]], [[Arquitectura Backend]]"),
        ("¿Qué dependencias y referencias tiene 'Git'?", "El concepto **Git** tiene las siguientes conexiones:\n- **Referencias salientes:** [[Control de Versiones]], [[Ramas]], [[Conventional Commits]]\n- **Referencias entrantes:** [[GitHub]], [[Pipeline CI/CD]], [[Flujo de Desarrollo]]"),
        ("¿Con qué temas se relaciona 'TypeScript'?", "El concepto **TypeScript** tiene las siguientes conexiones:\n- **Referencias salientes:** [[JavaScript]], [[Tipado Estático]], [[Compilación]]\n- **Referencias entrantes:** [[Frontend React]], [[Backend Node.js]], [[Estándares de Desarrollo]]"),
        ("¿Qué conexiones tiene 'Apache Kafka' en la memoria?", "El concepto **Apache Kafka** tiene las siguientes conexiones:\n- **Referencias salientes:** [[Event-Driven Architecture]], [[Topics]], [[Particiones]], [[Broker de Mensajes]]\n- **Referencias entrantes:** [[Microservicios]], [[Ingesta de Datos]], [[Eventos de Facturación]]")
    ]

    for human_val, gpt_val in grafo_cases:
        examples.append({"conversations": [
            {"from": "system", "value": "<MODO: GRAFO>"},
            {"from": "human", "value": human_val},
            {"from": "gpt", "value": gpt_val}
        ]})

        # Cargar 49 ejemplos complementarios para alcanzar exactamente 100
    examples.extend(ft2_extra.get_ft2_extra_examples())
    assert len(examples) == 100, f"Error: {len(examples)} != 100"
    # Multi-source: conversiones de agente remitente
    _ms_apply(examples, [
        (1,  'Consulta tecnica. Tono conciso.'),
        (6,  'Consulta directa. Tono tecnico.'),
        (10, 'Comparativa tecnica delegada.'),
        (26, 'Busqueda tecnica delegada.'),
        (31, 'Consulta conceptual delegada.'),
        (34, 'Consulta tecnica de red.'),
        (36, 'Consulta de infra. Tono tecnico.'),
        (41, 'Consulta de relaciones conceptuales.'),
        (43, 'Consulta de grafo conceptual.'),
        (46, 'Consulta de conexiones conceptuales.'),
        (66, 'Consulta sobre procesamiento de eventos.'),
        (82, 'Busqueda de protocolo de despliegue.'),
        (85, 'Busqueda delegada sobre dead letter queues.'),
        (90, 'Consulta sobre rollback en produccion.'),
        (93, 'Busqueda de protocolo de pruebas.'),
        (99, 'Solicitud de manual DRP.'),
    ])
    return examples


def main():
    out_dir = Path("data/exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "dataset_ft2_agent_react.jsonl"
    legacy_file = out_dir / "master_prompt_agent_dataset.jsonl"

    examples = create_examples()
    with open(out_file, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    # Copia retrocompatible
    with open(legacy_file, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"[EXITO] Dataset FT2 (Agente ReAct / Chain-of-Thought) generado en:")
    print(f"📁 {out_file.resolve()}")
    print(f"   Total de ejemplos: {len(examples)}")
    print(f"   - MODO AGENTE (con <thought>): 30 ejemplos")
    print(f"   - MODO EXPLICADOR: 10 ejemplos")
    print(f"   - MODO GRAFO: 10 ejemplos")


if __name__ == "__main__":
    main()
