#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PDF_DIR="${PDF_DIR:-$SCRIPT_DIR/pdfs}"
OUT_DIR="${OUT_DIR:-$SCRIPT_DIR/markdown}"
CLEANER="${CLEANER:-$SCRIPT_DIR/clean_marker_output.py}"
CONVERTER="${CONVERTER:-$SCRIPT_DIR/convert_pdfs_pymupdf4llm.py}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found in PATH." >&2
  exit 1
fi

if [[ "${USE_MARKER:-}" == "1" ]]; then
  if ! command -v marker >/dev/null 2>&1; then
    echo "marker is required but was not found in PATH." >&2
    exit 1
  fi
  if [[ ! -f "$CLEANER" ]]; then
    echo "Cleaner script not found: $CLEANER" >&2
    exit 1
  fi
  marker "$PDF_DIR" \
    --output_dir "$OUT_DIR" \
    --output_format markdown \
    --skip_existing

  python3 "$CLEANER" "$OUT_DIR"
else
  if [[ ! -f "$CONVERTER" ]]; then
    echo "Converter script not found: $CONVERTER" >&2
    exit 1
  fi
  converter_args=(--pdf-dir "$PDF_DIR" --out-dir "$OUT_DIR")
  if [[ "${OVERWRITE:-}" == "1" ]]; then
    converter_args+=(--overwrite)
  fi
  if ! python3 "$CONVERTER" "${converter_args[@]}"; then
    echo "Converter failed: $CONVERTER" >&2
    exit 1
  fi
fi
