"""
Test Suite for Document Processor (Milestone 1)
Tests document extraction from PDF, DOCX, PPTX, and XLSX formats.
"""

import os
import sys
import pytest
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from processors.document_processor import DocumentProcessor, create_processor


# Test configuration
TEST_CASES = {
    "pdf_strategy": {
        "input": "mock_strategy_doc.pdf",
        "expected_sections": ["Vision", "Mission", "Strategic"],
        "min_word_count": 100
    },
    "docx_goals": {
        "input": "mock_employee_goals.docx",
        "expected_goals_count": 5,
        "expected_fields": ["objective", "measure", "target", "timeline"],
        "min_word_count": 100
    },
    "xlsx_kpis": {
        "input": "mock_kpi_tracker.xlsx",
        "expected_columns": ["KPI", "Target", "Actual", "Owner"],
        "expected_rows_min": 10,
        "min_word_count": 50
    },
    "pptx_strategy": {
        "input": "mock_strategy_presentation.pptx",
        "expected_sections": ["Vision", "Strategic"],
        "min_word_count": 30
    }
}

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDocumentProcessor:
    """Test cases for the unified DocumentProcessor."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.processor = DocumentProcessor()
        self.fixtures_dir = FIXTURES_DIR

        # Create fixtures if they don't exist
        self._ensure_fixtures()

    def _ensure_fixtures(self):
        """Ensure test fixtures exist."""
        # Check if fixtures need to be created
        missing = []
        for test_name, config in TEST_CASES.items():
            fixture_path = self.fixtures_dir / config["input"]
            if not fixture_path.exists():
                missing.append(test_name)

        if missing:
            print(f"Creating missing fixtures: {missing}")
            try:
                # Add tests directory to path for import
                sys.path.insert(0, str(Path(__file__).parent))
                from fixtures.create_fixtures import create_all_fixtures
                create_all_fixtures()
            except Exception as e:
                print(f"Warning: Could not create all fixtures: {e}")

    def test_processor_initialization(self):
        """Test that DocumentProcessor initializes correctly."""
        processor = create_processor()
        assert processor is not None

        # Check extractors are available
        status = processor.get_extractor_status()
        assert isinstance(status, dict)
        print(f"Extractor status: {status}")

    def test_supported_formats(self):
        """Test that all required formats are supported."""
        formats = self.processor.get_supported_formats()
        assert '.pdf' in formats
        assert '.docx' in formats
        assert '.xlsx' in formats
        assert '.pptx' in formats

    def test_pdf_extraction(self):
        """Test PDF document extraction."""
        fixture_path = self.fixtures_dir / TEST_CASES["pdf_strategy"]["input"]

        if not fixture_path.exists():
            pytest.skip(f"PDF fixture not found: {fixture_path}")

        result = self.processor.extract(str(fixture_path), document_type='strategy')

        # Validate structure
        assert 'documentId' in result
        assert 'fileName' in result
        assert 'documentType' in result
        assert 'extractedText' in result
        assert 'structuredSections' in result
        assert 'metadata' in result

        # Validate content
        assert result['documentType'] == 'strategy'
        assert result['extractedText'], "Extracted text should not be empty"
        assert result['metadata']['wordCount'] >= TEST_CASES["pdf_strategy"]["min_word_count"]

        # Check for expected sections
        text_lower = result['extractedText'].lower()
        for section in TEST_CASES["pdf_strategy"]["expected_sections"]:
            assert section.lower() in text_lower, f"Expected section '{section}' not found"

        print(f"PDF extraction passed: {result['metadata']['wordCount']} words")

    def test_docx_extraction(self):
        """Test DOCX document extraction."""
        fixture_path = self.fixtures_dir / TEST_CASES["docx_goals"]["input"]

        if not fixture_path.exists():
            pytest.skip(f"DOCX fixture not found: {fixture_path}")

        result = self.processor.extract(str(fixture_path), document_type='goals')

        # Validate structure
        assert 'documentId' in result
        assert 'extractedText' in result
        assert 'structuredSections' in result
        assert 'metadata' in result

        # Validate content
        assert result['documentType'] == 'goals'
        assert result['extractedText'], "Extracted text should not be empty"
        assert result['metadata']['wordCount'] >= TEST_CASES["docx_goals"]["min_word_count"]

        # Check that structured sections exist
        assert len(result['structuredSections']) > 0, "Should have structured sections"

        # Check for goal-related content
        text_lower = result['extractedText'].lower()
        goal_keywords = ['goal', 'objective', 'target']
        found_keywords = [kw for kw in goal_keywords if kw in text_lower]
        assert len(found_keywords) > 0, "Should contain goal-related keywords"

        print(f"DOCX extraction passed: {result['metadata']['wordCount']} words, {len(result['structuredSections'])} sections")

    def test_xlsx_extraction(self):
        """Test XLSX document extraction."""
        fixture_path = self.fixtures_dir / TEST_CASES["xlsx_kpis"]["input"]

        if not fixture_path.exists():
            pytest.skip(f"XLSX fixture not found: {fixture_path}")

        result = self.processor.extract(str(fixture_path), document_type='strategy')

        # Validate structure
        assert 'documentId' in result
        assert 'extractedText' in result
        assert 'structuredSections' in result
        assert 'metadata' in result

        # Validate content
        assert result['extractedText'], "Extracted text should not be empty"
        assert result['metadata']['wordCount'] >= TEST_CASES["xlsx_kpis"]["min_word_count"]

        # Check for expected columns in text
        text_content = result['extractedText']
        for col in TEST_CASES["xlsx_kpis"]["expected_columns"]:
            assert col in text_content, f"Expected column '{col}' not found"

        # Check sheet count
        if 'sheetCount' in result['metadata']:
            assert result['metadata']['sheetCount'] >= 1

        print(f"XLSX extraction passed: {result['metadata']['wordCount']} words")

    def test_pptx_extraction(self):
        """Test PPTX document extraction."""
        fixture_path = self.fixtures_dir / TEST_CASES["pptx_strategy"]["input"]

        if not fixture_path.exists():
            pytest.skip(f"PPTX fixture not found: {fixture_path}")

        result = self.processor.extract(str(fixture_path), document_type='strategy')

        # Validate structure
        assert 'documentId' in result
        assert 'extractedText' in result
        assert 'structuredSections' in result
        assert 'metadata' in result

        # Validate content
        assert result['extractedText'], "Extracted text should not be empty"
        assert result['metadata']['wordCount'] >= TEST_CASES["pptx_strategy"]["min_word_count"]

        # Check for expected sections
        text_lower = result['extractedText'].lower()
        for section in TEST_CASES["pptx_strategy"]["expected_sections"]:
            assert section.lower() in text_lower, f"Expected section '{section}' not found"

        print(f"PPTX extraction passed: {result['metadata']['wordCount']} words")

    def test_batch_extraction(self):
        """Test batch document extraction."""
        file_paths = []
        for test_name, config in TEST_CASES.items():
            fixture_path = self.fixtures_dir / config["input"]
            if fixture_path.exists():
                file_paths.append(str(fixture_path))

        if not file_paths:
            pytest.skip("No fixtures available for batch test")

        results = self.processor.extract_batch(file_paths, document_type='strategy')

        assert len(results) == len(file_paths)
        for result in results:
            assert 'documentId' in result
            assert 'fileName' in result

        print(f"Batch extraction passed: {len(results)} documents")

    def test_file_validation(self):
        """Test file validation functionality."""
        # Test non-existent file
        result = self.processor.validate_file('/nonexistent/file.pdf')
        assert result['valid'] is False
        assert 'does not exist' in result['errors'][0]

        # Test unsupported format - create a temp file with unsupported extension
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'test content')
            temp_path = f.name

        try:
            result = self.processor.validate_file(temp_path)
            assert result['valid'] is False
            assert 'Unsupported format' in result['errors'][0]
        finally:
            os.remove(temp_path)

    def test_error_handling_corrupted_file(self):
        """Test error handling for corrupted files."""
        # Create a fake corrupted PDF
        corrupted_path = self.fixtures_dir / "corrupted.pdf"
        with open(corrupted_path, 'wb') as f:
            f.write(b"This is not a valid PDF")

        try:
            with pytest.raises(ValueError):
                self.processor.extract(str(corrupted_path))
        finally:
            # Cleanup
            if corrupted_path.exists():
                os.remove(corrupted_path)

    def test_metadata_extraction(self):
        """Test that metadata is properly extracted."""
        fixture_path = self.fixtures_dir / TEST_CASES["pdf_strategy"]["input"]

        if not fixture_path.exists():
            pytest.skip("PDF fixture not found")

        result = self.processor.extract(str(fixture_path))

        metadata = result['metadata']
        assert 'pageCount' in metadata
        assert 'wordCount' in metadata
        assert 'extractionTimestamp' in metadata
        assert 'fileSize' in metadata
        assert 'fileFormat' in metadata

        # Validate timestamp format (ISO8601)
        assert 'T' in metadata['extractionTimestamp']
        assert metadata['extractionTimestamp'].endswith('Z')

        print(f"Metadata extraction passed: {metadata}")

    def test_hierarchical_structure_preservation(self):
        """Test that document hierarchy is preserved in sections."""
        fixture_path = self.fixtures_dir / TEST_CASES["docx_goals"]["input"]

        if not fixture_path.exists():
            pytest.skip("DOCX fixture not found")

        result = self.processor.extract(str(fixture_path))

        sections = result['structuredSections']
        assert len(sections) > 0

        # Check section structure
        for section in sections:
            assert 'heading' in section
            assert 'content' in section
            assert 'hierarchy' in section
            assert isinstance(section['hierarchy'], int)

        print(f"Hierarchical structure test passed: {len(sections)} sections")


class TestExtractorAvailability:
    """Test extractor availability and graceful degradation."""

    def test_pdf_extractor_available(self):
        """Test PDF extractor is available."""
        from processors.pdf_extractor import PDFExtractor
        extractor = PDFExtractor()
        assert extractor is not None
        assert extractor.can_handle("test.pdf")
        assert not extractor.can_handle("test.docx")

    def test_docx_extractor_available(self):
        """Test DOCX extractor is available."""
        from processors.docx_extractor import DOCXExtractor
        extractor = DOCXExtractor()
        assert extractor is not None
        assert extractor.can_handle("test.docx")
        assert not extractor.can_handle("test.pdf")

    def test_xlsx_extractor_available(self):
        """Test XLSX extractor is available."""
        from processors.xlsx_extractor import XLSXExtractor
        extractor = XLSXExtractor()
        assert extractor is not None
        assert extractor.can_handle("test.xlsx")
        assert extractor.can_handle("test.xls")
        assert not extractor.can_handle("test.pdf")

    def test_pptx_extractor_available(self):
        """Test PPTX extractor is available."""
        from processors.pptx_extractor import PPTXExtractor
        extractor = PPTXExtractor()
        assert extractor is not None
        assert extractor.can_handle("test.pptx")
        assert not extractor.can_handle("test.pdf")


def run_manual_tests():
    """Run tests manually for debugging."""
    print("=" * 60)
    print("MILESTONE 1: Document Processor Tests")
    print("=" * 60)

    processor = DocumentProcessor()
    print(f"\nExtractor Status: {processor.get_extractor_status()}")
    print(f"Supported Formats: {processor.get_supported_formats()}")

    # Create fixtures
    print("\nCreating test fixtures...")
    try:
        from fixtures.create_fixtures import create_all_fixtures
        fixtures = create_all_fixtures()
        print(f"Created fixtures: {list(fixtures.keys())}")
    except Exception as e:
        print(f"Error creating fixtures: {e}")
        return

    # Test each fixture
    for test_name, config in TEST_CASES.items():
        fixture_path = FIXTURES_DIR / config["input"]
        print(f"\n--- Testing {test_name} ---")

        if not fixture_path.exists():
            print(f"SKIP: {fixture_path} not found")
            continue

        try:
            result = processor.extract(str(fixture_path))
            assert result['structuredSections'], f"Failed: {test_name} - No sections extracted"
            assert result['metadata']['wordCount'] >= config.get('min_word_count', 50)
            print(f"PASS: {test_name}")
            print(f"  - Words: {result['metadata']['wordCount']}")
            print(f"  - Sections: {len(result['structuredSections'])}")
        except Exception as e:
            print(f"FAIL: {test_name} - {e}")

    print("\n" + "=" * 60)
    print("Tests completed!")


if __name__ == '__main__':
    run_manual_tests()
