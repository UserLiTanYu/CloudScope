@echo off
cd /d "%~dp0..\backend"
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
pause
