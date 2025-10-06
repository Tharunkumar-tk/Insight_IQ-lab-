import os
import io
import logging
from typing import Dict

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

try:
    import openai  # type: ignore
except Exception:
    openai = None  # graceful degradation

logger = logging.getLogger("llm")

SYSTEM_PROMPT = (
    "You are an analyst generating concise, actionable market and competitive insights. "
    "Write in bullet points, focus on product moves, partnerships, funding, risks, and opportunities."
)


def generate_insights(texts, company: str = "", domain: str = "") -> str:
    """
    Generate insights using OpenAI if OPENAI_API_KEY present. Fallback: template-based summarizer.
    """
    api_key = os.getenv('OPENAI_API_KEY', '')
    if openai and api_key:
        try:
            openai.api_key = api_key
            # Use responses API (compatible with >=2024-xx SDK) or chat.completions as available
            # NOTE: Keep simple to avoid version pitfalls
            prompt = f"Domain: {domain}\nCompany: {company}\nGiven the following items, summarize top insights as 6 bullets.\n" + "\n".join([f"- {t[:300]}" for t in texts[:20]])
            # Try Chat Completions
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500,
                )
                return resp.choices[0].message.get("content", "").strip()
            except Exception:
                pass
            # If the SDK variant differs, fallback to a minimal manual format
        except Exception as e:
            logger.warning("OpenAI call failed, using template fallback: %s", e)
    # Fallback template
    bullets = []
    for i, t in enumerate(texts[:6], start=1):
        bullets.append(f"- [{i}] {t[:140]}...")
    if not bullets:
        bullets = ["- No recent items available. Using local CSV fallback."]
    return "\n".join(bullets)
