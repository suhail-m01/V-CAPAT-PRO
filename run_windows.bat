@echo off
setlocal
cd /d "%~dp0"

if exist .venv\Scripts\python.exe goto venv_ready

py -3.12 -c "import sys; assert sys.version_info[:2] == (3,12)" >nul 2>&1
if %errorlevel%==0 (
  echo Creating Python 3.12 virtual environment...
  py -3.12 -m venv .venv
  goto venv_ready
)

py -3.11 -c "import sys; assert sys.version_info[:2] == (3,11)" >nul 2>&1
if %errorlevel%==0 (
  echo Creating Python 3.11 virtual environment...
  py -3.11 -m venv .venv
  goto venv_ready
)

echo Python 3.11 or 3.12 x64 is required.
exit /b 1

:venv_ready
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python main.py
endlocal
