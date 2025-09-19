# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PDF2PNG/PDF2PPTX Converter (Refactored Version)

This spec file builds a standalone executable from the refactored codebase.
The executable includes all necessary dependencies and can run without
requiring Python installation on the target system.

Usage:
    pyinstaller build.spec

Output:
    dist/PDF2PPTX_Converter[.exe] - Standalone executable

Features:
- Optimized for the new src/ directory structure
- Includes all GUI assets and dependencies
- Single-file executable for easy distribution
- Console window disabled for clean user experience

Version: 2.0 (Refactored Architecture)
"""

import sys
from pathlib import Path

# Get project root directory
project_root = Path.cwd()
src_path = str(project_root / "src")

# Add src to path for proper imports
if src_path not in sys.path:
    sys.path.insert(0, src_path)

a = Analysis(
    ['main.py'],  # Main entry point for refactored version
    pathex=[str(project_root), src_path],
    binaries=[],
    datas=[
        # Include any data files if needed in the future
        # ('src/assets/*', 'assets/'),  # Uncomment if assets directory exists
    ],
    hiddenimports=[
        # Explicit imports to ensure they're included
        'tkinter',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.ttk',
        'fitz',  # PyMuPDF
        'PIL',
        'PIL.Image',
        'pptx',
        'pptx.util',
        'pptx.dml.color',
        'pptx.enum.shapes',
        # Our refactored modules
        'src.config',
        'src.core.pdf_processor',
        'src.ui.main_window',
        'src.ui.converters',
        'src.utils.error_handling',
        'src.utils.path_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy.distutils',
        'pytest',
        'unittest',
    ],
    noarchive=False,
    optimize=2,  # Enable optimizations
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PDF2PPTX_Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip symbols to reduce size
    upx=True,    # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Disable console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path here if available
    version_file=None,  # Add version info file here if available
)