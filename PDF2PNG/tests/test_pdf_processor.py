"""
Unit tests for the PDF processor core module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import fitz

from src.core.pdf_processor import (
    ConversionConfig,
    PDFProcessingError,
    analyze_page_orientation,
    process_page_to_pixmap,
    validate_conversion_config,
    mm_to_emu,
    points_to_emu
)


class TestConversionConfig:
    """Test ConversionConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ConversionConfig()
        assert config.scale_factor == 1.5
        assert config.auto_rotate is True
        assert config.slide_width_mm == 420.0
        assert config.slide_height_mm == 297.0
        assert config.target_dpi == 150

    def test_invalid_scale_factor(self):
        """Test validation of invalid scale factor."""
        with pytest.raises(ValueError, match="Scale factor must be positive"):
            ConversionConfig(scale_factor=0)

        with pytest.raises(ValueError, match="Scale factor must be positive"):
            ConversionConfig(scale_factor=-1.5)

    def test_invalid_dpi(self):
        """Test validation of invalid DPI."""
        with pytest.raises(ValueError, match="DPI must be at least 72"):
            ConversionConfig(target_dpi=50)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_mm_to_emu(self):
        """Test millimeter to EMU conversion."""
        # A3 width: 420mm should convert correctly
        result = mm_to_emu(420.0)
        expected = int((420.0 / 25.4) * 914400)
        assert result == expected

    def test_points_to_emu(self):
        """Test points to EMU conversion."""
        # 72 points = 1 inch = 914400 EMU
        assert points_to_emu(72.0) == 914400
        assert points_to_emu(36.0) == 457200

    def test_validate_conversion_config(self):
        """Test configuration validation."""
        # Valid config should not raise
        valid_config = ConversionConfig(scale_factor=2.0, target_dpi=150)
        validate_conversion_config(valid_config)

        # Invalid scale factor
        invalid_config = ConversionConfig(scale_factor=15.0)  # Too high
        with pytest.raises(ValueError, match="Scale factor must be between 0 and 10"):
            validate_conversion_config(invalid_config)

        # Invalid DPI
        invalid_config = ConversionConfig(target_dpi=800)  # Too high
        with pytest.raises(ValueError, match="DPI must be between 72 and 600"):
            validate_conversion_config(invalid_config)


class TestPageAnalysis:
    """Test page analysis functions."""

    def test_analyze_page_orientation_portrait(self):
        """Test portrait page detection."""
        mock_page = Mock()
        mock_page.rect = Mock()
        mock_page.rect.width = 100
        mock_page.rect.height = 200

        is_portrait, (width, height) = analyze_page_orientation(mock_page)

        assert is_portrait is True
        assert width == 100
        assert height == 200

    def test_analyze_page_orientation_landscape(self):
        """Test landscape page detection."""
        mock_page = Mock()
        mock_page.rect = Mock()
        mock_page.rect.width = 200
        mock_page.rect.height = 100

        is_portrait, (width, height) = analyze_page_orientation(mock_page)

        assert is_portrait is False
        assert width == 200
        assert height == 100


class TestPageProcessing:
    """Test page processing functions."""

    @patch('src.core.pdf_processor.analyze_page_orientation')
    def test_process_page_to_pixmap_no_rotation(self, mock_analyze):
        """Test page processing without rotation."""
        # Setup mocks
        mock_page = Mock()
        mock_page.number = 0
        mock_page.get_pixmap.return_value = Mock()

        mock_analyze.return_value = (False, (200, 100))  # Landscape

        config = ConversionConfig(scale_factor=1.5, auto_rotate=False)

        # Execute
        pixmap, page_info = process_page_to_pixmap(mock_page, config)

        # Verify
        mock_page.get_pixmap.assert_called_once()
        assert page_info.page_number == 1
        assert page_info.is_portrait is False
        assert page_info.was_rotated is False
        assert page_info.original_size == (200, 100)
        assert page_info.final_size == (200, 100)

    @patch('src.core.pdf_processor.analyze_page_orientation')
    def test_process_page_to_pixmap_with_rotation(self, mock_analyze):
        """Test page processing with auto-rotation."""
        # Setup mocks
        mock_page = Mock()
        mock_page.number = 0
        mock_page.get_pixmap.return_value = Mock()

        mock_analyze.return_value = (True, (100, 200))  # Portrait

        config = ConversionConfig(scale_factor=1.5, auto_rotate=True)

        # Execute
        pixmap, page_info = process_page_to_pixmap(mock_page, config)

        # Verify rotation occurred
        assert page_info.is_portrait is True
        assert page_info.was_rotated is True
        assert page_info.original_size == (100, 200)
        assert page_info.final_size == (200, 100)  # Swapped due to rotation

    def test_process_page_to_pixmap_error_handling(self):
        """Test error handling in page processing."""
        mock_page = Mock()
        mock_page.number = 0
        mock_page.get_pixmap.side_effect = Exception("Pixmap error")

        config = ConversionConfig()

        with pytest.raises(PDFProcessingError, match="Failed to process page 1"):
            process_page_to_pixmap(mock_page, config)


