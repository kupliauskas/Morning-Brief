
import os, io, json, datetime, hashlib
from pathlib import Path
import requests, feedparser
from bs4 import BeautifulSoup
from TTS.api import TTS
from pydub import AudioSegment
from rss_utils import write_feed

BASE_DIR = Path(__file__).parent.resolve()
DOCS_DIR = BASE_DIR / "docs"
EP_DIR = DOCS_DIR / "episodes"
EP_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = os.environ.get("GH_PAGES_URL", "https://example.com")

def fetch_headlines():
    out = {"markets":[], "logistics":[], "science":[], "geopol":[]}
    try:
        y = requests.get("https://query1.finance.yahoo.com/v1/finance/trending/US", timeout=15).json()
        tickers = [t['symbol'] for t in y.get('finance',{}).get('result',[{}])[0].get('quotes',[])][:5]
        if tickers:
            out["markets"].append("Trending tickers: " + ", ".join(tickers))
    except Exception:
        out["markets"].append("Markets data placeholder.")

    try:
        unctad = feedparser.parse("https://unctad.org/rss.xml")
        if unctad.entries:
            out["logistics"].append(unctad.entries[0].title)
    except Exception:
        out["logistics"].append("UNCTAD logistics headline placeholder.")

    try:
        arxiv = feedparser.parse("http://export.arxiv.org/api/query?search_query=all:energy&start=0&max_results=2&sortBy=submittedDate&sortOrder=descending")
        for e in arxiv.entries[:2]:
            out["science"].append(e.title)
    except Exception:
        out["science"].append("Science placeholder.")

    try:
        nato = feedparser.parse("https://www.nato.int/cps/en/natohq/news.htm?selectedLocale=en&format=xml")
        if nato.entries:
            out["geopol"].append(nato.entries[0].title)
    except Exception:
        out["geopol"].append("Geopolitics placeholder.")
    return out

TEMPLATE = """Morning Brief — {date}

1. Markets & Economics
{mk}

Conversation line: Oil softness eases inflation pressure.

2. Logistics & Industry
{lg}

Conversation line: Chokepoints risk Q4 retail prices.

3. Science & Technology
{sc}

Conversation line: Faster batteries could reset EV adoption.

4. Critical Geopolitics
{gp}

5. Synthesis / Closing
Theme: Signals across markets, supply chains, and tech.
Red flag: Data quality and policy shifts can change fast.
Smart line: Controlled volatility rewards prepared operators.
"""

def build_script(h):
    mk = " • " + "\n • ".join(h["markets"]) if h["markets"] else " • —"
    lg = " • " + "\n • ".join(h["logistics"]) if h["logistics"] else " • —"
    sc = " • " + "\n • ".join(h["science"]) if h["science"] else " • —"
    gp = " • " + "\n • ".join(h["geopol"]) if h["geopol"] else " • —"
    return TEMPLATE.format(
        date=datetime.date.today().strftime("%d %b %Y"),
        mk=mk, lg=lg, sc=sc, gp=gp
    )

def tts_coqui(text, out_path):
    # XTTS v2 multilingual; keep default English
    model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
    tts = TTS(model_name=model_name, progress_bar=False, gpu=False)
    tts.tts_to_file(text=text, file_path=out_path, speaker="en", language="en")

def ensure_index():
    index = DOCS_DIR / "index.html"
    if not index.exists():
        index.write_text("<!doctype html><meta charset='utf-8'><title>Morning Brief</title><p>Feed: <a href='feed.xml'>feed.xml</a>")

def load_existing_items():
    items = []
    for p in sorted(EP_DIR.glob("*.mp3")):
        parts = p.stem.split("-")
        date_str = "-".join(parts[0:3])
        title = "Morning Brief " + date_str
        url = f"{BASE_URL}/episodes/{p.name}"
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        guid = hashlib.sha1(p.name.encode()).hexdigest()
        items.append({"title": title, "url": url, "date": dt, "guid": guid})
    return items

def main():
    ensure_index()
    today = datetime.date.today().strftime("%Y-%m-%d")
    mp3_name = f"{today}-morning-brief.mp3"
    mp3_path = EP_DIR / mp3_name

    headlines = fetch_headlines()
    script = build_script(headlines)

    try:
        tts_coqui(script, str(mp3_path))
    except Exception:
        # fallback: 1-second silence to keep the pipeline alive
        AudioSegment.silent(duration=1000).export(str(mp3_path), format="mp3")

    items = load_existing_items()
    if not any(i["url"].endswith(mp3_name) for i in items):
        url = f"{BASE_URL}/episodes/{mp3_name}"
        dt = datetime.datetime.combine(datetime.date.today(), datetime.time(4,0))
        guid = hashlib.sha1(mp3_name.encode()).hexdigest()
        items.append({"title": f"Morning Brief {today}", "url": url, "date": dt, "guid": guid})

    write_feed(BASE_URL, str(DOCS_DIR), items)

if __name__ == "__main__":
    main()
