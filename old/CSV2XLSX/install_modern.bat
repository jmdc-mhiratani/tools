@echo off
echo ================================
echo CSV2XLSX Modern UI Installer
echo ================================
echo.

echo Installing required packages...
echo.

rem Python仮想環境の作成（オプション）
echo Creating virtual environment...
python -m venv venv_modern 2>nul
if %errorlevel% neq 0 (
    echo Warning: Could not create virtual environment
    echo Continuing with global installation...
    echo.
) else (
    echo Activating virtual environment...
    call venv_modern\Scripts\activate.bat
    echo.
)

rem 必要なパッケージのインストール
echo Installing CustomTkinter and dependencies...
pip install --upgrade pip
pip install -r requirements_modern.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install packages
    echo Please check your Python installation and internet connection
    pause
    exit /b 1
)

echo.
echo ================================
echo Installation Complete!
echo ================================
echo.
echo To run the modern GUI version:
echo   - Double-click csv2xlsx_modern.bat
echo   - Or run: python src\modern_gui.py
echo.
echo To run the classic GUI version:
echo   - Double-click csv2xlsx_gui.bat
echo   - Or run: python src\main.py
echo.
pause