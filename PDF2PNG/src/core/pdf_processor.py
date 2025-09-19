"""
Core PDF processing functionality with unified conversion logic.
Eliminates code duplication across GUI and standalone scripts.
"""

from __future__ import annotations

import fitz
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Iterator, Optional, Tuple
from io import BytesIO


@dataclass
class ConversionConfig:
    """Configuration for PDF conversion operations."""
    scale_factor: float = 1.5
    auto_rotate: bool = True
    slide_width_mm: float = 420.0
    slide_height_mm: float = 297.0
    target_dpi: int = 150

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.scale_factor <= 0:
            raise ValueError("Scale factor must be positive")
        if self.target_dpi < 72:
            raise ValueError("DPI must be at least 72")


@dataclass
class PageInfo:
    """Information about a processed PDF page."""
    page_number: int
    original_size: Tuple[float, float]  # width, height in points
    is_portrait: bool
    was_rotated: bool
    final_size: Tuple[float, float]  # after rotation


class PDFProcessingError(Exception):
    """Raised when PDF processing fails."""
    pass


@contextmanager
def open_pdf_document(file_path: Path) -> Generator[fitz.Document, None, None]:
    """
    Safely open and close PDF document with proper resource management.

    Args:
        file_path: Path to PDF file

    Yields:
        Opened PyMuPDF document

    Raises:
        PDFProcessingError: If PDF cannot be opened
    """
    if not file_path.exists():
        raise PDFProcessingError(f"PDF file not found: {file_path}")

    if not file_path.suffix.lower() == '.pdf':
        raise PDFProcessingError(f"Not a PDF file: {file_path}")

    try:
        doc = fitz.open(str(file_path))
        yield doc
    except Exception as e:
        raise PDFProcessingError(f"Failed to open PDF {file_path}: {e}")
    finally:
        if 'doc' in locals():
            doc.close()


def analyze_page_orientation(page: fitz.Page) -> Tuple[bool, Tuple[float, float]]:
    """
    Analyze page orientation and dimensions.

    Args:
        page: PyMuPDF page object

    Returns:
        Tuple of (is_portrait, (width, height))
    """
    rect = page.rect
    width, height = rect.width, rect.height
    is_portrait = width < height
    return is_portrait, (width, height)


def process_page_to_pixmap(
    page: fitz.Page,
    config: ConversionConfig
) -> Tuple[fitz.Pixmap, PageInfo]:
    """
    Process a PDF page to pixmap with optional rotation.

    Args:
        page: PyMuPDF page to process
        config: Conversion configuration

    Returns:
        Tuple of (processed pixmap, page info)

    Raises:
        PDFProcessingError: If page processing fails
    """
    try:
        is_portrait, original_size = analyze_page_orientation(page)

        # Determine rotation
        rotation = 90 if (config.auto_rotate and is_portrait) else 0

        # Create transformation matrix
        matrix = fitz.Matrix(config.scale_factor, config.scale_factor)

        # Generate pixmap with scaling and rotation
        pixmap = page.get_pixmap(matrix=matrix, rotate=rotation)

        # Calculate final size after rotation
        if rotation == 90:
            final_size = (original_size[1], original_size[0])  # Swap width/height
        else:
            final_size = original_size

        page_info = PageInfo(
            page_number=page.number + 1,
            original_size=original_size,
            is_portrait=is_portrait,
            was_rotated=(rotation == 90),
            final_size=final_size
        )

        return pixmap, page_info

    except Exception as e:
        raise PDFProcessingError(f"Failed to process page {page.number + 1}: {e}")


def process_page_to_bytes(
    page: fitz.Page,
    config: ConversionConfig,
    format: str = "png"
) -> Tuple[bytes, PageInfo]:
    """
    Process PDF page directly to image bytes.

    Args:
        page: PyMuPDF page to process
        config: Conversion configuration
        format: Output format ("png", "jpeg", etc.)

    Returns:
        Tuple of (image bytes, page info)
    """
    pixmap, page_info = process_page_to_pixmap(page, config)

    try:
        image_bytes = pixmap.tobytes(format)
        return image_bytes, page_info
    finally:
        # Clean up pixmap memory
        pixmap = None


def get_pdf_pages(pdf_path: Path) -> Iterator[fitz.Page]:
    """
    Iterator over PDF pages with proper resource management.

    Args:
        pdf_path: Path to PDF file

    Yields:
        PDF pages one at a time
    """
    with open_pdf_document(pdf_path) as doc:
        for page_num in range(len(doc)):
            yield doc[page_num]


def count_total_pages(pdf_files: list[Path]) -> int:
    """
    Count total pages across multiple PDF files.

    Args:
        pdf_files: List of PDF file paths

    Returns:
        Total page count

    Raises:
        PDFProcessingError: If any PDF cannot be read
    """
    total = 0
    for pdf_path in pdf_files:
        try:
            with open_pdf_document(pdf_path) as doc:
                total += len(doc)
        except PDFProcessingError:
            # Re-raise with context about which file failed
            raise PDFProcessingError(f"Failed to count pages in {pdf_path}")

    return total


# Unit conversion utilities
def mm_to_emu(mm: float) -> int:
    """Convert millimeters to EMU (English Metric Units)."""
    return int((mm / 25.4) * 914400)


def points_to_emu(points: float) -> int:
    """Convert PDF points to EMU."""
    return int((points / 72) * 914400)


def emu_to_inches(emu: int) -> float:
    """Convert EMU to inches."""
    return emu / 914400


def validate_conversion_config(config: ConversionConfig) -> None:
    """
    Validate conversion configuration parameters.

    Args:
        config: Configuration to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if config.scale_factor <= 0 or config.scale_factor > 10:
        raise ValueError("Scale factor must be between 0 and 10")

    if config.slide_width_mm <= 0 or config.slide_height_mm <= 0:
        raise ValueError("Slide dimensions must be positive")

    if config.target_dpi < 72 or config.target_dpi > 600:
        raise ValueError("DPI must be between 72 and 600")