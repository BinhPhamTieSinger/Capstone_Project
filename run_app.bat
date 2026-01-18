@echo off
echo Starting Backend...
start "Capstone Backend" cmd /k "uvicorn backend.main:app --reload --port 8000"

echo Starting Frontend...
start "Capstone Frontend" cmd /k "cd frontend && npm run dev"

echo servers started!
