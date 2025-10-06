import os
import time
import random
import logging
from typing import List, Dict, Tuple

import requests

# Environment loader
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger("fetchers")

DEFAULT_HEADERS = {"User-Agent": "InSightIQ/1.0"}

# Simple retry with exponential backoff
def _request_with_retries(method: str, url: str, *, params=None, headers=None, json=None, max_retries: int = 3, base_delay: float = 0.5):
    headers = {**DEFAULT_HEADERS, **(headers or {})}
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.request(method, url, params=params, headers=headers, json=json, timeout=30)
            if resp.status_code == 429:
                delay = base_delay * (2 ** (attempt - 1)) + random.random() * 0.2
                logger.warning(f"Rate limited on {url} (429). Backing off {delay:.2f}s (attempt {attempt}/{max_retries})")
                time.sleep(delay)
                continue
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_exc = e
            delay = base_delay * (2 ** (attempt - 1)) + random.random() * 0.2
            logger.warning(f"Request error {e} on {url}. Retrying in {delay:.2f}s (attempt {attempt}/{max_retries})")
            time.sleep(delay)
    raise last_exc

# Each fetcher returns standardized records: [{date, headline, source, sentiment, sentiment_score, link}]

def fetch_gnews(query: str, limit: int = 20) -> Tuple[List[Dict], str]:
    api_key = os.getenv("GNEWS_API_KEY", "")
    if not api_key:
        return [], 'api:gnews_missing_key'
    try:
        url = "https://gnews.io/api/v4/search"
        params = {"q": query, "lang": "en", "token": api_key, "max": min(limit, 100)}
        resp = _request_with_retries("GET", url, params=params)
        data = resp.json()
        out = []
        for a in data.get("articles", []):
            out.append({
                "date": (a.get("publishedAt") or "")[:10],
                "headline": a.get("title") or "",
                "source": (a.get("source") or {}).get("name") or "GNews",
                "sentiment": None,
                "sentiment_score": None,
                "link": a.get("url") or ""
            })
        return out, 'api:gnews'
    except Exception as e:
        logger.exception("GNews fetch failed: %s", e)
        return [], 'api:gnews_error'

def fetch_serp_news(query: str, limit: int = 20) -> Tuple[List[Dict], str]:
    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return [], 'api:serp_missing_key'
    try:
        url = "https://serpapi.com/search.json"
        params = {"engine": "google", "q": query, "tbm": "nws", "api_key": api_key}
        resp = _request_with_retries("GET", url, params=params)
        items = resp.json().get("news_results", [])
        out = []
        for it in items[:limit]:
            out.append({
                "date": (it.get("date") or "")[:10],
                "headline": it.get("title") or "",
                "source": it.get("source") or "Google News",
                "sentiment": None,
                "sentiment_score": None,
                "link": it.get("link") or ""
            })
        return out, 'api:serp'
    except Exception as e:
        logger.exception("SerpAPI fetch failed: %s", e)
        return [], 'api:serp_error'

# Placeholders for social/finance APIs (implementations can be expanded)

def fetch_twitter_recent(query: str, limit: int = 20) -> Tuple[List[Dict], str]:
    token = os.getenv("TWITTER_BEARER_TOKEN", "")
    if not token:
        return [], 'api:twitter_missing_key'
    try:
        url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": query,
            "tweet.fields": "created_at,public_metrics,lang",
            "max_results": min(limit, 100)
        }
        headers = {"Authorization": f"Bearer {token}"}
        resp = _request_with_retries("GET", url, params=params, headers=headers)
        out = []
        for t in resp.json().get("data", [])[:limit]:
            out.append({
                "date": (t.get("created_at") or "")[:10],
                "headline": (t.get("text") or "").replace("\n", " ")[:140],
                "source": "Twitter",
                "sentiment": None,
                "sentiment_score": None,
                "link": f"https://twitter.com/i/web/status/{t.get('id')}"
            })
        return out, 'api:twitter'
    except Exception as e:
        logger.exception("Twitter fetch failed: %s", e)
        return [], 'api:twitter_error'

def fetch_reddit_search(query: str, limit: int = 20) -> Tuple[List[Dict], str]:
    # To avoid PRAW dependency in this minimal wrapper, use Reddit JSON search (limited)
    try:
        url = "https://www.reddit.com/search.json"
        params = {"q": query, "limit": min(limit, 50), "sort": "new"}
        headers = {"User-Agent": "InSightIQ/1.0"}
        resp = _request_with_retries("GET", url, params=params, headers=headers)
        out = []
        for c in resp.json().get("data", {}).get("children", [])[:limit]:
            d = c.get("data", {})
            out.append({
                "date": time.strftime('%Y-%m-%d', time.gmtime(d.get("created_utc", time.time()))),
                "headline": d.get("title") or "",
                "source": "Reddit",
                "sentiment": None,
                "sentiment_score": None,
                "link": f"https://www.reddit.com{d.get('permalink','')}"
            })
        return out, 'api:reddit_public'
    except Exception as e:
        logger.exception("Reddit fetch failed: %s", e)
        return [], 'api:reddit_error'

# Financial APIs (Finnhub, AlphaVantage) minimal stubs

def fetch_finnhub_news(symbol: str, limit: int = 20) -> Tuple[List[Dict], str]:
    key = os.getenv("FINNHUB_KEY", "")
    if not key:
        return [], 'api:finnhub_missing_key'
    try:
        url = "https://finnhub.io/api/v1/company-news"
        # Default to last 7 days
        from datetime import date, timedelta
        to_d = date.today()
        from_d = to_d - timedelta(days=7)
        params = {"symbol": symbol, "from": str(from_d), "to": str(to_d), "token": key}
        resp = _request_with_retries("GET", url, params=params)
        out = []
        for a in resp.json()[:limit]:
            out.append({
                "date": time.strftime('%Y-%m-%d', time.gmtime(a.get("datetime", time.time()))),
                "headline": a.get("headline") or "",
                "source": a.get("source") or "Finnhub",
                "sentiment": None,
                "sentiment_score": None,
                "link": a.get("url") or ""
            })
        return out, 'api:finnhub'
    except Exception as e:
        logger.exception("Finnhub fetch failed: %s", e)
        return [], 'api:finnhub_error'

def fetch_alphavantage_news(symbol: str, limit: int = 20) -> Tuple[List[Dict], str]:
    key = os.getenv("ALPHAVANTAGE_KEY", "")
    if not key:
        return [], 'api:alphavantage_missing_key'
    try:
        url = "https://www.alphavantage.co/query"
        params = {"function": "NEWS_SENTIMENT", "tickers": symbol, "apikey": key}
        resp = _request_with_retries("GET", url, params=params)
        out = []
        for it in resp.json().get("feed", [])[:limit]:
            out.append({
                "date": (it.get("time_published") or "")[:8],
                "headline": it.get("title") or "",
                "source": it.get("source") or "AlphaVantage",
                "sentiment": None,
                "sentiment_score": None,
                "link": it.get("url") or ""
            })
        return out, 'api:alphavantage'
    except Exception as e:
        logger.exception("AlphaVantage fetch failed: %s", e)
        return [], 'api:alphavantage_error'
