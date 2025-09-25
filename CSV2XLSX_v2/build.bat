@echo off
echo ============================================
echo CSV2XLSX v2.0 Build Script
echo ============================================

echo Installing build dependencies...
uv add --dev pyinstaller

echo Building executable...
uv run python build.py

echo Build process completed!
pause