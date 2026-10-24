@echo off
REM WasteWise AI Lite - one click: installs on first run, then starts API + website.
cd /d %~dp0
if not exist .venv (
  python -m venv .venv
  call .venv\Scripts\activate
  pip install -r backend\requirements.txt
) else (
  call .venv\Scripts\activate
)
if not exist frontend\node_modules (
  cd frontend
  call npm install
  cd ..
)
start "WasteWise API" cmd /k "call .venv\Scripts\activate && cd backend && uvicorn app.main:app --port 8000"
start "WasteWise Website" cmd /k "cd frontend && npm run dev"
echo Wait about 20 seconds (first start trains the models), then open http://localhost:5173
timeout /t 25 >nul
start http://localhost:5173
