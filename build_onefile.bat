@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_release.ps1" -Mode onefile
exit /b %errorlevel%
