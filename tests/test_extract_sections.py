"""
Tests for extract_sections.py
"""

from extract_sections import (
    clean_content,
    detect_section_by_content,
    extract_doi,
    extract_sections_from_markdown,
    fuzzy_match_section,
)


class TestFuzzyMatchSection:
    """Tests for fuzzy_match_section function"""

    def test_exact_match_introduction(self):
        """Test exact match for introduction"""
        result = fuzzy_match_section("Introduction")
        assert result == "introduction"

    def test_exact_match_conclusion(self):
        """Test exact match for conclusion"""
        result = fuzzy_match_section("Conclusion")
        assert result == "conclusion"

    def test_numbered_section_introduction(self):
        """Test numbered section like '1. Introduction'"""
        result = fuzzy_match_section("1. Introduction")
        assert result == "introduction"

    def test_numbered_section_conclusion(self):
        """Test numbered section like '5. Conclusions'"""
        result = fuzzy_match_section("5. Conclusions")
        assert result == "conclusion"

    def test_markdown_header_introduction(self):
        """Test markdown header like '## Introduction'"""
        result = fuzzy_match_section("## Introduction")
        assert result == "introduction"

    def test_variation_concluding_remarks(self):
        """Test variation 'Concluding Remarks'"""
        result = fuzzy_match_section("Concluding Remarks")
        assert result == "conclusion"

    def test_variation_future_work(self):
        """Test variation 'Future Work'"""
        result = fuzzy_match_section("Future Work")
        assert result == "future_outlook"

    def test_variation_outlook(self):
        """Test variation 'Outlook'"""
        result = fuzzy_match_section("Outlook")
        assert result == "future_outlook"

    def test_case_insensitive(self):
        """Test case insensitivity"""
        result = fuzzy_match_section("INTRODUCTION")
        assert result == "introduction"

    def test_no_match_returns_none(self):
        """Test that non-matching headers return None"""
        result = fuzzy_match_section("Methods")
        assert result is None

    def test_low_similarity_returns_none(self):
        """Test that low similarity returns None"""
        result = fuzzy_match_section("Random Text")
        assert result is None


class TestExtractDoi:
    """Tests for extract_doi function"""

    def test_extract_doi_with_doi_prefix(self):
        """Test extracting DOI with 'doi:' prefix"""
        text = "doi:10.1038/nature12345"
        result = extract_doi(text)
        assert result == "10.1038/nature12345"

    def test_extract_doi_with_url(self):
        """Test extracting DOI from URL"""
        text = "https://doi.org/10.1126/science.abc123"
        result = extract_doi(text)
        assert result == "10.1126/science.abc123"

    def test_extract_doi_dx_url(self):
        """Test extracting DOI from dx.doi.org URL"""
        text = "http://dx.doi.org/10.1371/journal.pone.0123456"
        result = extract_doi(text)
        assert result == "10.1371/journal.pone.0123456"

    def test_extract_doi_plain(self):
        """Test extracting plain DOI"""
        text = "The DOI is 10.1016/j.cell.2023.01.001 for reference."
        result = extract_doi(text)
        assert result == "10.1016/j.cell.2023.01.001"

    def test_extract_doi_with_trailing_punctuation(self):
        """Test DOI extraction removes trailing punctuation"""
        text = "DOI: 10.1038/nature12345."
        result = extract_doi(text)
        assert result == "10.1038/nature12345"

    def test_extract_doi_with_multiple_slashes(self):
        """Test DOI with multiple slashes"""
        text = "doi:10.1234/abc/def/123"
        result = extract_doi(text)
        assert result == "10.1234/abc/def/123"

    def test_no_doi_returns_none(self):
        """Test that text without DOI returns None"""
        text = "This is some random text without a DOI"
        result = extract_doi(text)
        assert result is None

    def test_extract_first_doi_when_multiple(self):
        """Test extracting first DOI when multiple are present"""
        text = "First DOI: 10.1038/nature12345 and second DOI: 10.1126/science.abc123"
        result = extract_doi(text)
        assert result == "10.1038/nature12345"


class TestCleanContent:
    """Tests for clean_content function"""

    def test_remove_corresponding_author(self):
        """Test removal of 'Corresponding author' lines"""
        text = "Some content\n* Corresponding author.\nMore content"
        result = clean_content(text)
        assert "Corresponding author" not in result
        assert "Some content" in result
        assert "More content" in result

    def test_remove_email_lines(self):
        """Test removal of email lines"""
        text = "Some content\nE-mail: test@example.com\nMore content"
        result = clean_content(text)
        assert "E-mail" not in result
        assert "test@example.com" not in result

    def test_remove_standalone_page_numbers(self):
        """Test removal of standalone page numbers"""
        text = "Some content\n42\nMore content"
        result = clean_content(text)
        assert result == "Some content\nMore content"

    def test_remove_journal_headers(self):
        """Test removal of journal header lines"""
        text = "Some content\nQ. Zhu et al. Nano Materials Science 6 (2024) 115-138\nMore content"
        result = clean_content(text)
        assert "Nano Materials Science" not in result

    def test_remove_received_date_lines(self):
        """Test removal of 'Received' date lines"""
        text = "Some content\nReceived 15 January 2024\nMore content"
        result = clean_content(text)
        assert "Received" not in result

    def test_remove_available_online_lines(self):
        """Test removal of 'Available online' lines"""
        text = "Some content\nAvailable online 20 January 2024\nMore content"
        result = clean_content(text)
        assert "Available online" not in result

    def test_reduce_excessive_blank_lines(self):
        """Test reduction of excessive blank lines"""
        text = "Some content\n\n\n\n\nMore content"
        result = clean_content(text)
        assert result == "Some content\n\nMore content"

    def test_preserve_important_content(self):
        """Test that important content is preserved"""
        text = "Introduction\n\nThis paper presents important findings.\n\nWe conclude that..."
        result = clean_content(text)
        assert "Introduction" in result
        assert "important findings" in result
        assert "We conclude" in result

    def test_empty_text_returns_empty(self):
        """Test that empty text returns empty string"""
        result = clean_content("")
        assert result == ""


