import json
import hashlib
import os
from pathlib import Path

def calc_hash(ex):
    convs = ex.get('conversations', [])
    raw = '|'.join(f"{c.get('from')}:{c.get('value', '').strip()}" for c in convs)
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

out_dir = Path('data/exports')
files = [
    out_dir / 'dataset_ft1_cli_standards.jsonl',
    out_dir / 'dataset_ft2_agent_react.jsonl',
    out_dir / 'dataset_ft3_structured_saves.jsonl'
]

seen = set()
merged = []
stats = {'total': 0, 'agente_react': 0, 'general': 0, 'duplicados': 0, 'por_archivo': {}}

for f in files:
    cnt = 0
    with open(f, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            h = calc_hash(data)
            if h in seen:
                stats['duplicados'] += 1
                continue
            seen.add(h)
            merged.append(data)
            cnt += 1
            has_th = any('<thought>' in c.get('value', '') for c in data.get('conversations', []))
            if has_th:
                stats['agente_react'] += 1
            else:
                stats['general'] += 1
    stats['por_archivo'][f.name] = cnt

out_file = out_dir / 'dataset_cumulative_v3.jsonl'
with open(out_file, 'w', encoding='utf-8') as out_fh:
    for ex in merged:
        out_fh.write(json.dumps(ex, ensure_ascii=False) + '\n')

stats['total'] = len(merged)
print("SUCCESS:", json.dumps(stats, indent=2))
os._exit(0)
