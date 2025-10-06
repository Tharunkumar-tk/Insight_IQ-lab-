import os
import csv
import random
from datetime import date, timedelta

DOMAINS = {
    "ai-ml": ["OpenAI","Anthropic","DeepMind","Hugging Face","Stability AI"],
    "cloud-saas": ["AWS","Microsoft Azure","Google Cloud","Salesforce","Oracle"],
    "cybersecurity": ["Palo Alto Networks","CrowdStrike","Fortinet","Cloudflare","Check Point"],
    "web3": ["Coinbase","Binance","ConsenSys","Chainalysis","Polygon Labs"],
    "ar-vr": ["Meta (Reality Labs)","HTC Vive","Niantic","Magic Leap","Varjo"],
    "robotics": ["Boston Dynamics","ABB Robotics","iRobot","Fanuc","UiPath"],
    "semiconductors": ["Intel","AMD","NVIDIA","TSMC","Qualcomm"],
    "quantum": ["IBM Quantum","Rigetti","IonQ","D-Wave Systems","Xanadu"],
    "consumer-electronics": ["Apple","Samsung Electronics","Sony","LG Electronics","Xiaomi"],
    "green-energy": ["Tesla Energy","Enphase Energy","Siemens Energy","Ørsted","First Solar"],
}

SOURCES = [
    "Reuters","Bloomberg","The Verge","TechCrunch","Wall Street Journal","Financial Times",
    "CNBC","Forbes","Wired","The Information","Ars Technica","Engadget","Protocol","VentureBeat"
]

ADJ_POS = ["surges","expands","announces","partners with","wins","tops","accelerates","outperforms","beats"]
ADJ_NEU = ["introduces","files","launches","reports","reveals","updates","mentions","notes","states"]
ADJ_NEG = ["falls","warns","delays","faces probe","misses","recalls","downgrades","cuts","suffers"]

random.seed(1337)  # deterministic randomness


def _random_date_within_18_months():
    days = random.randint(0, 30*18)
    return (date.today() - timedelta(days=days)).isoformat()


def _make_row(domain_slug: str) -> dict:
    company = random.choice(DOMAINS[domain_slug])
    sentiment_roll = random.random()
    if sentiment_roll < 0.4:
        sentiment = "positive"; score = random.uniform(0.21, 1.0); verb = random.choice(ADJ_POS)
    elif sentiment_roll < 0.8:
        sentiment = "neutral"; score = random.uniform(-0.2, 0.2); verb = random.choice(ADJ_NEU)
    else:
        sentiment = "negative"; score = random.uniform(-1.0, -0.21); verb = random.choice(ADJ_NEG)

    headline = f"{company} {verb} in {domain_slug.replace('-', ' ')} market"
    return {
        "date": _random_date_within_18_months(),
        "headline": headline,
        "source": random.choice(SOURCES),
        "sentiment": sentiment,
        "sentiment_score": f"{score:.3f}",
        "link": f"https://example.com/{domain_slug}/{company.lower().replace(' ', '-')}/{abs(hash(headline)) % 100000}"
    }


def generate_all(base_dir: str = None):
    here = os.path.dirname(os.path.dirname(__file__))  # backend/
    data_dir = os.path.join(here, 'data')
    os.makedirs(data_dir, exist_ok=True)

    for slug in DOMAINS.keys():
        rows = [_make_row(slug) for _ in range(100)]
        rows.sort(key=lambda r: r["date"], reverse=True)
        path = os.path.join(data_dir, f"{slug}.csv")
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=["date","headline","source","sentiment","sentiment_score","link"])
            w.writeheader()
            w.writerows(rows)
    return True


if __name__ == "__main__":
    ok = generate_all()
    print("CSV generation:", "ok" if ok else "failed")
