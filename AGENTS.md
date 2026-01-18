# AGENTS.md

This file provides context for AI coding agents working on this repository.

## Project Overview

PDF section extraction tool for academic papers. Converts PDFs to markdown, then extracts key sections (Introduction, Conclusion, Future Outlook, etc.) using regex patterns, fuzzy matching, and content-based detection.

## Repository Structure

```
pdf-analysis/
├── extract_sections.py   # Main extraction script
├── requirements.txt      # Dependencies (pymupdf4llm, rapidfuzz)
├── pdfs/                 # Input PDFs (gitignored)
├── extracted_sections.json  # JSON output (gitignored)
└── extracted_sections.md    # Markdown output (gitignored)
```

## Code Conventions

- **Python 3.8+** with type hints where beneficial
- Use `re.compile()` for regex patterns with descriptive comments
- Keep noise filtering patterns in `NOISE_PATTERNS` list
- Keep section detection patterns in `target_headers` dict
- Functions should have docstrings explaining purpose

## Key Components

### Section Detection (`extract_sections_from_markdown`)

- Primary: Regex patterns in `target_headers` dict
- Fallback: Fuzzy matching via `fuzzy_match_section()`  
- Last resort: Content-based detection via `detect_section_by_content()`

### Boundary Detection

- `generic_section_pattern`: Numbered headers like "2. Methods"
- `end_section_patterns`: References, Acknowledgments, etc.
- Filters false positives (page numbers, addresses, citations)

### Content Cleaning (`clean_content`)

- Removes noise via patterns in `NOISE_PATTERNS`
- Filters: author lines, emails, page numbers, copyright text

## Common Tasks

### Adding a new section type

1. Add pattern to `target_headers` dict
2. Add keywords to `SECTION_KEYWORDS` for fuzzy matching
3. Add to `section_order` list in `export_to_markdown()`

### Adding noise filters

1. Add regex pattern to `NOISE_PATTERNS` list
2. Pattern should match entire line (`^...$`)
3. Test with `python extract_sections.py`

### Testing changes

```bash
source venv/bin/activate
python extract_sections.py
# Check extracted_sections.md for results
```

## Dependencies

- `pymupdf4llm` - PDF to Markdown conversion
- `rapidfuzz` - Fuzzy string matching for headers
