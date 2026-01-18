# PDF Analysis - Academic Paper Section Extraction

Intelligent PDF extraction tool for academic papers with advanced section detection and clean output formatting.

## Features

- **Smart Section Detection** - Automatically extracts Introduction, Conclusion, Results, Discussion, and Future Outlook sections
- **Fuzzy Matching** - Detects section variations like "Concluding Remarks", "Summary and Conclusions", "Perspectives"
- **DOI Extraction** - Automatically finds and includes clickable DOI links
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

## Usage

1. Place PDF files in the `pdfs/` directory
2. Run the extraction script:

```bash
python extract_sections.py
```

1. View results:
   - `extracted_sections.json` - Structured JSON output
   - `extracted_sections.md` - LLM-friendly markdown

## Example Output

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

## License

MIT
