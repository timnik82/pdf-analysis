"""
Tests for extract_and_check_dois.py
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from extract_and_check_dois import (
    extract_dois_from_markdown,
    generate_html_table,
    load_firebase_config,
)


class TestExtractDoisFromMarkdown:
    """Tests for extract_dois_from_markdown function"""

    def test_extract_doi_from_url(self, tmp_path):
        """Test extracting DOI from full URL"""
        md_file = tmp_path / "test.md"
        md_file.write_text("Check this paper: https://doi.org/10.1038/nature12345")

        dois = extract_dois_from_markdown(str(md_file))

        assert len(dois) == 1
        assert "10.1038/nature12345" in dois

    def test_extract_doi_from_markdown_link(self, tmp_path):
        """Test extracting DOI from markdown link text"""
        md_file = tmp_path / "test.md"
        md_file.write_text("[10.1038/nature12345](https://doi.org/10.1038/nature12345)")

        dois = extract_dois_from_markdown(str(md_file))

        assert len(dois) == 1
        assert "10.1038/nature12345" in dois

    def test_extract_doi_with_doi_prefix(self, tmp_path):
        """Test extracting DOI with DOI: prefix"""
        md_file = tmp_path / "test.md"
        md_file.write_text("DOI: 10.1126/science.abc123")

        dois = extract_dois_from_markdown(str(md_file))

        assert len(dois) == 1
        assert "10.1126/science.abc123" in dois

    def test_extract_multiple_dois(self, tmp_path):
        """Test extracting multiple DOIs from a file"""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            "Paper 1: https://doi.org/10.1038/nature12345\n"
            "Paper 2: DOI: 10.1126/science.abc123\n"
            "Paper 3: [10.1016/j.cell.2023.01.001](https://doi.org/10.1016/j.cell.2023.01.001)"
        )

        dois = extract_dois_from_markdown(str(md_file))

        assert len(dois) == 3
        assert "10.1038/nature12345" in dois
        assert "10.1126/science.abc123" in dois
        assert "10.1016/j.cell.2023.01.001" in dois

    def test_deduplicate_dois(self, tmp_path):
        """Test that duplicate DOIs are removed"""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            "https://doi.org/10.1038/nature12345\n"
            "DOI: 10.1038/nature12345\n"
            "[10.1038/nature12345](https://doi.org/10.1038/nature12345)"
        )

        dois = extract_dois_from_markdown(str(md_file))

        assert len(dois) == 1
        assert "10.1038/nature12345" in dois

    def test_empty_file_returns_empty_list(self, tmp_path):
        """Test that empty file returns empty list"""
        md_file = tmp_path / "test.md"
        md_file.write_text("")

        dois = extract_dois_from_markdown(str(md_file))

        assert dois == []

    def test_no_dois_returns_empty_list(self, tmp_path):
        """Test that file without DOIs returns empty list"""
        md_file = tmp_path / "test.md"
        md_file.write_text("This is just some random text without any DOIs.")

        dois = extract_dois_from_markdown(str(md_file))

        assert dois == []


class TestLoadFirebaseConfig:
    """Tests for load_firebase_config function"""

    def test_load_valid_config(self, tmp_path, monkeypatch):
        """Test loading valid Firebase config"""
        config = {
            "apiKey": "test-api-key",
            "authDomain": "test.firebaseapp.com",
            "projectId": "test-project",
        }
        config_file = tmp_path / "firebase-config.json"
        config_file.write_text(json.dumps(config))

        # Patch the function to look in tmp_path
        monkeypatch.setattr(
            "extract_and_check_dois.Path.__file__",
            str(tmp_path / "extract_and_check_dois.py"),
        )

        with patch.object(Path, "resolve") as mock_resolve:
            mock_resolve.return_value.parent = tmp_path
            result = load_firebase_config()

        assert result == config

    def test_missing_config_raises_error(self, tmp_path):
        """Test that missing config file raises FileNotFoundError"""
        with patch.object(Path, "resolve") as mock_resolve:
            mock_resolve.return_value.parent = tmp_path

            with pytest.raises(FileNotFoundError) as excinfo:
                load_firebase_config()

            assert "Firebase config not found" in str(excinfo.value)


class TestGenerateHtmlTable:
    """Tests for generate_html_table function"""

    def test_generate_html_with_mock_banner(self, tmp_path):
        """Test that mock banner appears when is_mock is True"""
        results = {
            "summary": {
                "total_checked": 2,
                "found_in_library": 0,
                "not_in_library": 2,
            },
            "in_library": [],
            "not_in_library": ["10.1038/nature12345", "10.1126/science.abc123"],
            "is_mock": True,
        }
        output_file = tmp_path / "output.html"

        with patch("extract_and_check_dois.load_firebase_config") as mock_config:
            mock_config.side_effect = FileNotFoundError("Not found")
            generate_html_table(results, str(output_file))

        html_content = output_file.read_text()
        assert "DEMO MODE" in html_content
        assert "Data verification skipped" in html_content

    def test_generate_html_without_mock_banner(self, tmp_path):
        """Test that mock banner does not appear when is_mock is False/missing"""
        results = {
            "summary": {
                "total_checked": 2,
                "found_in_library": 1,
                "not_in_library": 1,
            },
            "in_library": [
                {"doi": "10.1038/nature12345", "title": "Test Paper", "year": 2023}
            ],
            "not_in_library": ["10.1126/science.abc123"],
        }
        output_file = tmp_path / "output.html"

        with patch("extract_and_check_dois.load_firebase_config") as mock_config:
            mock_config.side_effect = FileNotFoundError("Not found")
            generate_html_table(results, str(output_file))

        html_content = output_file.read_text()
        assert "DEMO MODE" not in html_content

    def test_generate_html_with_firebase_config(self, tmp_path):
        """Test that Firebase script is included when config is available"""
        results = {
            "summary": {
                "total_checked": 1,
                "found_in_library": 0,
                "not_in_library": 1,
            },
            "in_library": [],
            "not_in_library": ["10.1038/nature12345"],
        }
        output_file = tmp_path / "output.html"
        firebase_config = {
            "apiKey": "test-key",
            "projectId": "test-project",
            "databaseURL": "https://test.firebasedatabase.app",
        }

        with patch("extract_and_check_dois.load_firebase_config") as mock_config:
            mock_config.return_value = firebase_config
            generate_html_table(results, str(output_file))

        html_content = output_file.read_text()
        assert "initializeApp" in html_content
        assert "signInAnonymously" in html_content
        assert "test-key" in html_content

    def test_generate_html_fallback_to_localstorage(self, tmp_path):
        """Test fallback to localStorage when Firebase config is missing"""
        results = {
            "summary": {
                "total_checked": 1,
                "found_in_library": 0,
                "not_in_library": 1,
            },
            "in_library": [],
            "not_in_library": ["10.1038/nature12345"],
        }
        output_file = tmp_path / "output.html"

        with patch("extract_and_check_dois.load_firebase_config") as mock_config:
            mock_config.side_effect = FileNotFoundError("Not found")
            generate_html_table(results, str(output_file))

        html_content = output_file.read_text()
        assert "localStorage" in html_content
        assert "Local storage mode" in html_content
        assert "initializeApp" not in html_content

    def test_auth_status_inside_container(self, tmp_path):
        """Test that auth-status div is inside the container"""
        results = {
            "summary": {
                "total_checked": 1,
                "found_in_library": 0,
                "not_in_library": 1,
            },
            "in_library": [],
            "not_in_library": ["10.1038/nature12345"],
        }
        output_file = tmp_path / "output.html"

        with patch("extract_and_check_dois.load_firebase_config") as mock_config:
            mock_config.side_effect = FileNotFoundError("Not found")
            generate_html_table(results, str(output_file))

        html_content = output_file.read_text()
        # Check that auth-status appears after container opening but before h1
        container_pos = html_content.find('<div class="container">')
        auth_status_pos = html_content.find('id="auth-status"')
        h1_pos = html_content.find("<h1>")
        closing_container_pos = html_content.find("</div>\n\n    <script")

        assert container_pos < auth_status_pos < h1_pos
        assert auth_status_pos < closing_container_pos


class TestDoiKeySanitization:
    """Tests for DOI key sanitization for Firebase compatibility"""

    def test_doi_key_sanitization_in_html(self, tmp_path):
        """Test that DOI keys are sanitized for Firebase (no dots)"""
        # DOIs with dots that need to be replaced
        results = {
            "summary": {
                "total_checked": 1,
                "found_in_library": 0,
                "not_in_library": 1,
            },
            "in_library": [],
            "not_in_library": ["10.1038/nature.12345"],
        }
        output_file = tmp_path / "output.html"

        with patch("extract_and_check_dois.load_firebase_config") as mock_config:
            mock_config.side_effect = FileNotFoundError("Not found")
            generate_html_table(results, str(output_file))

        html_content = output_file.read_text()
        # The checkbox id should have dots and slashes replaced with underscores
        assert 'id="check_10_1038_nature_12345"' in html_content
        # Original DOI should still be displayed
        assert "10.1038/nature.12345" in html_content

    def test_special_characters_in_doi(self, tmp_path):
        """Test handling of special characters in DOIs"""
        results = {
            "summary": {
                "total_checked": 1,
                "found_in_library": 0,
                "not_in_library": 1,
            },
            "in_library": [],
            "not_in_library": ["10.1000/xyz#abc"],
        }
        output_file = tmp_path / "output.html"

        with patch("extract_and_check_dois.load_firebase_config") as mock_config:
            mock_config.side_effect = FileNotFoundError("Not found")
            generate_html_table(results, str(output_file))

        html_content = output_file.read_text()
        # Dots and slashes replaced with underscores, other special chars URL-encoded
        assert 'id="check_10_1000_xyz%23abc"' in html_content
