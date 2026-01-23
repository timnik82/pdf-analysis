import json
import os
import re

import pymupdf4llm
from rapidfuzz import fuzz

# =============================================================================
# SECTION KEYWORDS FOR FUZZY MATCHING
# =============================================================================
SECTION_KEYWORDS = {
    "introduction": [
        "introduction",
        "background",
        "overview",
        "preface",
        "motivation",
        "background and motivation",
    ],
    "conclusion": [
        "conclusion",
        "conclusions",
        "concluding remarks",
        "summary",
        "summary and conclusions",
        "final remarks",
        "closing remarks",
        "general conclusions",
        "concluding notes",
    ],
    "future_outlook": [
        "future work",
        "future works",
        "future outlook",
        "future directions",
        "future research",
        "future perspectives",
        "future studies",
        "outlook",
        "perspectives",
        "outlook and perspectives",
        "perspectives and outlook",
        "open questions",
        "open challenges",
        "implications",
        "implications and future work",
        "roadmap",
    ],
    "results": ["results", "findings", "experimental results"],
    "discussion": ["discussion", "analysis", "results and discussion"],
}

# =============================================================================
# CONTENT-BASED DETECTION INDICATORS
# =============================================================================
CONCLUSION_INDICATORS = [
    "in conclusion",
    "to conclude",
    "in summary",
    "we have shown",
    "this study demonstrates",
    "our findings suggest",
    "we conclude",
    "this work has demonstrated",
    "the results demonstrate",
    "we have presented",
    "this paper has presented",
    "to summarize",
    "in this paper, we have",
    "our results show that",
    "we have demonstrated",
]

INTRODUCTION_INDICATORS = [
    "in this paper",
    "in this study",
    "in this work",
    "we present",
    "this paper presents",
    "the purpose of this",
    "the goal of this",
    "the aim of this",
    "this study aims",
    "we propose",
    "we introduce",
]

# =============================================================================
# CONTENT CLEANING PATTERNS
# =============================================================================
# Patterns to remove from extracted content (noise)
NOISE_PATTERNS = [
    r"^\s*[-*]?\s*Corresponding\s+author\.?.*$",  # Corresponding author lines
    r"^\s*\*{1,2}\s*Corresponding\s+author\.?.*$",  # ** Corresponding author
    r"^\s*E-?mail\s*:.*$",  # Email lines
    r"^\s*\[E-?mail\s+address:.*$",  # Markdown email links
    r"^\s*Tel\.?\s*:.*$",  # Phone lines
    r"^\s*Fax\s*:.*$",  # Fax lines
    r"^\s*https?://.*$",  # Standalone URLs (not DOI)
    r"^\s*\[https?://.*$",  # Markdown URL links
    r"^\s*\d{1,3}\s*$",  # Standalone page numbers (1-3 digits alone on a line)
    r"^\s*[A-Z]\.\s*[A-Z][a-z]+\s+et\s+al\..*$",  # Journal headers like "Q. Zhu et al. Nano Materials..."
    r"^.*\(\d{4}\)\s*\d+[-–]\d+\s*$",  # Journal citations like "Nano Materials Science 6 (2024) 115-138"
    r"^\s*#\d+[-–].*$",  # Address lines like "#08-03, 138634, Singapore"
    r"^\s*\d+\s+These\s+authors\s+contribute.*$",  # Author contribution notes
    r"^\s*Received\s+\d+.*$",  # Received date lines
    r"^\s*Available\s+online.*$",  # Available online lines
    r"^\s*\d{4}-\d{4}/.*$",  # ISSN/DOI lines like "2589-9651/©..."
    r"^\[BY-NC-ND\s+license.*$",  # License lines
]

# DOI extraction pattern
DOI_PATTERN = re.compile(
    r"(?:doi\s*[:/]?\s*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,}/[^\s]+)", re.IGNORECASE
)


def fuzzy_match_section(header_text, threshold=80):
    """
    Match header text to section type using fuzzy matching.
    Returns the section type if a match is found above threshold, else None.
    """
    # Clean the header text
    cleaned = re.sub(r"^[\d\.IVX]+\s*", "", header_text)  # Remove numbering
    cleaned = re.sub(r"[#*]+", "", cleaned).strip().lower()  # Remove markdown

    for section_type, keywords in SECTION_KEYWORDS.items():
        for keyword in keywords:
            ratio = fuzz.ratio(cleaned, keyword)
            partial_ratio = fuzz.partial_ratio(cleaned, keyword)
            if ratio >= threshold or partial_ratio >= threshold:
                return section_type
    return None


