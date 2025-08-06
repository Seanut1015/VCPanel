@echo off
call ..\.venv\Scripts\activate.bat

cd UI_files

where pyuic6 >nul 2>nul
if errorlevel 1 (
    echo [ERROR] NOT install pyuic6 : pip install pyqt6
    pause
    exit /b 1
)

pyuic6 untitled.ui -o UI.py

