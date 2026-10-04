@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_release.ps1" -Mode both
if errorlevel 1 (
  echo.
  echo BUILD FAILED. Review the error above.
  exit /b 1
)
echo.
echo RELEASE READY in the release folder.
endlocal
