import os
import json
import logging
from typing import List, Dict
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd

# Load .env
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Logging
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'server.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("backend")

# Static dirs
STATIC_CHARTS = os.path.join(os.path.dirname(__file__), 'static', 'charts')
os.makedirs(STATIC_CHARTS, exist_ok=True)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Domain definitions and competitors
DOMAINS = {
    "ai-ml": {
        "name": "Artificial Intelligence & Machine Learning",
        "competitors": ["OpenAI","Anthropic","DeepMind","Hugging Face","Stability AI"],
    },
    "cloud-saas": {
        "name": "Cloud Computing & SaaS",
        "competitors": ["AWS","Microsoft Azure","Google Cloud","Salesforce","Oracle"],
    },
    "cybersecurity": {
        "name": "Cybersecurity & Data Privacy",
        "competitors": ["Palo Alto Networks","CrowdStrike","Fortinet","Cloudflare","Check Point"],
    },
    "web3": {
        "name": "Web3, Blockchain & Crypto",
        "competitors": ["Coinbase","Binance","ConsenSys","Chainalysis","Polygon Labs"],
    },
    "ar-vr": {
        "name": "Augmented & Virtual Reality",
        "competitors": ["Meta (Reality Labs)","HTC Vive","Niantic","Magic Leap","Varjo"],
    },
    "robotics": {
        "name": "Robotics & Automation",
        "competitors": ["Boston Dynamics","ABB Robotics","iRobot","Fanuc","UiPath"],
    },
    "semiconductors": {
        "name": "Semiconductors & Hardware",
        "competitors": ["Intel","AMD","NVIDIA","TSMC","Qualcomm"],
    },
    "quantum": {
        "name": "Quantum Computing",
        "competitors": ["IBM Quantum","Rigetti","IonQ","D-Wave Systems","Xanadu"],
    },
    "consumer-electronics": {
        "name": "Consumer Electronics",
        "competitors": ["Apple","Samsung Electronics","Sony","LG Electronics","Xiaomi"],
    },
    "green-energy": {
        "name": "Green Tech & Energy Innovation",
        "competitors": ["Tesla Energy","Enphase Energy","Siemens Energy","Ørsted","First Solar"],
    },
}

# Utilities
from .notebook_integration import (
    collect_data, run_sentiment_wrapper, generate_insights_wrapper,
    forecast_timeseries_wrapper
)
from .utils.sentiment import run_sentiment as _run_sent
from .utils.forecast import save_forecast_chart

