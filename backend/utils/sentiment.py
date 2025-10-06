import os
from typing import Tuple

# Env loader snippet
from dotenv import load_dotenv
import os as _os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Try VADER, fallback to heuristic
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer  # type: ignore
    _sia = SentimentIntensityAnalyzer()
    _has_vader = True
except Exception:
    _has_vader = False

POS_WORDS = {"good","great","excellent","positive","win","advantage","improve","success","growth","beat","upgrade"}
NEG_WORDS = {"bad","fail","loss","negative","drop","bug","vulnerability","delay","lawsuit","attack","downgrade"}


def run_sentiment(text: str) -> Tuple[str, float]:
    if not text or not str(text).strip():
        return "neutral", 0.0
    if _has_vader:
        try:
            score = float(_sia.polarity_scores(str(text))['compound'])
        except Exception:
            score = 0.0
    else:
        t = str(text).lower()
        pos = any(w in t for w in POS_WORDS)
        neg = any(w in t for w in NEG_WORDS)
        if pos and not neg:
            score = 0.3
        elif neg and not pos:
            score = -0.3
        else:
            score = 0.0
    # Map to label
    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"
    return label, score
