@echo off
echo ============================================
echo CSV2XLSX v3.0.0 Build Script (PySide6)
echo ============================================

echo Installing build dependencies...
uv pip install pyinstaller

echo Building executable with PySide6...
uv run python scripts\build.py

echo Build process completed!
echo.
echo Generated files:
echo - dist/CSV2XLSX_v3.0.0/ (executable directory)
echo - csv2xlsx_pyside6.spec (PyInstaller config)
echo - installer.iss (Inno Setup script)
echo.
pause