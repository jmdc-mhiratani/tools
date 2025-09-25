# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
CSV2XLSX_v2 is a CSV ⇄ Excel conversion tool with automatic encoding detection and GUI interface built with tkinter. The project follows a minimal, phased development approach focusing on simplicity over complexity.

## Development Commands

### Environment Setup
```bash
# Install uv package manager
pip install uv

# Initialize project and install dependencies
uv sync

# Install development dependencies
uv sync --extra dev
```

### Running the Application
```bash
# Run the main application
uv run python src/main.py
```

### Code Quality
```bash
# Format code with black
uv run black src/ tests/

# Lint code with ruff
uv run ruff src/ tests/

# Run tests
uv run pytest tests/
```

## Architecture & Key Design Principles

### Design Philosophy
- **Modular Architecture**: Clean separation of concerns with dedicated modules
- **Enterprise-Grade**: Production-ready code with comprehensive error handling
- **Scalability**: Support for large files through chunked processing
- **Extensibility**: Plugin-ready architecture for future enhancements

### New Modular Structure
```
src/
├── main.py              # Application entry point
├── converter.py         # High-performance conversion engines
├── ui/
│   ├── main_window.py   # Advanced GUI with threading
│   └── components.py    # Reusable UI components
└── utils/
    ├── file_handler.py  # File operations and validation
    └── validators.py    # Security and data validation
```

### Core Components
1. **Conversion Engine** (`converter.py`):
   - CSVConverter with large file support and chunked processing
   - ExcelToCSVConverter with UTF-8 BOM compatibility
   - Automatic encoding detection and data type inference

2. **Advanced GUI** (`ui/main_window.py`):
   - Threaded operations for responsive UI
   - Progress tracking with cancellation support
   - Batch processing with file selection

3. **Utility Layer** (`utils/`):
   - File validation and security checks
   - Performance estimation and system resource monitoring
   - Configuration management and logging

### Technical Specifications
- **CSV Input**: Auto-detects Shift_JIS and UTF-8 encoding
- **CSV Output**: Always UTF-8 with BOM for Excel compatibility
- **Excel Format**: .xlsx using openpyxl backend
- **Error Handling**: Individual file failures don't stop batch processing

### Development Phases

**Phase 1 (Minimum Viable):**
- File selection dialog
- Basic CSV ↔ Excel conversion
- Simple progress display

**Phase 2 (Extended Features):**
- Automatic encoding detection
- UTF-8 BOM support for Excel compatibility
- Detailed error handling and logging

## Important Implementation Notes

### File Organization
- Keep all source code in `src/` directory
- Tests go in `tests/` directory
- Documentation in `docs/` directory

### Dependencies
- **pandas**: Core data processing engine
- **openpyxl**: Excel file operations
- **chardet**: Encoding detection
- **tkinter**: GUI (built-in with Python)

### GUI Design
The application uses a single-window tkinter interface with:
- File/folder selection buttons
- File list with checkboxes for selective conversion
- Radio buttons for output format selection
- Progress bar for batch operations

### Encoding Strategy
- Always detect input CSV encoding using chardet
- Output CSV files with UTF-8 BOM for maximum Excel compatibility
- Handle encoding errors gracefully with per-file error reporting