def extract_doi(text):
    """
    Extract DOI from text. Returns the first DOI found or None.
    """
    match = DOI_PATTERN.search(text)
    if match:
        doi = match.group(1)
        # Clean up trailing punctuation
        doi = re.sub(r"[.,;:)\]]+$", "", doi)
        return doi
    return None


def clean_content(text):
    """
    Remove noise from extracted content like 'Corresponding author' lines,
    email addresses, and other non-essential metadata.
    """
    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        is_noise = False
        for pattern in NOISE_PATTERNS:
            if re.match(pattern, line, re.IGNORECASE | re.MULTILINE):
                is_noise = True
                break
        if not is_noise:
            cleaned_lines.append(line)

    # Join and clean up excessive blank lines
    result = "\n".join(cleaned_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)  # Max 2 consecutive newlines
    return result.strip()


def detect_section_by_content(text, section_type="conclusion"):
    """
    Detect sections by content patterns when headers are missing or non-standard.
    Analyzes the last portion of the document for conclusion-like content.
    """
    indicators = (
        CONCLUSION_INDICATORS
        if section_type == "conclusion"
        else INTRODUCTION_INDICATORS
    )
    text_lower = text.lower()

    # Count indicator matches
    matches = sum(1 for indicator in indicators if indicator in text_lower)

    # If we have multiple strong indicators, it's likely that section type
    return matches >= 2