class TestDetectSectionByContent:
    """Tests for detect_section_by_content function"""

    def test_detect_conclusion_with_multiple_indicators(self):
        """Test conclusion detection with multiple indicators"""
        text = "In conclusion, we have shown that this approach works. Our findings suggest significant improvements."
        result = detect_section_by_content(text, "conclusion")
        assert result is True

    def test_detect_conclusion_with_single_indicator(self):
        """Test conclusion detection with single indicator returns False"""
        text = "In conclusion, we present our findings."
        result = detect_section_by_content(text, "conclusion")
        assert result is False

    def test_detect_introduction_with_multiple_indicators(self):
        """Test introduction detection with multiple indicators"""
        text = "In this paper, we present a new method. We propose a novel approach."
        result = detect_section_by_content(text, "introduction")
        assert result is True

    def test_no_indicators_returns_false(self):
        """Test that text without indicators returns False"""
        text = "This is some random text without any section indicators."
        result = detect_section_by_content(text, "conclusion")
        assert result is False

    def test_case_insensitive_detection(self):
        """Test case insensitive indicator detection"""
        text = (
            "IN CONCLUSION, we have demonstrated the method. WE CONCLUDE that it works."
        )
        result = detect_section_by_content(text, "conclusion")
        assert result is True


class TestExtractSectionsFromMarkdown:
    """Tests for extract_sections_from_markdown function"""

    def test_extract_introduction_section(self):
        """Test extracting introduction section"""
        markdown = """
# Introduction

This is the introduction text with enough content to pass the minimum length threshold for section extraction.

# Methods

This is the methods section with more content.
"""
        result = extract_sections_from_markdown(markdown)
        assert "introduction" in result
        assert "introduction text" in result["introduction"]

    def test_extract_conclusion_section(self):
        """Test extracting conclusion section"""
        markdown = """
# Results

Some results here with enough content to be meaningful.

# Conclusion

This is the conclusion text with sufficient content to pass the minimum length filter.

# References
"""
        result = extract_sections_from_markdown(markdown)
        assert "conclusion" in result
        assert "conclusion text" in result["conclusion"]

    def test_extract_multiple_sections(self):
        """Test extracting multiple sections"""
        markdown = """
# Introduction

Introduction content with enough text to pass the length filter for meaningful content.

# Results

Results content with sufficient detail to be extracted properly by the function.

# Conclusion

Conclusion content that is long enough to meet the minimum requirements for extraction.
"""
        result = extract_sections_from_markdown(markdown)
        assert "introduction" in result
        assert "results" in result
        assert "conclusion" in result

    def test_numbered_sections(self):
        """Test extracting numbered sections like '1. Introduction'"""
        markdown = """
1. Introduction

Introduction content with enough detail to be properly extracted and processed.

2. Methods

Methods content that provides enough information for the test case to work.

3. Conclusion

Conclusion content with sufficient length to pass the minimum threshold requirements.
"""
        result = extract_sections_from_markdown(markdown)
        assert "introduction" in result
        assert "conclusion" in result

    def test_section_boundaries_stop_at_references(self):
        """Test that sections stop at References"""
        markdown = """
# Conclusion

Conclusion content here with enough text to pass the minimum length filter for extraction.

# References

1. Author et al. (2023)
2. Another Author et al. (2024)
"""
        result = extract_sections_from_markdown(markdown)
        assert "conclusion" in result
        assert "References" not in result["conclusion"]

    def test_filter_very_short_content(self):
        """Test that very short content is filtered out"""
        markdown = """
# Introduction

Short

# Methods

Much longer content that should be included because it exceeds the minimum length threshold.
"""
        result = extract_sections_from_markdown(markdown)
        # Very short sections (< 50 chars) should be filtered
        assert "introduction" not in result

    def test_empty_markdown_returns_empty_dict(self):
        """Test empty markdown returns empty dictionary"""
        result = extract_sections_from_markdown("")
        assert result == {}

    def test_future_outlook_variations(self):
        """Test different future outlook section names"""
        markdown1 = "# Future Work\n\nFuture work content with enough detail to be properly extracted."
        markdown2 = "# Outlook\n\nOutlook content with sufficient length for extraction requirements."

        result1 = extract_sections_from_markdown(markdown1)
        result2 = extract_sections_from_markdown(markdown2)

        assert "future_outlook" in result1
        assert "future_outlook" in result2
