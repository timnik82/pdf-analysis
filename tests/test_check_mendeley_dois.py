"""
Tests for check_mendeley_dois_v2.py
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, mock_open
from check_mendeley_dois_v2 import (
    check_dois,
    fetch_library_dois,
    print_results,
    save_results
)


class TestCheckDois:
    """Tests for check_dois function"""
    
    def test_check_dois_all_found(self):
        """Test checking DOIs when all are in library"""
        dois_to_check = ["10.1038/nature12345", "10.1126/science.abc123"]
        library_docs = {
            "10.1038/nature12345": {
                "doi": "10.1038/nature12345",
                "title": "Test Paper 1",
                "year": 2023
            },
            "10.1126/science.abc123": {
                "doi": "10.1126/science.abc123",
                "title": "Test Paper 2",
                "year": 2024
            }
        }
        
        found_docs, missing_dois = check_dois(dois_to_check, library_docs)
        
        assert len(found_docs) == 2
        assert len(missing_dois) == 0
        assert found_docs[0]["doi"] == "10.1038/nature12345"
        assert found_docs[1]["doi"] == "10.1126/science.abc123"
    
    def test_check_dois_all_missing(self):
        """Test checking DOIs when none are in library"""
        dois_to_check = ["10.1038/nature99999", "10.1126/science.xyz999"]
        library_docs = {
            "10.1038/nature12345": {
                "doi": "10.1038/nature12345",
                "title": "Test Paper 1",
                "year": 2023
            }
        }
        
        found_docs, missing_dois = check_dois(dois_to_check, library_docs)
        
        assert len(found_docs) == 0
        assert len(missing_dois) == 2
        assert "10.1038/nature99999" in missing_dois
        assert "10.1126/science.xyz999" in missing_dois
    
    def test_check_dois_mixed_results(self):
        """Test checking DOIs with mixed results"""
        dois_to_check = ["10.1038/nature12345", "10.1126/science.xyz999"]
        library_docs = {
            "10.1038/nature12345": {
                "doi": "10.1038/nature12345",
                "title": "Test Paper 1",
                "year": 2023
            }
        }
        
        found_docs, missing_dois = check_dois(dois_to_check, library_docs)
        
        assert len(found_docs) == 1
        assert len(missing_dois) == 1
        assert found_docs[0]["doi"] == "10.1038/nature12345"
        assert "10.1126/science.xyz999" in missing_dois
    
    def test_check_dois_case_insensitive(self):
        """Test that DOI matching is case-insensitive"""
        dois_to_check = ["10.1038/NATURE12345"]  # Uppercase
        library_docs = {
            "10.1038/nature12345": {  # Lowercase in library
                "doi": "10.1038/nature12345",
                "title": "Test Paper 1",
                "year": 2023
            }
        }
        
        found_docs, missing_dois = check_dois(dois_to_check, library_docs)
        
        assert len(found_docs) == 1
        assert len(missing_dois) == 0
    
    def test_check_dois_strips_whitespace(self):
        """Test that DOIs are stripped of whitespace"""
        dois_to_check = [" 10.1038/nature12345 ", "10.1126/science.abc123  "]
        library_docs = {
            "10.1038/nature12345": {
                "doi": "10.1038/nature12345",
                "title": "Test Paper 1",
                "year": 2023
            }
        }
        
        found_docs, missing_dois = check_dois(dois_to_check, library_docs)
        
        assert len(found_docs) == 1
        assert "10.1126/science.abc123" in missing_dois
    
    def test_check_dois_empty_list(self):
        """Test checking empty DOI list"""
        dois_to_check = []
        library_docs = {
            "10.1038/nature12345": {
                "doi": "10.1038/nature12345",
                "title": "Test Paper 1",
                "year": 2023
            }
        }
        
        found_docs, missing_dois = check_dois(dois_to_check, library_docs)
        
        assert len(found_docs) == 0
        assert len(missing_dois) == 0


class TestFetchLibraryDois:
    """Tests for fetch_library_dois function"""
    
    @patch('check_mendeley_dois_v2.requests.get')
    def test_fetch_library_dois_single_page(self, mock_get):
        """Test fetching library DOIs with single page of results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "doc1",
                "title": "Test Paper 1",
                "year": 2023,
                "authors": [{"last_name": "Smith"}],
                "identifiers": {"doi": "10.1038/nature12345"}
            },
            {
                "id": "doc2",
                "title": "Test Paper 2",
                "year": 2024,
                "authors": [{"last_name": "Jones"}],
                "identifiers": {"doi": "10.1126/science.abc123"}
            }
        ]
        mock_response.links = {}  # No pagination
        mock_get.return_value = mock_response
        
        result = fetch_library_dois("fake_token")
        
        assert len(result) == 2
        assert "10.1038/nature12345" in result
        assert "10.1126/science.abc123" in result
        assert result["10.1038/nature12345"]["title"] == "Test Paper 1"
        assert result["10.1126/science.abc123"]["title"] == "Test Paper 2"
    
    @patch('check_mendeley_dois_v2.requests.get')
    def test_fetch_library_dois_skip_documents_without_doi(self, mock_get):
        """Test that documents without DOIs are skipped"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "doc1",
                "title": "Test Paper 1",
                "year": 2023,
                "identifiers": {"doi": "10.1038/nature12345"}
            },
            {
                "id": "doc2",
                "title": "Test Paper 2 - No DOI",
                "year": 2024,
                "identifiers": {}  # No DOI
            },
            {
                "id": "doc3",
                "title": "Test Paper 3",
                "year": 2024,
                "identifiers": {"doi": ""}  # Empty DOI
            }
        ]
        mock_response.links = {}  # No pagination
        mock_get.return_value = mock_response
        
        result = fetch_library_dois("fake_token")
        
        # Only doc1 should be included
        assert len(result) == 1
        assert "10.1038/nature12345" in result
    
    @patch('check_mendeley_dois_v2.requests.get')
    def test_fetch_library_dois_case_insensitive_storage(self, mock_get):
        """Test that DOIs are stored in lowercase for case-insensitive matching"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": "doc1",
                "title": "Test Paper",
                "identifiers": {"doi": "10.1038/NATURE12345"}  # Mixed case
            }
        ]
        mock_response.links = {}  # No pagination
        mock_get.return_value = mock_response
        
        result = fetch_library_dois("fake_token")
        
        # Should be stored with lowercase key
        assert "10.1038/nature12345" in result
        # But original case preserved in value
        assert result["10.1038/nature12345"]["doi"] == "10.1038/NATURE12345"
    
    @patch('check_mendeley_dois_v2.requests.get')
    def test_fetch_library_dois_handles_api_error(self, mock_get):
        """Test that API errors are handled properly"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception) as excinfo:
            fetch_library_dois("fake_token")
        
        assert "Failed to fetch documents" in str(excinfo.value)
    
    @patch('check_mendeley_dois_v2.requests.get')
    def test_fetch_library_dois_pagination(self, mock_get):
        """Test that pagination works correctly with multiple pages"""
        # First page response
        first_response = Mock()
        first_response.status_code = 200
        first_response.json.return_value = [
            {
                "id": "doc1",
                "title": "Paper 1",
                "year": 2023,
                "identifiers": {"doi": "10.1038/nature11111"}
            },
            {
                "id": "doc2",
                "title": "Paper 2",
                "year": 2023,
                "identifiers": {"doi": "10.1038/nature22222"}
            }
        ]
        # Set response.links with next page URL
        first_response.links = {'next': {'url': 'https://api.mendeley.com/documents?limit=100&marker=next_page_marker'}}
        
        # Second page response
        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = [
            {
                "id": "doc3",
                "title": "Paper 3",
                "year": 2024,
                "identifiers": {"doi": "10.1038/nature33333"}
            }
        ]
        # No next link on last page
        second_response.links = {}
        
        # Mock returns different responses on subsequent calls
        mock_get.side_effect = [first_response, second_response]
        
        result = fetch_library_dois("fake_token")
        
        # Should have collected DOIs from both pages
        assert len(result) == 3
        assert "10.1038/nature11111" in result
        assert "10.1038/nature22222" in result
        assert "10.1038/nature33333" in result
        assert result["10.1038/nature11111"]["title"] == "Paper 1"
        assert result["10.1038/nature33333"]["title"] == "Paper 3"
        
        # Verify requests.get was called twice (once per page)
        assert mock_get.call_count == 2
    
    @patch('check_mendeley_dois_v2.requests.get')
    def test_fetch_library_dois_pagination_multiple_links(self, mock_get):
        """Test pagination with multiple links in Link header"""
        # Response with multiple links in Link header
        response = Mock()
        response.status_code = 200
        response.json.return_value = [
            {
                "id": "doc1",
                "title": "Paper 1",
                "identifiers": {"doi": "10.1038/nature12345"}
            }
        ]
        # response.links with next page (this is how requests parses Link headers)
        response.links = {'next': {'url': 'https://api.mendeley.com/documents?limit=100&marker=next_marker'}}
        
        # Second response without next link
        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = []
        second_response.links = {}  # No next link
        
        mock_get.side_effect = [response, second_response]
        
        result = fetch_library_dois("fake_token")
        
        # Should parse the 'next' link correctly even with multiple links
        assert len(result) == 1
        assert mock_get.call_count == 2
        # Verify second call used the extracted next URL
        second_call_url = mock_get.call_args_list[1][0][0]
        assert 'next_marker' in second_call_url


class TestSaveResults:
    """Tests for save_results function"""
    
    def test_save_results_creates_correct_structure(self, tmp_path):
        """Test that save_results creates correct JSON structure"""
        output_file = tmp_path / "results.json"
        
        dois_checked = ["10.1038/nature12345", "10.1126/science.abc123"]
        found_docs = [
            {
                "doi": "10.1038/nature12345",
                "title": "Test Paper 1",
                "year": 2023,
                "id": "doc1"
            }
        ]
        missing_dois = ["10.1126/science.abc123"]
        
        save_results(dois_checked, found_docs, missing_dois, str(output_file))
        
        # Read the saved file
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        assert result["summary"]["total_checked"] == 2
        assert result["summary"]["found_in_library"] == 1
        assert result["summary"]["not_in_library"] == 1
        assert len(result["in_library"]) == 1
        assert len(result["not_in_library"]) == 1
        assert result["in_library"][0]["doi"] == "10.1038/nature12345"
        assert "10.1126/science.abc123" in result["not_in_library"]
    
    def test_save_results_all_found(self, tmp_path):
        """Test save_results when all DOIs are found"""
        output_file = tmp_path / "results.json"
        
        dois_checked = ["10.1038/nature12345", "10.1126/science.abc123"]
        found_docs = [
            {"doi": "10.1038/nature12345", "title": "Paper 1", "year": 2023, "id": "doc1"},
            {"doi": "10.1126/science.abc123", "title": "Paper 2", "year": 2024, "id": "doc2"}
        ]
        missing_dois = []
        
        save_results(dois_checked, found_docs, missing_dois, str(output_file))
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        assert result["summary"]["total_checked"] == 2
        assert result["summary"]["found_in_library"] == 2
        assert result["summary"]["not_in_library"] == 0
        assert len(result["not_in_library"]) == 0
    
    def test_save_results_none_found(self, tmp_path):
        """Test save_results when no DOIs are found"""
        output_file = tmp_path / "results.json"
        
        dois_checked = ["10.1038/nature99999", "10.1126/science.xyz999"]
        found_docs = []
        missing_dois = ["10.1038/nature99999", "10.1126/science.xyz999"]
        
        save_results(dois_checked, found_docs, missing_dois, str(output_file))
        
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        assert result["summary"]["total_checked"] == 2
        assert result["summary"]["found_in_library"] == 0
        assert result["summary"]["not_in_library"] == 2
        assert len(result["in_library"]) == 0


class TestPrintResults:
    """Tests for print_results function"""
    
    def test_print_results_with_found_and_missing(self, capsys):
        """Test print_results with both found and missing DOIs"""
        dois_checked = ["10.1038/nature12345", "10.1126/science.abc123"]
        found_docs = [
            {
                "doi": "10.1038/nature12345",
                "title": "Test Paper 1",
                "year": 2023,
                "authors": [{"last_name": "Smith"}, {"last_name": "Jones"}]
            }
        ]
        missing_dois = ["10.1126/science.abc123"]
        
        print_results(dois_checked, found_docs, missing_dois)
        
        captured = capsys.readouterr()
        assert "Checked 2 DOIs" in captured.out
        assert "ALREADY IN LIBRARY (1)" in captured.out
        assert "NOT IN LIBRARY (1)" in captured.out
        assert "10.1038/nature12345" in captured.out
        assert "10.1126/science.abc123" in captured.out
        assert "Test Paper 1" in captured.out
    
    def test_print_results_all_found(self, capsys):
        """Test print_results when all DOIs are found"""
        dois_checked = ["10.1038/nature12345"]
        found_docs = [
            {
                "doi": "10.1038/nature12345",
                "title": "Test Paper 1",
                "year": 2023,
                "authors": []
            }
        ]
        missing_dois = []
        
        print_results(dois_checked, found_docs, missing_dois)
        
        captured = capsys.readouterr()
        assert "Checked 1 DOIs" in captured.out
        assert "ALREADY IN LIBRARY (1)" in captured.out
        assert "NOT IN LIBRARY" not in captured.out
    
    def test_print_results_none_found(self, capsys):
        """Test print_results when no DOIs are found"""
        dois_checked = ["10.1038/nature99999"]
        found_docs = []
        missing_dois = ["10.1038/nature99999"]
        
        print_results(dois_checked, found_docs, missing_dois)
        
        captured = capsys.readouterr()
        assert "Checked 1 DOIs" in captured.out
        assert "NOT IN LIBRARY (1)" in captured.out
        assert "ALREADY IN LIBRARY" not in captured.out
