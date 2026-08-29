@echo off
REM =========================================================================
REM   Morse Code Communication and Emergency Signaling System
REM   One-click launcher for Windows 11
REM   Author: Mustafa Shahid  (BSCS-14B, CMS 500889)
REM =========================================================================

title  Morse Code COAL Project - Launcher

echo.
echo  ==============================================================
echo    MORSE CODE COMMUNICATION ^& EMERGENCY SIGNALING SYSTEM
echo    CS-234  Computer Organization ^& Assembly Language
echo    Mustafa Shahid  ^|  BSCS-14B  ^|  CMS 500889
echo  ==============================================================
echo.

REM ---- check for python -----------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo  [!] Python was not found in PATH.
    echo       Install Python 3.10 or newer from https://www.python.org/downloads/
    echo       Tick "Add Python to PATH" during the installer.
    pause
    exit /b 1
)

REM ---- install requirements (only missing ones) -----------------------------
echo  [*] Verifying required packages ...
python -m pip install --quiet --disable-pip-version-check -r "%~dp0Software\requirements.txt"
if errorlevel 1 (
    echo  [!] Could not install Python packages. Check your internet connection.
    pause
    exit /b 1
)

REM ---- launch the GUI -------------------------------------------------------
echo  [*] Launching application ...
echo.
pushd "%~dp0Software"
python morse_app.py
popd

if errorlevel 1 (
    echo.
    echo  [!] The application exited with an error.
    pause
)
