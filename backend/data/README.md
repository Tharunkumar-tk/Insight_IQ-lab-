# Data CSVs for InSightIQ

Each CSV is placed under backend/data/ and named by domain slug:
- ai-ml.csv
- cloud-saas.csv
- cybersecurity.csv
- web3.csv
- ar-vr.csv
- robotics.csv
- semiconductors.csv
- quantum.csv
- consumer-electronics.csv
- green-energy.csv

Schema columns:
- date: ISO YYYY-MM-DD
- headline: short description
- source: publisher/site name
- sentiment: positive | neutral | negative
- sentiment_score: float -1.0 .. 1.0 (3 decimal precision)
- link: URL string

Regeneration:
- The CSVs can be regenerated locally at any time without external APIs.
- Use the endpoint POST /api/regenerate-csvs or run the script directly:
  - Windows: python backend\scripts\generate_csvs.py
  - bash: python backend/scripts/generate_csvs.py

Notes:
- When external API quotas fail, the backend falls back to these CSVs.
- You can replace these with real data exports as needed, preserving schema.