def extract_sections_from_markdown(markdown_text):
    """
    Parses markdown text to find specific sections like Introduction, Conclusion, etc.
    Returns a dictionary of section names and their content.

    Uses a three-pronged approach:
    1. Exact regex pattern matching (primary)
    2. Fuzzy matching fallback for non-standard headers
    3. Content-based detection for edge cases
    """
    sections = {}

    # =========================================================================
    # EXPANDED REGEX PATTERNS
    # =========================================================================
    target_headers = {
        "introduction": re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})(?:(?:\d+\.?|[IVX]+\.?)\s*)?"
            r"(?:Introduction|Background(?:\s+and\s+Motivation)?|Overview|Preface|Motivation)"
            r"(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        "conclusion": re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})(?:(?:\d+\.?|[IVX]+\.?)\s*)?"
            r"(?:Conclusions?|Concluding\s+Remarks?|Summary(?:\s+and\s+Conclusions?)?|"
            r"Final\s+Remarks?|Closing\s+Remarks?|General\s+Conclusions?|"
            r"Conclusions?\s+and\s+(?:Outlook|Future\s+(?:Work|Directions?))|"
            r"Summary\s+and\s+(?:Outlook|Perspectives?))"
            r"(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        "future_outlook": re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})(?:(?:\d+\.?|[IVX]+\.?)\s*)?"
            r"(?:Future\s+(?:Works?|Outlook|Directions?|Research|Perspectives?|Studies)|"
            r"Outlook(?:\s+and\s+(?:Perspectives?|Future\s+(?:Work|Directions?)))?|"
            r"Perspectives?(?:\s+and\s+(?:Outlook|Future\s+(?:Work|Directions?)))?|"
            r"(?:Open\s+)?(?:Questions|Challenges)(?:\s+and\s+(?:Outlook|Future\s+Directions?))?|"
            r"Implications(?:\s+and\s+Future\s+(?:Work|Directions?))?|Road\s*map|"
            r"What\'?s\s+Next|Looking\s+(?:Ahead|Forward))"
            r"(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        "results": re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})(?:(?:\d+\.?|[IVX]+\.?)\s*)?"
            r"(?:Results?|Findings|Experimental\s+Results?)"
            r"(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        "discussion": re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})(?:(?:\d+\.?|[IVX]+\.?)\s*)?"
            r"(?:Discussion|Analysis|Results?\s+and\s+Discussion)"
            r"(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
    }

    # Patterns for end-of-paper sections that should act as boundaries
    # (we don't extract these, but they terminate other sections)
    end_section_patterns = [
        re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})References?(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})Bibliography(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})Acknowledg(?:e)?ments?(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})Author\s+Contributions?(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})Declaration\s+of\s+(?:Competing\s+)?Interests?(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})Conflicts?\s+of\s+Interest(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})Funding(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})Supplementary\s+(?:Materials?|Information)(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"^(?:#+\s*)?(?:\*{0,2})Appendix(?:\*{0,2})\s*$",
            re.IGNORECASE | re.MULTILINE,
        ),
    ]

    # =========================================================================
    # FIND ALL BOUNDARIES (headers that delimit sections)
    # =========================================================================
    extracted_boundaries = []

    # Generic section pattern: "2. Graphene Properties" or "2.1. Synthesis"
    # Match numbered sections more broadly, then filter out false positives
    generic_section_pattern = re.compile(
        r"^(\d+\.)\s+([A-Z].{5,60})$",  # "2. Section Title" - starts with capital, 5-60 chars
        re.MULTILINE,
    )
    for match in generic_section_pattern.finditer(markdown_text):
        header = match.group(0)
        # Skip if it looks like a citation (contains "et al." or dates/journal info)
        if "et al" in header.lower():
            continue
        if re.search(r"\(\d{4}\)", header):  # Year in parentheses like (2024)
            continue
        if re.search(r"\d+[-–]\d+", header):  # Page ranges like 115-138
            continue
        # Skip if it's too short (likely false positive)
        if len(header.split()) < 2:
            continue
        extracted_boundaries.append((match.start(), "generic_section", header))

    for key, pattern in target_headers.items():
        for match in pattern.finditer(markdown_text):
            extracted_boundaries.append((match.start(), key, match.group()))

    # Also include standard markdown headers as boundaries, but filter aggressively
    header_pattern = re.compile(r"^#+\s*.+$", re.MULTILINE)
    for match in header_pattern.finditer(markdown_text):
        header_text = match.group()

        # Skip false positives
        header_content = re.sub(r"^#+\s*", "", header_text)  # Remove leading #'s

        # Skip if header starts with numbers (addresses like #08-03, page refs)
        if re.match(r"^\d", header_content):
            continue
        # Skip very short headers (likely noise)
        if len(header_content.strip()) < 4:
            continue
        # Skip headers that look like metadata (contain @, mailto:, http)
        if (
            "@" in header_content
            or "mailto:" in header_content
            or "http" in header_content
        ):
            continue

        # Try fuzzy matching on headers not captured by regex
        fuzzy_section = fuzzy_match_section(header_text)
        boundary_type = fuzzy_section if fuzzy_section else "markdown_header"
        extracted_boundaries.append((match.start(), boundary_type, header_text))

    # Add end-of-paper sections as boundaries (References, Acknowledgments, etc.)
    for pattern in end_section_patterns:
        for match in pattern.finditer(markdown_text):
            extracted_boundaries.append((match.start(), "end_section", match.group()))

    # Sort boundaries by position
    extracted_boundaries.sort(key=lambda x: x[0])

    # =========================================================================
    # EXTRACT CONTENT FOR EACH TARGET SECTION
    # =========================================================================
    sections_to_extract = [
        "introduction",
        "conclusion",
        "future_outlook",
        "results",
        "discussion",
    ]

    for key in sections_to_extract:
        pattern = target_headers[key]
        match = pattern.search(markdown_text)

        # If no regex match, try to find via fuzzy-matched boundaries
        if not match:
            for boundary_start, boundary_type, boundary_text in extracted_boundaries:
                if boundary_type == key:
                    # Create a pseudo-match using the boundary info
                    match_start = boundary_start
                    match_end = boundary_start + len(boundary_text)
                    break
            else:
                continue  # No match found for this section
        else:
            match_start = match.start()
            match_end = match.end()

        # Find the next boundary after this match
        end_index = len(markdown_text)

        for boundary_start, _boundary_type, _ in extracted_boundaries:
            if boundary_start > match_start + 10:  # Buffer to avoid self-match
                end_index = boundary_start
                break

        # Extract and clean content
        content = markdown_text[match_end if match else match_start : end_index].strip()

        # Filter out very short content (likely false positives)
        if len(content) > 50:
            sections[key] = content

    # =========================================================================
    # CONTENT-BASED FALLBACK DETECTION
    # =========================================================================
    # If we didn't find a conclusion, check the last part of the document
    if "conclusion" not in sections:
        # Get the last ~2000 characters
        last_portion = (
            markdown_text[-2000:] if len(markdown_text) > 2000 else markdown_text
        )
        if detect_section_by_content(last_portion, "conclusion"):
            # Extract from the last major paragraph break
            paragraphs = markdown_text.split("\n\n")
            if len(paragraphs) >= 3:
                sections["conclusion"] = "\n\n".join(paragraphs[-3:]).strip()
                sections["_conclusion_note"] = (
                    "Detected by content analysis (no explicit header found)"
                )

    return sections


