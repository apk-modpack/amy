"""Script para construir y consolidar Datasets Acumulativos bajo el estándar oficial.

Estándar de Nombres:
  - Parciales:
      data/exports/dataset_ft1_cli_standards.jsonl     (Estándares CLI y micro-formato XML)
      data/exports/dataset_ft2_agent_react.jsonl       (Razonamiento Agente ReAct / Multi-ciclos)
      data/exports/dataset_ft3_structured_saves.jsonl  (Guardado estructurado y corrección de fallos)
      data/exports/dataset_ft4_multiagent.jsonl        (Protocolo multi-agente e identidad)
      data/exports/dataset_ft5_tasklist.jsonl          (Lista de tareas cognitivas y loop multi-ciclo)
      data/exports/dataset_ft6_wiki_grounding.jsonl    (Wiki-grounding y menor dependencia de contexto)
  - Acumulativos para Fine-Tuning:
      data/exports/dataset_cumulative_v6.jsonl         (FT1 a FT6 consolidado - 600 ejemplos)

Uso:
    python build_cumulative_dataset.py
    python build_cumulative_dataset.py --output dataset_cumulative_v6.jsonl --add-file nuevo_dataset.jsonl
"""

import sys
import argparse
from pathlib import Path

# Soporte UTF-8 en terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from wiki_agent.tools.dataset_manager import CumulativeDatasetBuilder
import generate_ft1_dataset
import generate_agent_dataset
import generate_ft3_dataset
import generate_ft4_multiagent_dataset
import generate_ft5_tasklist_dataset
import generate_ft6_wiki_grounding_dataset


def main():
    parser = argparse.ArgumentParser(
        description="Constructor de Dataset Acumulativo Estandarizado para Fine-Tuning de Llama 3.2"
    )
    parser.add_argument(
        "--output", "-o",
        default="dataset_cumulative_v6.jsonl",
        help="Nombre del archivo de salida acumulativo (default: dataset_cumulative_v6.jsonl)"
    )
    parser.add_argument(
        "--output-dir", "-d",
        default="data/exports",
        help="Directorio de exportación (default: data/exports)"
    )
    parser.add_argument(
        "--add-file", "-a",
        action="append",
        default=[],
        help="Archivo JSONL adicional a incorporar (se puede usar múltiples veces)"
    )

    args = parser.parse_args()

    out_dir = PROJECT_ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    input_files = []

    print("=================================================================")
    print(" [SISTEMA] CONSTRUCTOR DE DATASET ACUMULATIVO PARA FINE-TUNING")
    print("=================================================================")

    # 1. Generar Dataset FT1: Estándares CLI y Micro-formato XML
    print("\n1. Generando/Verificando Dataset FT1: Estándares CLI y micro-formato XML...")
    ft1_file = out_dir / "dataset_ft1_cli_standards.jsonl"
    generate_ft1_dataset.main()
    if ft1_file.exists():
        input_files.append(ft1_file)

    # 2. Generar Dataset FT2: Agente ReAct (Thought + Multi-ciclo)
    print("\n2. Generando/Verificando Dataset FT2: Agente ReAct (<thought> + herramientas)...")
    ft2_file = out_dir / "dataset_ft2_agent_react.jsonl"
    generate_agent_dataset.main()
    if ft2_file.exists():
        input_files.append(ft2_file)

    # 3. Generar Dataset FT3: Guardado Estructurado y Corrección de Fallos
    print("\n3. Generando/Verificando Dataset FT3: Guardado estructurado y correccion de fallos...")
    ft3_file = out_dir / "dataset_ft3_structured_saves.jsonl"
    generate_ft3_dataset.main()
    if ft3_file.exists():
        input_files.append(ft3_file)

    # 4. Generar Dataset FT4: Interacción Inter-Agente y Remitente HUMAN
    print("\n4. Generando/Verificando Dataset FT4: Protocolo inter-agente y remitente HUMAN...")
    ft4_file = out_dir / "dataset_ft4_multiagent.jsonl"
    generate_ft4_multiagent_dataset.main()
    if ft4_file.exists():
        input_files.append(ft4_file)

    # 5. Generar Dataset FT5: Lista de Tareas Cognitivas y Planificación Multi-paso
    print("\n5. Generando/Verificando Dataset FT5: Lista de tareas cognitivas y planificación...")
    ft5_file = out_dir / "dataset_ft5_tasklist.jsonl"
    generate_ft5_tasklist_dataset.main()
    if ft5_file.exists():
        input_files.append(ft5_file)

    # 6. Generar Dataset FT6: Wiki-Grounding y Menor Dependencia de Contexto
    print("\n6. Generando/Verificando Dataset FT6: Wiki-Grounding y menor dependencia de contexto...")
    ft6_file = out_dir / "dataset_ft6_wiki_grounding.jsonl"
    generate_ft6_wiki_grounding_dataset.main()
    if ft6_file.exists():
        input_files.append(ft6_file)

    # 7. Archivos adicionales especificados por parámetro
    for extra in args.add_file:
        p = Path(extra)
        if p.exists():
            input_files.append(p)
            print(f"   [+] Añadido dataset adicional: {p}")
        else:
            print(f"   [AVISO] Archivo no encontrado: {p}")

    # 8. Fusión y normalización acumulativa
    print("\n7. Consolidando y deduplicando datasets bajo el estándar acumulativo...")
    builder = CumulativeDatasetBuilder(output_dir=out_dir)
    final_path, stats = builder.merge_datasets(
        input_files=input_files,
        output_filename=args.output,
        deduplicate=True
    )

    print("\n=================================================================")
    print(f" [EXITO] DATASET ACUMULATIVO MAESTRO GENERADO")
    print(f" Archivo: {final_path.resolve()}")
    print("-----------------------------------------------------------------")
    print(f" Total de ejemplos consolidados : {stats['total_validos']}")
    print(f" - Ejemplos Agente ReAct (FT2)  : {stats['categorias']['agente_react']}")
    print(f" - Ejemplos Estándar CLI (FT1)  : {stats['categorias']['conocimiento_general']}")
    print(f" - Duplicados descartados       : {stats['duplicados_omitidos']}")
    print("\n Desglose por componente:")
    for f_name, f_info in stats["por_archivo"].items():
        print(f"   * {f_name:<36}: {f_info['incorporados']} ejemplos")
    print("=================================================================")
    print(f"Sube '{args.output}' a tu carpeta 'finetuning' en Google Drive.")
    print("En la Celda 0 de Colab ajusta:")
    print(f'   DATASET_FILENAME = "{args.output}"')
    version_tag = args.output.replace("dataset_", "").replace(".jsonl", "")
    print(f'   OUTPUT_GGUF_NAME = "llama3.2-{version_tag}.gguf"')
    print("=================================================================\n")


if __name__ == "__main__":
    main()
