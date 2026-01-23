#!/usr/bin/env bash
set -euo pipefail

PDF_DIR="/home/timnik/coding/pdf-analysis/pdfs"
OUT_DIR="/home/timnik/coding/pdf-analysis/markdown"
CLEANER="/home/timnik/coding/pdf-analysis/clean_marker_output.py"

marker "$PDF_DIR" \
  --output_dir "$OUT_DIR" \
  --output_format markdown \
  --skip_existing

python3 "$CLEANER" "$OUT_DIR"
