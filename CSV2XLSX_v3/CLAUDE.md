# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

日本語で考え、日本語で回答する。

## Project Overview
CSV2XLSX_v2 is a CSV ⇄ Excel conversion tool with automatic encoding detection and modern Qt-based GUI interface. The project follows a modular architecture approach with clean Model-View-Controller separation.

## Current Development Status (2025/10/26)
- **バージョン**: v2.3.0
- **仮想環境**: Python 3.13.7 + uv環境構築完了
- **UI**: PySide6ベースのモダンQt GUI (完了)
- **ロギング**: 全8モジュール統合完了
- **ビルドシステム**: PyInstaller + Inno Setup (PySide6対応完了)
- **次フェーズ**: pytest-qt実装、パフォーマンス最適化

### v2.3.0 Major Changes
- **GUI Framework Migration**: TkEasyGUI → PySide6 (Qt6) ✅
- **Modern UI**: Material Design-inspired styling with QSS ✅
- **Model/View Architecture**: QTableView + QAbstractTableModel for file management ✅
- **Enhanced UX**: Resizable panels, context menus, menu bar, toolbar ✅
- **Logging Integration**: All widgets/models with structured logging ✅
- **Build System**: PyInstaller configuration for PySide6 deployment ✅

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
# Run the application
uv run python src/main_qt6.py
```

### Code Quality
```bash
# Format code (Ruff Format)
uv run ruff format src/ tests/

# Lint + Auto-fix (Ruff)
uv run ruff check --fix src/ tests/

# Type check (Mypy)
uv run mypy src/

# Run all checks (pre-commit)
uv run ruff format src/ tests/ && \
uv run ruff check --fix src/ tests/ && \
uv run mypy src/

# Run tests
uv run pytest tests/
```

### Building Windows Executable (PySide6)
```bash
# Method 1: Use build.bat (推奨)
build.bat

# Method 2: Manual build
uv pip install pyinstaller
uv run python build.py

# Build output (v2.3.0+)
# - dist/CSV2XLSX_v2.3.0/ (実行可能ディレクトリ)
# - dist/CSV2XLSX_v2.3.0/CSV2XLSX_v2.3.0.exe (実行ファイル)
# - csv2xlsx_pyside6.spec (PyInstaller設定ファイル)
# - installer.iss (Inno Setupスクリプト)
```

#### PyInstaller Configuration Details (v2.3.0)
The build process includes:
- **PySide6 Hooks**: Automatic collection of Qt binaries, plugins, and data files
- **Resource Bundling**: QSS stylesheet and VERSION.txt bundled into executable
- **Hidden Imports**: All required PySide6 modules explicitly included (QtCore, QtGui, QtWidgets, shiboken6)
- **Exclusions**: TkEasyGUI, matplotlib, IPython excluded for smaller executable size
- **GUI Mode**: Console window disabled (`console=False`) for clean user experience
- **Entry Point**: `src/main_qt6.py` as primary application entry

#### Build Testing
```bash
# Test the executable before distribution
cd dist/CSV2XLSX_v2.3.0
./CSV2XLSX_v2.3.0.exe  # Windows
```

## Architecture & Key Design Principles

### Design Philosophy
- **Modular Architecture**: Clean separation of concerns with dedicated modules
- **Enterprise-Grade**: Production-ready code with comprehensive error handling
- **Scalability**: Support for large files through chunked processing
- **Extensibility**: Plugin-ready architecture for future enhancements

### Modular Structure (v2.3.0)
```
src/
├── main_qt6.py          # Application entry point
├── converter.py         # High-performance conversion engines
├── ui_qt6/              # Qt6 UI layer
│   ├── main_window.py   # QMainWindow with menu/toolbar
│   ├── widgets/
│   │   ├── file_table.py       # QTableView + Model
│   │   ├── settings_panel.py   # Conversion settings
│   │   ├── log_viewer.py       # Log display
│   │   └── progress_widget.py  # Progress tracking
│   ├── dialogs/
│   │   ├── settings_dialog.py  # App preferences
│   │   └── about_dialog.py     # About dialog
│   ├── models/
│   │   └── file_list_model.py  # QAbstractTableModel
│   └── resources/
│       └── styles.qss           # Qt stylesheet
├── core/                # Business logic layer
│   ├── file_manager.py
│   ├── conversion_controller.py
│   ├── progress_tracker.py
│   └── settings_manager.py
└── utils/
    ├── file_handler.py
    └── validators.py
```

### Core Components
1. **Conversion Engine** (`converter.py`):
   - CSVConverter with large file support and chunked processing
   - ExcelToCSVConverter with UTF-8 BOM compatibility
   - Automatic encoding detection and data type inference

2. **Modern Qt GUI** (`ui_qt6/main_window.py`):
   - PySide6 QMainWindow with menu bar, toolbar, status bar
   - Model/View architecture (QTableView + QAbstractTableModel)
   - Signal/Slot system for clean event handling
   - Resizable split panels for flexible layout
   - QSS-based Material Design styling
   - Context menus and keyboard shortcuts

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
- **PySide6**: Modern Qt6 GUI framework (v2.3.0+)
- ~~**tkeasygui**: Legacy GUI (deprecated in v2.3.0)~~

### GUI Design (v2.3.0)
The application uses a modern Qt6 interface with:
- **QMainWindow**: Professional desktop application layout
- **Menu Bar**: File, Edit, View, Tools, Help menus
- **Tool Bar**: Quick access to common operations
- **Split Layout**: Resizable settings panel (left) and file list (right)
- **QTableView**: Multi-column file list (Name, Size, Type, Status)
- **Context Menus**: Right-click actions for file operations
- **Tab Widget**: Organized Excel/CSV settings
- **QSS Styling**: Material Design-inspired color scheme
- **Status Bar**: Real-time status updates

#### Legacy TkEasyGUI Design (deprecated)
The legacy version used a simpler single-window interface:
- File selection buttons
- Listbox for file display
- Radio buttons for output format
- Basic progress bar

### Encoding Strategy
- Always detect input CSV encoding using chardet
- Output CSV files with UTF-8 BOM for maximum Excel compatibility
- Handle encoding errors gracefully with per-file error reporting
