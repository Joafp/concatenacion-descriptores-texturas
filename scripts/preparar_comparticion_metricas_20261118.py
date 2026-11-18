#!/usr/bin/env python3
"""Inventario y copia de métricas textuales existentes; no ejecuta experimentos."""
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/metricas_compartidas_20261118_v1'
SKIP = {'checkpoints', 'staging', 'rgb_ngram_count_cache', 'count_cache', 'logs', 'smoke'}
EXTS = {'.csv', '.json', '.md', '.txt'}
KEYWORDS = ('metric', 'summary', 'resumen', 'coverage', 'confusion', 'per_class',
            'por_clase', 'nested_fold_results', 'condition_results', 'latency', 'latencia')
CANONICAL = {
    'hytex_paper_metrics_20261116_v3', 'external_paper_metrics_20261116_v2',
    'sota_reporte_20261117_v1', 'e4_resmlp_complete_audit_20261116_v1',
    'e5_top4_plus_ngram_audit_20261116_v1', 'e5_secondary_complete_20261116_v1',
    'top4_fixed_kth_completion_audit_20261115_v1', 'hytex_fmd_robustness_20261116_audit_v1',
    'neshov_paperlike_fmd_10x10_consolidated_20261103_v1',
}
SECRET = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AIza[0-9A-Za-z_-]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{30,}')


def run_git(arguments, input_text=None):
    return subprocess.run(['git', *arguments], cwd=ROOT, input=input_text,
                          text=True, capture_output=True, check=False)


def main():
    paths = []
    for base, dirs, files in os.walk(ROOT / 'results'):
        dirs[:] = [name for name in dirs if name not in SKIP and not name.startswith('metricas_compartidas_')]
        parent = Path(base)
        for name in files:
            file = parent / name
            if file.is_symlink() or file.suffix.lower() not in EXTS:
                continue
            rel = file.relative_to(ROOT).as_posix()
            in_canonical = any(part in CANONICAL for part in file.parts)
            if in_canonical or any(term in name.lower() for term in KEYWORDS):
                paths.append(rel)
    paths.sort()
    if not paths:
        raise ValueError('No se encontraron archivos')
    ignored_result = run_git(['check-ignore', '--stdin', '-z'], '\0'.join(paths) + '\0')
    if ignored_result.returncode not in (0, 1):
        raise RuntimeError(ignored_result.stderr)
    ignored = set(ignored_result.stdout.split('\0'))
    tracked_result = run_git(['ls-files', '-z', 'results'])
    if tracked_result.returncode:
        raise RuntimeError(tracked_result.stderr)
    tracked = set(tracked_result.stdout.split('\0'))
    entries, copies = [], {}
    for path in paths:
        if any(char in path for char in ':*?<>|\\'):
            raise ValueError(f'Ruta incompatible con Windows: {path}')
        file = ROOT / path
        before = file.stat()
        if before.st_size > 10_000_000:
            raise ValueError(f'Archivo demasiado grande para este paquete: {path}')
        raw = file.read_bytes()
        after = file.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError(f'Archivo en modificación: {path}')
        raw.decode('utf-8-sig')
        if SECRET.search(raw):
            raise ValueError(f'Posible credencial detectada en {path}; no se preparó el paquete')
        digest = hashlib.sha256(raw).hexdigest()
        destination = path
        state = 'ya_versionado' if path in tracked else 'nuevo'
        if path in ignored:
            destination = f'results/metricas_compartidas_20261118_v1/archivos_ignorados/{digest}{file.suffix.lower()}'
            copies[destination] = raw
            state = 'copia_de_ruta_ignorada'
        entries.append({'origen': path, 'ruta_git': destination, 'sha256': digest,
                        'bytes': len(raw), 'situacion': state})
    OUT.mkdir(parents=True, exist_ok=False)
    for path, data in copies.items():
        destination = ROOT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write(data)
    index = {'fecha_utc': datetime.now(timezone.utc).isoformat(),
             'alcance': 'Archivos CSV/JSON/MD/TXT con nombres relacionados con métricas, cobertura, resumen, confusión o latencia bajo results, más directorios canónicos listados; se excluyen logs, checkpoints, staging, smoke y cachés. No es un catálogo exhaustivo ni avala estados.',
             'directorios_canonicos': sorted(CANONICAL), 'archivos': entries}
    (OUT / 'inventario.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    counts = {state: sum(row['situacion'] == state for row in entries)
              for state in ('ya_versionado', 'nuevo', 'copia_de_ruta_ignorada')}
    print('Archivos indexados:', len(entries), 'por situación:', counts, 'copias únicas:', len(copies))


if __name__ == '__main__':
    main()
