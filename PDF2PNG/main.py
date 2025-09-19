#!/usr/bin/env python3
"""
PDF2PNG/PDF2PPTX Converter - Main Entry Point

A refactored PDF conversion tool with improved architecture, error handling,
and maintainability. Supports conversion from PDF to PNG images and PowerPoint
presentations with a user-friendly GUI interface.

Usage:
    python main.py              # Launch GUI application
    python -m src.ui.main_window # Alternative launch method

Features:
- PDF to PNG image conversion with customizable scaling
- PDF to PowerPoint (PPTX) conversion with A3 landscape layout
- Automatic rotation for portrait pages
- Customizable PowerPoint label styling
- Progress tracking and user feedback
- Folder-based batch processing

Requirements:
    - Python 3.8+
    - PyMuPDF (fitz)
    - python-pptx
    - Pillow (PIL)
    - tkinter (usually included with Python)

Author: PDF2PNG Project
Version: 2.0 (Refactored Architecture)
Date: 2025-09-18
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from src.ui.main_window import main

    if __name__ == "__main__":
        # Launch the GUI application
        main()

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\n🔧 Possible solutions:")
    print("1. Install required dependencies:")
    print("   pip install -r requirements.txt")
    print("\n2. Ensure you're running from the project root directory")
    print("\n3. Check that the src/ directory structure is intact")

    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print("\n🐛 This appears to be a bug. Please check:")
    print("1. All dependencies are properly installed")
    print("2. No files are missing from the src/ directory")
    print("3. You have proper permissions to read project files")

    sys.exit(1)