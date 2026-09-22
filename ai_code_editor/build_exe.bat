@echo off
REM ============================================================
REM Sotstech Python Editor - Windows EXE build script (v2)
REM Builds inside a CLEAN, ISOLATED virtual environment so that
REM unrelated packages already installed on your PC (Kivy, numpy,
REM pygame, etc.) cannot interfere with PyInstaller's build.
REM ============================================================

cd /d "%~dp0"

echo Creating a clean virtual environment (build_env)...
python -m venv build_env

echo.
echo Activating virtual environment...
call build_env\Scripts\activate.bat

echo.
echo Upgrading pip and installing ONLY this project's dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo Building EXE (this can take a minute)...
pyinstaller --noconfirm --clean --onefile --windowed ^
    --name "SotstechPythonEditor" ^
    --icon "app_icon.ico" ^
    --add-data "dosyam;dosyam" ^
    main.py

echo.
echo Deactivating virtual environment...
call build_env\Scripts\deactivate.bat

echo.
echo Done! Your EXE is in the "dist" folder:
echo   dist\SotstechPythonEditor.exe
pause
