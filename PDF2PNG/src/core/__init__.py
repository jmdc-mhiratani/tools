"""Core PDF processing functionality."""

from .pdf_processor import (
    ConversionConfig,
    PDFProcessingError,
    PageInfo,
    open_pdf_document,
    process_page_to_pixmap,
    process_page_to_bytes,
    count_total_pages,
    mm_to_emu,
    points_to_emu
)

__all__ = [
    "ConversionConfig",
    "PDFProcessingError",
    "PageInfo",
    "open_pdf_document",
    "process_page_to_pixmap",
    "process_page_to_bytes",
    "count_total_pages",
    "mm_to_emu",
    "points_to_emu"
]