#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for descriptor in beitv2_base_final beitv2_base_multilayer; do
  .venv-confirmatory/bin/python src/replicate_electronics_beitv2_kth.py --descriptor "$descriptor"
done