class TestFileOperations:
    """Test file operation functions."""

    @patch('src.core.pdf_processor.open_pdf_document')
    def test_count_total_pages(self, mock_open_pdf):
        """Test counting pages across multiple PDFs."""
        from src.core.pdf_processor import count_total_pages

        # Mock PDF documents with different page counts
        mock_doc1 = Mock()
        mock_doc1.__len__ = Mock(return_value=5)

        mock_doc2 = Mock()
        mock_doc2.__len__ = Mock(return_value=3)

        mock_open_pdf.side_effect = [
            mock_doc1,
            mock_doc2
        ]

        pdf_files = [Path("doc1.pdf"), Path("doc2.pdf")]
        total = count_total_pages(pdf_files)

        assert total == 8

    def test_count_total_pages_error(self):
        """Test error handling in page counting."""
        from src.core.pdf_processor import count_total_pages

        with patch('src.core.pdf_processor.open_pdf_document') as mock_open:
            mock_open.side_effect = PDFProcessingError("Cannot open PDF")

            pdf_files = [Path("bad.pdf")]

            with pytest.raises(PDFProcessingError, match="Failed to count pages"):
                count_total_pages(pdf_files)


@pytest.fixture
def mock_fitz_document():
    """Create a mock PyMuPDF document for testing."""
    doc = Mock()
    doc.__len__ = Mock(return_value=2)
    doc.close = Mock()

    # Mock pages
    page1 = Mock()
    page1.number = 0
    page1.rect = Mock()
    page1.rect.width = 100
    page1.rect.height = 200

    page2 = Mock()
    page2.number = 1
    page2.rect = Mock()
    page2.rect.width = 200
    page2.rect.height = 100

    doc.__iter__ = Mock(return_value=iter([page1, page2]))
    doc.__getitem__ = Mock(side_effect=lambda x: [page1, page2][x])

    return doc


class TestPDFDocumentHandling:
    """Test PDF document context manager."""

    @patch('fitz.open')
    def test_open_pdf_document_success(self, mock_fitz_open, mock_fitz_document):
        """Test successful PDF opening."""
        from src.core.pdf_processor import open_pdf_document

        mock_fitz_open.return_value = mock_fitz_document
        test_path = Path("test.pdf")

        # Mock file existence
        with patch.object(test_path, 'exists', return_value=True), \
             patch.object(test_path, 'suffix', '.pdf'):

            with open_pdf_document(test_path) as doc:
                assert doc == mock_fitz_document

        mock_fitz_document.close.assert_called_once()

    def test_open_pdf_document_file_not_found(self):
        """Test error when PDF file doesn't exist."""
        from src.core.pdf_processor import open_pdf_document

        test_path = Path("nonexistent.pdf")

        with patch.object(test_path, 'exists', return_value=False):
            with pytest.raises(PDFProcessingError, match="PDF file not found"):
                with open_pdf_document(test_path):
                    pass

    def test_open_pdf_document_invalid_extension(self):
        """Test error for non-PDF files."""
        from src.core.pdf_processor import open_pdf_document

        test_path = Path("test.txt")

        with patch.object(test_path, 'exists', return_value=True), \
             patch.object(test_path, 'suffix', '.txt'):

            with pytest.raises(PDFProcessingError, match="Not a PDF file"):
                with open_pdf_document(test_path):
                    pass