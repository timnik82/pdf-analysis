# PDF Analysis - Academic Paper Section Extraction

Intelligent PDF extraction tool for academic papers with advanced section detection and clean output formatting.

## Features

- **Smart Section Detection** - Automatically extracts Introduction, Conclusion, Results, Discussion, and Future Outlook sections
- **Fuzzy Matching** - Detects section variations like "Concluding Remarks", "Summary and Conclusions", "Perspectives"
- **DOI Extraction** - Automatically finds and includes clickable DOI links
- **Mendeley Integration** - Check DOIs against your Mendeley library to avoid duplicates
- **Dual Export Format**
  - `JSON` - Structured data for programmatic access
  - `Markdown` - Clean, LLM-friendly format for analysis
- **Intelligent Noise Filtering** - Removes page headers, author affiliations, copyright notices, and other metadata

## Installation

```bash
# Clone the repository
git clone https://github.com/timnik82/pdf-analysis.git
cd pdf-analysis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## PDF Section Extraction

1. Place PDF files in the `pdfs/` directory
2. Run the extraction script:

```bash
python extract_sections.py
```

1. View results:
   - `extracted_sections.json` - Structured JSON output
   - `extracted_sections.md` - LLM-friendly markdown

## Mendeley DOI Checker

Check a batch of DOIs against your Mendeley library to see which papers you already have.

> **Note**: Uses `check_mendeley_dois_v2.py` which works with Python 3.12+ by using the Mendeley API directly (the old SDK is incompatible with modern Python).

### Setup

1. Follow the [Mendeley Setup Guide](mendeley_setup_guide.md) to get API credentials
2. Copy `.env.example` to `.env` and add your credentials
3. Install dependencies: `pip install python-dotenv requests`

### Usage

**Check specific DOIs:**

```bash
python check_mendeley_dois_v2.py --dois "10.1038/nature12345,10.1126/science.abc123"
```

**Check DOIs from a file:**

```bash
# Create a file with one DOI per line
python check_mendeley_dois_v2.py --file dois.txt
```

**Interactive mode:**

```bash
python check_mendeley_dois_v2.py --interactive
```

**Save results to JSON:**

```bash
python check_mendeley_dois_v2.py --file dois.txt --output results.json
```

### Example Output

```text
======================================================================
RESULTS: Checked 5 DOIs against your Mendeley library
======================================================================

✓ ALREADY IN LIBRARY (2):

  • 10.1038/nature12345
    Recent advances in graphene-based phase change composites - Smith, Johnson et al. (2023)

  • 10.1371/journal.pmed.0020124
    Why Most Published Research Findings Are False - Ioannidis (2005)


✗ NOT IN LIBRARY (3):

  • 10.1016/j.cell.2023.01.001
  • 10.1101/2024.01.15.575432
  • 10.1126/science.abc123

======================================================================
```

## Example PDF Extraction Output

```markdown
# Paper 1: Recent advances in graphene-based phase change composites...

**DOI:** [https://doi.org/10.1016/j.nanoms.2023.09.003](...)

## Introduction
Energy storage and conservation are receiving increased attention...

## Conclusion
The present article provides an overview of the latest advancements...
```

## Dependencies

- `pymupdf4llm` - PDF to Markdown conversion
- `rapidfuzz` - Fuzzy string matching for section headers
- `mendeley` - Mendeley API Python SDK
- `python-dotenv` - Environment variable management

## Testing

This repository includes comprehensive test coverage for core functionality.

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_extract_sections.py

# Run specific test class
pytest tests/test_extract_sections.py::TestFuzzyMatchSection

# Run specific test
pytest tests/test_extract_sections.py::TestFuzzyMatchSection::test_exact_match_introduction
```

### Test Coverage

**extract_sections.py tests (45 tests)**:
- `fuzzy_match_section` - Section header matching with variations
- `extract_doi` - DOI extraction from text
- `clean_content` - Content cleaning and noise removal
- `detect_section_by_content` - Content-based section detection
- `extract_sections_from_markdown` - End-to-end section extraction

**check_mendeley_dois_v2.py tests (18 tests)**:
- `check_dois` - DOI matching against library (case-insensitive, whitespace handling)
- `fetch_library_dois` - API interaction (mocked), including pagination support
- `save_results` - JSON output formatting
- `print_results` - Console output formatting

All tests are organized in the `tests/` directory with clear, descriptive names and comprehensive edge case coverage.

## License

MIT
