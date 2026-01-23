#!/usr/bin/env python3
"""
Convert PDFs to cleaned Markdown using pymupdf4llm.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pymupdf4llm

from clean_marker_output import clean_markdown


def iter_pdf_files(pdf_dir: Path) -> list[Path]:
    """Collect PDF files from a directory."""
    return sorted(
        [
            path
            for path in pdf_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        ]
    )


def convert_pdf(pdf_path: Path, out_dir: Path, overwrite: bool) -> None:
    """Convert a single PDF to cleaned Markdown."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{pdf_path.stem}.md"

    if out_path.exists() and not overwrite:
        print(f"Skipping existing {out_path}")
        return

    md_text = pymupdf4llm.to_markdown(str(pdf_path))
    cleaned = clean_markdown(md_text)
    out_path.write_text(cleaned, encoding="utf-8")
    print(f"Wrote {out_path}")


def main() -> int:
    """Entry point for converting PDFs to Markdown."""
    parser = argparse.ArgumentParser(
        description="Convert PDFs to cleaned Markdown with pymupdf4llm."
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=Path("pdfs"),
        help="Directory containing PDFs to convert.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("markdown"),
        help="Directory to write Markdown files.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing Markdown files.",
    )
    args = parser.parse_args()

    if not args.pdf_dir.is_dir():
        print(f"PDF directory not found: {args.pdf_dir}")
        return 1

    pdf_files = iter_pdf_files(args.pdf_dir)
    if not pdf_files:
        print("No PDF files found.")
        return 1

    had_errors = False
    for pdf_path in pdf_files:
        try:
            convert_pdf(pdf_path, args.out_dir, args.overwrite)
        except Exception as exc:
            print(f"Error converting {pdf_path}: {exc}", file=sys.stderr)
            had_errors = True

    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
