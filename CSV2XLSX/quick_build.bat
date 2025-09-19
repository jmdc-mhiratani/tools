@echo off
echo ===================================
echo CSV2XLSX Windows Build Script
echo ===================================
echo.

echo Step 1: Environment check...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo Python found. Checking version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%
echo.

echo Step 2: Virtual environment setup...
if not exist venv_build (
    echo Creating virtual environment...
    python -m venv venv_build
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists
)

echo Activating virtual environment...
call venv_build\Scripts\activate
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

echo Step 3: Dependencies installation...
echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo Installing PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)
echo.

echo Step 4: Building executables...
python build.py
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)
echo.

echo ===================================
echo Build completed successfully!
echo ===================================
echo.
echo Output files location:
echo   dist\CSV2XLSX_IC\
echo.
echo Distribution package:
echo   dist\CSV2XLSX_IC_v1.0.0_Windows.zip
echo.
echo You can now distribute the ZIP file or the contents of CSV2XLSX_IC folder.
echo.
pause