app = FastAPI(title="InSightIQ API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health
@app.get("/api/health")
def health():
    return {"status": "ok"}

# Domains
@app.get("/api/domains")
def get_domains():
    items = []
    for slug, meta in DOMAINS.items():
        items.append({
            "slug": slug,
            "name": meta["name"],
            "competitors": [
                {"name": c, "logo": f"backend/logos/{slug}/{c.lower().replace(' ', '-')}.png"}
                for c in meta["competitors"]
            ]
        })
    return {"domains": items}

# Competitors by domain
@app.get("/api/competitors")
def get_competitors(domain: str = Query(...)):
    meta = DOMAINS.get(domain)
    if not meta:
        return JSONResponse(status_code=404, content={"error": "unknown domain"})
    comps = [{"name": c, "logo": f"backend/logos/{domain}/{c.lower().replace(' ', '-')}.png"} for c in meta["competitors"]]
    return {"domain": domain, "competitors": comps}

# CSV helper

def _load_domain_csv(domain: str, limit: int = 20):
    path = os.path.join(DATA_DIR, f"{domain}.csv")
    if not os.path.exists(path):
        return [], None
    df = pd.read_csv(path)
    # standardize
    recs = df.sample(min(limit, len(df)), random_state=None).to_dict(orient='records') if len(df) > limit else df.to_dict(orient='records')
    return recs, path

# News endpoint
@app.get("/api/news")
def api_news(company: str = Query(""), domain: str = Query("ai-ml"), limit: int = Query(20)):
    try:
        records, source = collect_data(company=company, domain=domain, limit=limit)
        if not records:
            raise Exception("empty")
        return {"items": records[:limit], "source": source}
    except Exception:
        fallback, csv_path = _load_domain_csv(domain, limit)
        if company:
            fallback = [r for r in fallback if company.lower() in (r.get("headline", "").lower())]
        return {"items": fallback[:limit], "source": f"fallback:csv", "csv": csv_path}

# Social endpoint (reuse same as news for now)
@app.get("/api/social")
def api_social(company: str = Query(""), domain: str = Query("ai-ml"), limit: int = Query(20)):
    try:
        records, source = collect_data(company=company, domain=domain, limit=limit)
        if not records:
            raise Exception("empty")
        return {"items": records[:limit], "source": source}
    except Exception:
        fallback, csv_path = _load_domain_csv(domain, limit)
        if company:
            fallback = [r for r in fallback if company.lower() in (r.get("headline", "").lower())]
        return {"items": fallback[:limit], "source": f"fallback:csv", "csv": csv_path}

# CSV sample for UI
@app.get("/api/csv-sample")
def csv_sample(domain: str = Query(...), limit: int = Query(20)):
    recs, path = _load_domain_csv(domain, limit)
    return {"items": recs[:limit], "csv": path}

# Forecast endpoint
@app.get("/api/forecast")
def api_forecast(company: str = Query("aggregate"), days: int = Query(30)):
    # Create a synthetic time series from CSV sentiment
    # value = rolling average of sentiment_score
    # Fallback if CSV missing
    used_domain = None
    for d in DOMAINS.keys():
        path = os.path.join(DATA_DIR, f"{d}.csv")
        if os.path.exists(path):
            used_domain = d
            break
    if not used_domain:
        return {"forecast": [], "chart": None, "source": "fallback:empty"}
    df = pd.read_csv(os.path.join(DATA_DIR, f"{used_domain}.csv"))
    df = df.sort_values("date")
    if company and company != "aggregate":
        df = df[df['headline'].str.contains(company, case=False, na=False)]
    # Build value column from sentiment_score
    try:
        ts = df[["date", "sentiment_score"]].copy()
        ts["value"] = pd.to_numeric(ts["sentiment_score"], errors='coerce').fillna(0.0)
        ts = ts[["date", "value"]]
    except Exception:
        ts = pd.DataFrame({"date": df.get("date", []), "value": [0.0]*len(df)})
    fdf, used_prophet = forecast_timeseries_wrapper(ts, days=days)
    chart_path = os.path.join(STATIC_CHARTS, f"forecast_{company.replace(' ','_')}_{days}.png")
    save_forecast_chart(fdf, chart_path)
    # Convert to JSON-friendly
    items = [
        {"date": str(r.ds)[:10], "yhat": float(r.yhat), "yhat_lower": float(getattr(r, 'yhat_lower', r.yhat)), "yhat_upper": float(getattr(r, 'yhat_upper', r.yhat))}
        for r in fdf.itertuples(index=False)
    ]
    return {"forecast": items, "chart": chart_path.replace("\\", "/"), "source": f"forecast:{'prophet' if used_prophet else 'naive'}"}

# Insights endpoint
@app.get("/api/insights")
def api_insights(company: str = Query(...), domain: str = Query("ai-ml")):
    try:
        items, source = collect_data(company=company, domain=domain, limit=20)
        texts = [(it.get("headline") or "") for it in items]
        insights = generate_insights_wrapper(texts, company=company, domain=domain)
        # sentiment summary
        sentiments = [it.get("sentiment_score") for it in items if it.get("sentiment_score") is not None]
        avg = float(pd.to_numeric(pd.Series(sentiments), errors='coerce').fillna(0.0).mean()) if sentiments else 0.0
        return {
            "company": company,
            "domain": domain,
            "insights": insights,
            "top_headlines": items,
            "social_posts": items[:10],
            "sentiment_summary": {"average": round(avg, 3), "count": len(sentiments)},
            "source": source,
        }
    except Exception:
        # Fallback to CSV
        recs, path = _load_domain_csv(domain, 50)
        filtered = [r for r in recs if company.lower() in (r.get("headline", "").lower())]
        texts = [(r.get("headline") or "") for r in filtered[:20]]
        insights = generate_insights_wrapper(texts, company=company, domain=domain)
        sentiments = [r.get("sentiment_score") for r in filtered]
        avg = float(pd.to_numeric(pd.Series(sentiments), errors='coerce').fillna(0.0).mean()) if sentiments else 0.0
        return {
            "company": company,
            "domain": domain,
            "insights": insights,
            "top_headlines": filtered[:20],
            "social_posts": filtered[:10],
            "sentiment_summary": {"average": round(avg, 3), "count": len(sentiments)},
            "source": "fallback:csv",
            "csv": path
        }

# Alerts webhook
class AlertPayload(BaseModel):
    title: str
    severity: str = "info"
    message: str
    meta: Dict = {}

@app.post("/api/webhook/alerts")
def webhook_alerts(payload: AlertPayload):
    path = os.path.join(LOG_DIR, 'alerts.log')
    os.makedirs(LOG_DIR, exist_ok=True)
    rec = {"title": payload.title, "severity": payload.severity, "message": payload.message, "meta": payload.meta}
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec) + "\n")
    logger.info("ALERT: %s", rec["title"])  # console line
    return {"status": "received"}

# Regenerate CSVs
@app.post("/api/regenerate-csvs")
def regenerate_csvs():
    from .scripts.generate_csvs import generate_all
    ok = generate_all()
    log_path = os.path.join(LOG_DIR, 'data_generation.log')
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write("regenerated\n")
    return {"status": "ok" if ok else "failed"}

# Run server for `python backend/app.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=False)
