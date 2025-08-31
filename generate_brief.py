# generate_brief.py — upgraded sources, gTTS, self-contained RSS

import os
import datetime as dt
import hashlib
import feedparser
from gtts import gTTS

# --------- CONFIG ---------
SITE_BASE = "https://kupliauskas.github.io/Morning-Brief"
EP_DIR = "docs/episodes"
FEED_PATH = "docs/feed.xml"
EP_TITLE_PREFIX = "Morning Brief – "
VOICE_LANG = "en"       # gTTS language
VOICE_TLD = "co.uk"     # UK voice
# --------------------------

RSS_SOURCES = {
    "markets": [
        ("ECB", "https://www.ecb.europa.eu/press/press.xml"),
        ("Bank of England", "https://www.bankofengland.co.uk/news/news.xml"),
        ("IMF", "https://www.imf.org/en/News/rss"),
        ("EIA Today in Energy", "https://www.eia.gov/rss/todayinenergy.xml"),
    ],
    "logistics": [
        ("UNCTAD", "https://unctad.org/rss.xml"),
        ("Drewry", "https://www.drewry.co.uk/rss"),
        ("MarineTraffic", "https://www.marinetraffic.com/blog/feed/"),
    ],
    "science": [
        ("arXiv", "http://export.arxiv.org/rss/cs"),
        ("bioRxiv", "https://www.biorxiv.org/rss/latest.xml"),
        ("UKRI", "https://www.ukri.org/feed/"),
    ],
    "geopolitics": [
        ("NATO", "https://www.nato.int/cps/en/natohq/news.xml"),
        ("US Treasury/OFAC", "https://home.treasury.gov/rss/press-releases.xml"),
        ("EU Commission Press", "https://ec.europa.eu/commission/presscorner/home/en/rss.xml"),
    ],
}

def get_titles(url: str, limit: int) -> list[str]:
    try:
        feed = feedparser.parse(url)
        titles = [e.title for e in feed.entries[:limit] if getattr(e, "title", None)]
        return titles
    except Exception:
        return []

def collect_headlines() -> dict:
    # 3–4 headlines per section total (across sources)
    out = {}
    for section, feeds in RSS_SOURCES.items():
        titles = []
        for _, url in feeds:
            need = 4 - len(titles)
            if need <= 0:
                break
            titles += get_titles(url, need)
        out[section] = titles[:4]
    return out

def build_script(h: dict) -> str:
    today_human = dt.date.today().strftime("%d %B %Y")
    parts = [f"Morning Brief — {today_human}", ""]

    parts.append("Markets and Economics:")
    parts += [f"- {t}" for t in h.get("markets", [])]
    parts.append("Conversation line: Watch rates, energy and guidance together, not in isolation.")

    parts.append("\nLogistics and Industry:")
    parts += [f"- {t}" for t in h.get("logistics", [])]
    parts.append("Conversation line: Chokepoints and capacity decisions still drive landed cost.")

    parts.append("\nScience and Technology:")
    parts += [f"- {t}" for t in h.get("science", [])]
    parts.append("Conversation line: Useful innovation is the edge; ignore theatrics.")

    parts.append("\nCritical Geopolitics:")
    parts += [f"- {t}" for t in h.get("geopolitics", [])]
    parts.append("Conversation line: Sanctions and summits move supply routes first.")

    parts.append("\nClosing: Theme is alignment — money, movement, science, politics.")
    parts.append("Red flag: Low-quality data gives false confidence.")
    parts.append("Smart line: Prepared operators turn volatility into margin.")
    return "\n".join(parts)

# ---- Simple RSS (no external helper) ----
def rss_header(title: str, link: str, desc: str) -> str:
    from email.utils import formatdate
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">\n'
        "<channel>\n"
        f"<title>{title}</title>\n"
        f"<link>{link}</link>\n"
        f"<description>{desc}</description>\n"
        "<language>en-gb</language>\n"
        f"<lastBuildDate>{formatdate(localtime=True)}</lastBuildDate>\n"
        "<itunes:explicit>false</itunes:explicit>\n"
    )

def rss_item(title: str, mp3_url: str, pub_dt: dt.datetime) -> str:
    from email.utils import formatdate
    guid = hashlib.sha1(mp3_url.encode()).hexdigest()
    return (
        "<item>\n"
        f"<title>{title}</title>\n"
        f"<description>{title}</description>\n"
        f"<pubDate>{formatdate(pub_dt.timestamp(), localtime=True)}</pubDate>\n"
        f"<guid isPermaLink=\"false\">{guid}</guid>\n"
        f"<enclosure url=\"{mp3_url}\" length=\"0\" type=\"audio/mpeg\"/>\n"
        "</item>\n"
    )

def rss_footer() -> str:
    return "</channel>\n</rss>\n"

def write_feed(channel_title: str, site_base: str, items: list[dict], feed_path: str):
    xml = rss_header(channel_title, site_base, "Private daily briefing")
    for it in items:
        xml += rss_item(it["title"], it["url"], it["date"])
    xml += rss_footer()
    os.makedirs(os.path.dirname(feed_path), exist_ok=True)
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(xml)

# ------------- MAIN -------------
if __name__ == "__main__":
    headlines = collect_headlines()
    script = build_script(headlines)

    os.makedirs(EP_DIR, exist_ok=True)
    today = dt.date.today()
    ep_name = f"{today:%Y-%m-%d}-morning-brief.mp3"
    ep_path = os.path.join(EP_DIR, ep_name)

    # TTS (UK voice via gTTS)
    tts = gTTS(script, lang=VOICE_LANG, tld=VOICE_TLD)
    tts.save(ep_path)

    # Update RSS
    items = []
    # include existing files (keeps the feed cumulative)
    for fn in sorted(os.listdir(EP_DIR)):
        if fn.endswith(".mp3"):
            date_part = fn.split("-")[:3]
            try:
                pub_dt = dt.datetime.strptime("-".join(date_part), "%Y-%m-%d")
            except ValueError:
                pub_dt = dt.datetime.combine(dt.date.today(), dt.time(4, 0))
            items.append({
                "title": f"{EP_TITLE_PREFIX}{'-'.join(date_part)}",
                "url": f"{SITE_BASE}/episodes/{fn}",
                "date": pub_dt,
            })

    write_feed("Morning Brief", SITE_BASE, items, FEED_PATH)
    print(f"Created: {ep_path}")
    print(f"Updated feed: {FEED_PATH}")
