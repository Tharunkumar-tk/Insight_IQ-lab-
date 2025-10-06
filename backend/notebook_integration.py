import os
from typing import List, Tuple
import pandas as pd

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

from utils.fetchers import (
    fetch_gnews, fetch_serp_news, fetch_twitter_recent, fetch_reddit_search,
    fetch_finnhub_news, fetch_alphavantage_news,
)
from utils.sentiment import run_sentiment
from utils.forecast import forecast_timeseries, save_forecast_chart
from utils.llm_client import generate_insights

# NOTEBOOK_INTEGRATION: Safe wrappers informed by notebook logic.
# TODO: review thresholds, similarity filters, and any experimental parameters in the notebook.


def collect_data(company: str = "", domain: str = "", limit: int = 50) -> Tuple[List[dict], str]:
    """
    Attempt to collect data from multiple APIs in sequence. On failures or empty responses, return [].
    Returns (records, source_tag)
    """
    query = company or domain or "AI technology"

    # try multiple sources in priority order
    for fn in (fetch_gnews, fetch_serp_news):
        rows, tag = fn(query=query, limit=limit)
        if rows:
            # add basic sentiment
            for r in rows:
                label, score = run_sentiment((r.get("headline") or ""))
                r["sentiment"] = label
                r["sentiment_score"] = round(float(score), 3)
            return rows, tag
    # social sources as auxiliary content
    aux_rows = []
    for fn in (fetch_twitter_recent, fetch_reddit_search):
        rows, tag = fn(query=query, limit=min(20, limit))
        aux_rows.extend(rows)
    if aux_rows:
        for r in aux_rows:
            label, score = run_sentiment((r.get("headline") or ""))
            r["sentiment"] = label
            r["sentiment_score"] = round(float(score), 3)
        return aux_rows, 'api:social'
    return [], 'api:none'


def run_sentiment_wrapper(text: str):
    return run_sentiment(text)


def generate_insights_wrapper(texts: List[str], company: str = "", domain: str = "") -> str:
    return generate_insights(texts, company=company, domain=domain)


def forecast_timeseries_wrapper(df: pd.DataFrame, days: int = 30):
    return forecast_timeseries(df, days=days)
