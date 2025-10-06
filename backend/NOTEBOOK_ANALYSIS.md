# Notebook Analysis: AI INTEL MODULE 3.ipynb

Summary
- The notebook contains multi-source data collection, enrichment, and filtering for AI-related content.
- Key sources implemented: NewsAPI, Reddit (PRAW), Hacker News (Algolia API), arXiv (feedparser), YouTube (Data API), Twitter v2 recent search.
- Enrichment includes VADER sentiment (with NLTK download), TextBlob polarity in an earlier cell, URL and timestamp normalization, and AI relevance filtering via sentence-transformers + spaCy NER + keyword/rules.
- Several cells contain environment variable assignments to embed API keys (NewsAPI, Reddit, YouTube, Twitter). In production we read these from backend/.env.

What we integrated as production modules
- utils/fetchers.py:
  - fetch_gnews (GNews)
  - fetch_serp_news (SerpAPI Google News)
  - fetch_twitter_recent (Twitter v2)
  - fetch_reddit_search (public JSON fallback for Reddit to avoid PRAW)
  - fetch_finnhub_news, fetch_alphavantage_news (minimal shells)
  - All requests include retries with exponential backoff; 429 honored.
- utils/sentiment.py:
  - run_sentiment() using VADER if available; otherwise rule-based fallback.
- utils/forecast.py:
  - forecast_timeseries(): Prophet wrapper with a robust naive fallback if Prophet isn’t installed.
  - save_forecast_chart(): matplotlib PNG chart generator into backend/static/charts/.
- utils/llm_client.py:
  - generate_insights(): OpenAI wrapper reading OPENAI_API_KEY from .env; fallback to template summarizer if API fails or key missing.
- notebook_integration.py:
  - collect_data(): tries GNews → SerpAPI → social (Twitter/Reddit) with sentiment tagging; returns standardized records.
  - run_sentiment_wrapper(), generate_insights_wrapper(), forecast_timeseries_wrapper() adapters.

Cells converted or mapped
- Data collection (NewsAPI, Reddit, HN, arXiv, YouTube, Twitter): mapped to fetchers.py (with PRAW replaced by public JSON endpoint for Reddit to reduce dependency and complexity). HN/arXiv not included initially to keep a smaller dependency surface; can be added later.
- Sentiment (VADER/TextBlob): consolidated in utils/sentiment.py using VADER + heuristic fallback. TextBlob omitted to simplify deps.
- AI filtering (sentence-transformers + spaCy): left as a TODO for later optional enhancement; not required for the initial endpoints.
- Forecasting (Prophet): not explicitly present in the provided snippet; we added a Prophet wrapper following standard Prophet usage with a naive fallback.

Endpoints implemented in backend/app.py
- GET /api/domains
- GET /api/competitors?domain=<slug>
- GET /api/news?company=<name>&domain=<slug>&limit=20
- GET /api/social?company=<name>&domain=<slug>&limit=20
- GET /api/csv-sample?domain=<slug>
- GET /api/forecast?company=<name>&days=30
- GET /api/insights?company=<name>&domain=<slug>
- POST /api/webhook/alerts
- POST /api/regenerate-csvs
- GET /api/health

Required manual review / TODOs
- If you want parity with notebook’s AI filtering:
  - Add sentence-transformers and spaCy (en_core_web_sm) and wire their relevance scoring into collect_data().
- Extend fetchers to include HN and arXiv as in the notebook.
- If you need TextBlob-based scoring in addition to VADER, add the dependency and a switch.
- Consider caching and bulk pagination for higher throughput and quota savings.

Recommended improvements
- Add request-level caching (e.g., requests-cache) with short TTLs to reduce repeated API calls.
- Add structured rate-limit handling per API with jittered backoff and logging of quota status.
- Implement a small in-memory LRU cache for insights per (company, domain) for a few minutes.
- Add async variants for fetchers if you increase concurrency (FastAPI can support it).
- Add data validation with Pydantic models for standardized record schema.
