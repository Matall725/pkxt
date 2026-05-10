@echo off
setlocal

cd /d "%~dp0"

set "DJANGO_SECRET_KEY=dev-secret-key"
set "DJANGO_ALLOW_SQLITE_BOOTSTRAP=1"

call :resolve_python
if errorlevel 1 goto :fail

if /i "%~1"=="--check" goto :check
if /i "%~1"=="--migrate-only" goto :migrate

echo [1/2] Applying migrations...
call %PYTHON_CMD% manage.py migrate
if errorlevel 1 goto :fail

echo [2/2] Starting local server on http://127.0.0.1:8000/ ...
start "" http://127.0.0.1:8000/accounts/login/
call %PYTHON_CMD% manage.py runserver
goto :end

:check
echo Running Django system check...
call %PYTHON_CMD% manage.py check
goto :end

:migrate
echo Applying migrations only...
call %PYTHON_CMD% manage.py migrate
goto :end

:resolve_python
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    goto :eof
)
if exist "E:\python.exe" (
    set "PYTHON_CMD=E:\python.exe"
    goto :eof
)
where py >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    goto :eof
)
where python >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :eof
)
echo Python was not found. Install Python or create .venv\Scripts\python.exe first.
exit /b 1

:fail
echo.
echo Startup failed.
pause
exit /b 1

:end
endlocal
