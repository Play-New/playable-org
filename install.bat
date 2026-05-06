@echo off
REM Double-click shim for install.ps1.
REM Bypasses PowerShell's default execution policy for this run only —
REM it does NOT change the system-wide setting.

setlocal
set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install.ps1"
set "EXITCODE=%ERRORLEVEL%"
echo.
echo Premi un tasto per chiudere la finestra.
pause >nul
exit /b %EXITCODE%