def export_to_markdown(results, output_file):
    """
    Export extracted sections to a markdown file for LLM consumption.
    Creates a clean, structured markdown document with all papers and their sections.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Extracted Academic Paper Sections\n\n")
        f.write(f"Total papers processed: {len(results)}\n\n")
        f.write("---\n\n")

        for i, paper in enumerate(results, 1):
            filename = paper.get("filename", "Unknown")
            # Clean up filename for display
            display_name = filename.replace(".pdf", "").replace("-annotated", "")

            f.write(f"# Paper {i}: {display_name}\n\n")

            # Add DOI link if available
            if "doi" in paper and paper["doi"]:
                doi = paper["doi"]
                f.write(f"**DOI:** [https://doi.org/{doi}](https://doi.org/{doi})\n\n")

            # Write each section in a standardized order
            section_order = [
                "introduction",
                "results",
                "discussion",
                "conclusion",
                "future_outlook",
            ]
            section_titles = {
                "introduction": "Introduction",
                "results": "Results",
                "discussion": "Discussion",
                "conclusion": "Conclusion",
                "future_outlook": "Future Outlook",
            }

            sections_found = []
            for section_key in section_order:
                if section_key in paper and not section_key.startswith("_"):
                    sections_found.append(section_key)
                    f.write(f"## {section_titles[section_key]}\n\n")
                    f.write(paper[section_key])
                    f.write("\n\n")

                    # Add note if section was detected by content analysis
                    note_key = f"_{section_key}_note"
                    if note_key in paper:
                        f.write(f"*Note: {paper[note_key]}*\n\n")

            if not sections_found:
                f.write("*No sections extracted from this paper.*\n\n")

            f.write("---\n\n")

    print(f"Markdown export saved to {output_file}")


def process_pdfs(pdf_dir, output_file):
    """
    Iterates through PDFs in pdf_dir, converts them to MD, extracts sections,
    and saves results to both JSON and Markdown formats.
    """
    results = []

    if not os.path.isdir(pdf_dir):
        print(f"Error: Directory {pdf_dir} does not exist.")
        return

    print(f"Processing PDFs in {pdf_dir}...")

    files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]

    if not files:
        print("No PDF files found.")
        return

    for filename in files:
        filepath = os.path.join(pdf_dir, filename)
        print(f"Processing {filename}...")

        try:
            # Convert PDF to Markdown using pymupdf4llm
            md_text = pymupdf4llm.to_markdown(filepath)

            # Extract DOI from the full text (usually in first pages)
            doi = extract_doi(md_text[:5000])  # Check first ~5000 chars

            # Extract specific sections
            extracted_data = extract_sections_from_markdown(md_text)

            # Clean content in all sections
            for key in list(extracted_data.keys()):
                if key not in ["filename", "doi"] and not key.startswith("_"):
                    extracted_data[key] = clean_content(extracted_data[key])

            # Add metadata
            extracted_data["filename"] = filename
            if doi:
                extracted_data["doi"] = doi

            results.append(extracted_data)
            section_keys = [
                k
                for k in extracted_data.keys()
                if not k.startswith("_") and k not in ["filename", "doi"]
            ]
            print(f"  Found sections: {section_keys}")

        except Exception as e:
            print(f"  Error processing {filename}: {e}")

    # Determine output path: if output_file contains no directory, place it inside pdf_dir
    output_dir_part = os.path.dirname(output_file)
    if output_dir_part:
        output_path = output_file
    else:
        output_path = os.path.join(pdf_dir, output_file)

    # Ensure parent directory exists (if caller provided a path)
    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    # Save to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nJSON extraction saved to {output_path}")

    # Save to Markdown for LLM consumption (same folder as JSON)
    markdown_file = output_path.replace(".json", ".md")
    export_to_markdown(results, markdown_file)

    print("\n✓ Extraction complete. Output files:")
    print(f"  - {output_path} (JSON, for programmatic access)")
    print(f"  - {markdown_file} (Markdown, for LLM analysis)")


if __name__ == "__main__":
    # Configuration
    PDF_DIRECTORY = "pdfs"
    OUTPUT_JSON = "extracted_sections.json"

    process_pdfs(PDF_DIRECTORY, OUTPUT_JSON)
