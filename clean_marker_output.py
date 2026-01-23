#!/usr/bin/env python3
"""
Clean Marker-generated Markdown by removing publisher footers and references.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List

FOOTER_PATTERNS = [
    re.compile(r"Downloaded from .*Wiley Online Library", re.IGNORECASE),
    re.compile(r"See the Terms and Conditions", re.IGNORECASE),
    re.compile(r"OA articles are governed by", re.IGNORECASE),
]

FIGURE_PATTERNS = [
    re.compile(r"^\s*!\[.*\]\(.*\)\s*$"),  # Markdown image tags
    re.compile(r"^\s*<img[^>]*>\s*$", re.IGNORECASE),  # HTML image tags
    re.compile(r"^\s*(figure|fig\.?)\s*\d+\s*[:.]", re.IGNORECASE),  # Captions
]

REFERENCE_START_PATTERNS = [
    re.compile(r"^\s*#{1,6}\s*(references|bibliography)\b", re.IGNORECASE),
    re.compile(r"^\s*(references|bibliography)\s*$", re.IGNORECASE),
    re.compile(r"^\s*-\s*\[\d+\]\s+", re.IGNORECASE),
    re.compile(r"^\s*#{1,6}\s*supporting information\b", re.IGNORECASE),
    re.compile(r"^\s*#{1,6}\s*acknowledg(e)?ments\b", re.IGNORECASE),
    re.compile(r"^\s*#{1,6}\s*conflict of interest\b", re.IGNORECASE),
    re.compile(r"^\s*#{1,6}\s*data availability\b", re.IGNORECASE),
]


def iter_markdown_files(paths: Iterable[Path]) -> List[Path]:
    """Collect markdown files from file/dir inputs."""
    files: List[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(path.rglob("*.md"))
        elif path.is_file() and path.suffix.lower() == ".md":
            files.append(path)
    return sorted(set(files))


def strip_footer_lines(lines: List[str]) -> List[str]:
    """Remove lines that match known publisher footer patterns."""
    return [
        line
        for line in lines
        if not any(pattern.search(line) for pattern in FOOTER_PATTERNS)
    ]


def strip_figure_lines(lines: List[str]) -> List[str]:
    """Remove image tags and figure caption lines."""
    return [
        line
        for line in lines
        if not any(pattern.search(line) for pattern in FIGURE_PATTERNS)
    ]


def strip_references(lines: List[str]) -> List[str]:
    """Trim content at the first detected reference-like heading or list."""
    for idx, line in enumerate(lines):
        normalized = re.sub(r"[*_`]", "", line)
        if any(pattern.search(normalized) for pattern in REFERENCE_START_PATTERNS):
            return lines[:idx]
    return lines


def normalize_trailing_blank_lines(lines: List[str]) -> List[str]:
    """Remove trailing blank lines for consistent output."""
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def clean_markdown(text: str) -> str:
    """Clean a markdown document string."""
    lines = text.splitlines()
    lines = strip_footer_lines(lines)
    lines = strip_figure_lines(lines)
    lines = strip_references(lines)
    lines = normalize_trailing_blank_lines(lines)
    return "\n".join(lines) + "\n"


def main() -> int:
    """Entry point for cleaning markdown files in place."""
    parser = argparse.ArgumentParser(
        description="Remove common publisher footers and references from Markdown."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Markdown file(s) or directories to clean.",
    )
    args = parser.parse_args()

    files = iter_markdown_files(args.paths)
    if not files:
        print("No Markdown files found.")
        return 1

    for md_path in files:
        original = md_path.read_text(encoding="utf-8")
        cleaned = clean_markdown(original)
        if cleaned != original:
            md_path.write_text(cleaned, encoding="utf-8")
            print(f"Cleaned {md_path}")
        else:
            print(f"No changes for {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
