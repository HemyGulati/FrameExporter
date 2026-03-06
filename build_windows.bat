@echo off
REM ============================================================
REM  FrameExporter Windows Build Script
REM  Uses "python -m pip" to avoid PATH issues with pip.exe
REM ============================================================

echo.
echo  ===========================================
echo   FrameExporter  ^|  Windows Build Script
echo  ===========================================
echo.

REM ── Locate Python ─────────────────────────────────────────
SET PYTHON=

py --version >nul 2>&1
IF NOT ERRORLEVEL 1 ( SET PYTHON=py & GOTO :python_found )

python --version >nul 2>&1
IF NOT ERRORLEVEL 1 ( SET PYTHON=python & GOTO :python_found )

python3 --version >nul 2>&1
IF NOT ERRORLEVEL 1 ( SET PYTHON=python3 & GOTO :python_found )

echo  [ERROR] Python not found on this machine.
echo.
echo  Install Python 3.10+ from:  https://www.python.org/downloads/
echo  During install, tick:  [x] Add Python to PATH
echo.
pause
exit /b 1

:python_found
echo  Python found:
%PYTHON% --version
echo.

REM ── Step 1: Dependencies ─────────────────────────────────
echo  [1/6] Installing Python dependencies...
%PYTHON% -m pip install --upgrade pip --quiet
%PYTHON% -m pip install -r requirements.txt
IF ERRORLEVEL 1 ( echo [ERROR] pip install failed. & pause & exit /b 1 )
%PYTHON% -m pip install pyinstaller
IF ERRORLEVEL 1 ( echo [ERROR] PyInstaller install failed. & pause & exit /b 1 )
echo.

REM ── Step 2: Download Tesseract ───────────────────────────
echo  [2/6] Downloading Tesseract OCR installer...
IF NOT EXIST "assets" mkdir assets

SET TESS_URL=https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.4.0.20240606.exe
SET TESS_OUT=assets\tesseract-ocr-w64-setup.exe

IF EXIST "%TESS_OUT%" (
    echo         Already downloaded - skipping.
) ELSE (
    powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('%TESS_URL%', '%TESS_OUT%')"
    IF NOT EXIST "%TESS_OUT%" (
        echo  [ERROR] Download failed. Check internet connection.
        echo  Or manually download from: https://github.com/UB-Mannheim/tesseract/wiki
        echo  Save as: assets\tesseract-ocr-w64-setup.exe
        pause & exit /b 1
    )
    echo         Downloaded OK.
)
echo.

REM ── Step 3: Build .exe ────────────────────────────────────
echo  [3/6] Building FrameExporter.exe...
%PYTHON% -m PyInstaller --onefile --windowed --name "FrameExporter" --icon "assets\icon.ico" --add-data "assets;assets" main.py
IF ERRORLEVEL 1 ( echo [ERROR] PyInstaller build failed. & pause & exit /b 1 )
echo.

REM ── Step 4: Copy assets into dist ────────────────────────
echo  [4/6] Copying assets to dist\...
IF NOT EXIST "dist\assets" mkdir "dist\assets"
xcopy /E /I /Y assets dist\assets >nul 2>&1
echo         Done.
echo.
echo  [5/6] Build complete!  dist\FrameExporter.exe
echo.

REM ── Step 5: Compile installer with Inno Setup ────────────
echo  [6/6] Looking for Inno Setup...

SET ISCC=
IF EXIST "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"            SET "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
IF EXIST "C:\Program Files\Inno Setup 6\ISCC.exe"                  SET "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
IF EXIST "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"           SET "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
IF EXIST "%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe" SET "ISCC=%USERPROFILE%\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

IF DEFINED ISCC (
    echo         Found - compiling installer...
    IF NOT EXIST "installer_output" mkdir installer_output
    "%ISCC%" installer.iss
    IF ERRORLEVEL 1 (
        echo  [ERROR] Inno Setup failed.
    ) ELSE (
        echo.
        echo  =====================================================
        echo   ALL DONE!
        echo   Installer: installer_output\FrameExporter_Setup.exe
        echo  =====================================================
    )
) ELSE (
    echo         Inno Setup not found.
    echo.
    echo  To make the final installer:
    echo    1. Download Inno Setup (free): https://jrsoftware.org/isinfo.php
    echo    2. Open installer.iss in Inno Setup Compiler
    echo    3. Press Ctrl+F9
    echo    Output: installer_output\FrameExporter_Setup.exe
    echo.
    echo  The raw .exe is already at: dist\FrameExporter.exe
)
echo.
pause
