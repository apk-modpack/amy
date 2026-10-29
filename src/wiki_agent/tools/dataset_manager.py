"""Gestor de Datasets Acumulativos para Fine-Tuning de Llama 3.2.

Permite fusionar, validar, deduplicar y versionar múltiples datasets (.jsonl)
para entrenar de forma limpia y acumulativa desde el modelo base Llama 3.2.
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def normalize_to_sharegpt(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normaliza cualquier formato de conversación a formato canónico ShareGPT.
    
    Admite:
      - ShareGPT: {"conversations": [{"from": "human"|"gpt"|"system", "value": "..."}]}
      - OpenAI / Messages: {"messages": [{"role": "user"|"assistant"|"system", "content": "..."}]}
      - Alpaca: {"instruction": "...", "input": "...", "output": "..."}
    """
    if "conversations" in entry and isinstance(entry["conversations"], list):
        convs = []
        for turn in entry["conversations"]:
            sender = turn.get("from", "human")
            val = turn.get("value", "")
            if not val:
                continue
            convs.append({"from": sender, "value": val})
        if convs:
            return {"conversations": convs}

    elif "messages" in entry and isinstance(entry["messages"], list):
        role_map = {"user": "human", "assistant": "gpt", "system": "system"}
        convs = []
        for msg in entry["messages"]:
            role = role_map.get(msg.get("role", "user"), "human")
            content = msg.get("content", "")
            if not content:
                continue
            convs.append({"from": role, "value": content})
        if convs:
            return {"conversations": convs}

    elif "instruction" in entry and "output" in entry:
        instr = entry.get("instruction", "").strip()
        inp = entry.get("input", "").strip()
        out = entry.get("output", "").strip()
        
        user_msg = f"{instr}\n\n{inp}".strip() if inp else instr
        if user_msg and out:
            return {
                "conversations": [
                    {"from": "human", "value": user_msg},
                    {"from": "gpt", "value": out}
                ]
            }

    return None


def calculate_hash(example: Dict[str, Any]) -> str:
    """Calcula un hash MD5 representativo del contenido para evitar duplicados exactos."""
    convs = example.get("conversations", [])
    raw_str = "|".join(f"{c.get('from')}:{c.get('value', '').strip()}" for c in convs)
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest()


class CumulativeDatasetBuilder:
    """Constructor y consolidador de datasets acumulativos."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def merge_datasets(
        self,
        input_files: List[Path],
        output_filename: str = "dataset_acumulado_v1.jsonl",
        deduplicate: bool = True
    ) -> Tuple[Path, Dict[str, Any]]:
        """Fusiona múltiples archivos JSONL en un dataset acumulativo normalizado.
        
        Args:
            input_files: Lista de rutas a archivos .jsonl.
            output_filename: Nombre del archivo de salida resultante.
            deduplicate: Si es True, descarta conversaciones idénticas.
            
        Returns:
            Tuple con la ruta del archivo generado y estadísticas del proceso.
        """
        seen_hashes = set()
        merged_examples: List[Dict[str, Any]] = []
        stats: Dict[str, Any] = {
            "total_leidos": 0,
            "total_validos": 0,
            "duplicados_omitidos": 0,
            "por_archivo": {},
            "categorias": {
                "agente_react": 0,
                "conocimiento_general": 0
            }
        }

        for path in input_files:
            file_path = Path(path)
            if not file_path.exists():
                logger.warning("Archivo no encontrado: %s", file_path)
                continue

            count_in_file = 0
            valid_in_file = 0

            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    line_clean = line.strip()
                    if not line_clean:
                        continue

                    count_in_file += 1
                    stats["total_leidos"] += 1

                    try:
                        raw_data = json.loads(line_clean)
                    except json.JSONDecodeError:
                        logger.error("JSON inválido en %s línea %d", file_path.name, line_num)
                        continue

                    normalized = normalize_to_sharegpt(raw_data)
                    if not normalized:
                        continue

                    if deduplicate:
                        h = calculate_hash(normalized)
                        if h in seen_hashes:
                            stats["duplicados_omitidos"] += 1
                            continue
                        seen_hashes.add(h)

                    # Clasificar para métricas informativas
                    convs = normalized.get("conversations", [])
                    has_thought = any("<thought>" in c.get("value", "") for c in convs)
                    if has_thought:
                        stats["categorias"]["agente_react"] += 1
                    else:
                        stats["categorias"]["conocimiento_general"] += 1

                    merged_examples.append(normalized)
                    valid_in_file += 1

            stats["por_archivo"][file_path.name] = {
                "leidos": count_in_file,
                "incorporados": valid_in_file
            }

        stats["total_validos"] = len(merged_examples)

        # Guardar dataset acumulado
        out_path = self.output_dir / output_filename
        with open(out_path, "w", encoding="utf-8") as f:
            for ex in merged_examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")

        return out_path, stats
