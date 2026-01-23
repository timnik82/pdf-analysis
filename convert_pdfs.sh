#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PDF_DIR="${PDF_DIR:-$SCRIPT_DIR/pdfs}"
OUT_DIR="${OUT_DIR:-$SCRIPT_DIR/markdown}"
CLEANER="${CLEANER:-$SCRIPT_DIR/clean_marker_output.py}"

marker "$PDF_DIR" \
  --output_dir "$OUT_DIR" \
  --output_format markdown \
  --skip_existing

python3 "$CLEANER" "$OUT_DIR"
