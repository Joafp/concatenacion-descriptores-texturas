#!/usr/bin/env bash
set -euo pipefail

# Puente robusto para invocación desde ``wsl.exe --exec``: fija el directorio
# del proyecto antes de delegar al barrido principal.
cd "$(cd -- "$(dirname -- "$0")/.." && pwd)"
exec bash scripts/run_diverse_topk_control.sh "$@"
