@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Logs dir
if not exist backend\logs mkdir backend\logs

REM Create venv
python -m venv .venv
call .\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt

REM Create default logo asset
python frontend\assets\create_default_logo.py

REM Generate CSVs
python backend\scripts\generate_csvs.py

REM Ensure .env exists
if not exist backend\.env (
  copy backend\.env.example backend\.env > NUL
  echo Created backend\.env from .env.example. Please add your API keys.>> backend\logs\setup.log
)

REM Sanity check
python -c "import pandas, requests; print('ok')" >> backend\logs\setup.log 2>>&1

REM Start backend
start "backend" cmd /c "python backend\app.py > backend\logs\backend.log 2>>&1"

REM Start frontend static server
start "frontend" cmd /c "python -m http.server 3000 -d frontend > backend\logs\frontend.log 2>>&1"

REM Report missing logos and keys
python - <<PY
import os
from backend.scripts.generate_csvs import DOMAINS
missing = []
for slug, comps in DOMAINS.items():
    for c in comps:
        fname = c.lower().replace(' ','-') + '.png'
        path = os.path.join('backend','logos',slug,fname)
        if not os.path.exists(path):
            missing.append(path)
print('MISSING_LOGOS='+';'.join(missing))
required = ['OPENAI_API_KEY','GNEWS_API_KEY','SERPAPI_KEY','FINNHUB_KEY','ALPHAVANTAGE_KEY','REDDIT_CLIENT_ID','REDDIT_CLIENT_SECRET','REDDIT_USER_AGENT','TWITTER_BEARER_TOKEN','SLACK_WEBHOOK_URL']
vals = {}
path = os.path.join('backend','.env')
if os.path.exists(path):
    for line in open(path,encoding='utf-8'):
        if '=' in line and not line.strip().startswith('#'):
            k,v = line.strip().split('=',1)
            vals[k]=v
missing_keys = [k for k in required if not vals.get(k)]
print('MISSING_KEYS='+';'.join(missing_keys))
PY

echo.
echo Done. Open:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000

echo If any logos are missing, please upload them to backend\logos\^<slug^>\^<competitor^>.png and re-run setup.
