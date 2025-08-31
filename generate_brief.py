# generate_brief.py — long-form script, cleaner prose, gTTS en-GB, owner email in RSS

import os, re, hashlib
import datetime as dt
import feedparser
from bs4 import BeautifulSoup
from gtts import gTTS

SITE_BASE = "https://kupliauskas.github.io/Morning-Brief"
EP_DIR    = "docs/episodes"
FEED_PATH = "docs/feed.xml"
SHOW     = "Morning Brief"
OWNER_NAME  = "Adolfas"
OWNER_EMAIL = "kupliauskas@gmail.com"

VOICE_LANG = "en"     # gTTS
VOICE_TLD  = "co.uk"  # UK voice

RSS = {
    "markets": [
        ("ECB",  "https://www.ecb.europa.eu/press/press.xml"),
        ("BoE",  "https://www.bankofengland.co.uk/news/news.xml"),
        ("IMF",  "https://www.imf.org/en/News/rss"),
        ("EIA",  "https://www.eia.gov/rss/todayinenergy.xml"),
    ],
    "logistics": [
        ("UNCTAD",        "https://unctad.org/rss.xml"),
        ("Drewry",        "https://www.drewry.co.uk/rss"),
        ("MarineTraffic", "https://www.marinetraffic.com/blog/feed/"),
    ],
    "science": [
        ("arXiv (CS)", "http://export.arxiv.org/rss/cs"),
        ("bioRxiv",    "https://www.biorxiv.org/rss/latest.xml"),
        ("UKRI",       "https://www.ukri.org/feed/"),
    ],
    "geopolitics": [
        ("NATO",             "https://www.nato.int/cps/en/natohq/news.xml"),
        ("US Treasury/OFAC", "https://home.treasury.gov/rss/press-releases.xml"),
        ("EU Commission",    "https://ec.europa.eu/commission/presscorner/home/en/rss.xml"),
    ],
}

def strip_html(text: str) -> str:
    soup = BeautifulSoup(text or "", "html.parser")
    t = soup.get_text(" ", strip=True)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def get_entries(url, limit):
    feed = feedparser.parse(url)
    entries = []
    for e in feed.entries[:limit]:
        title = strip_html(getattr(e, "title", ""))
        # prefer summary/description where available
        desc = strip_html(getattr(e, "summary", "") or getattr(e, "description", ""))
        entries.append((title, desc))
    return entries

def collect():
    # target ~12–15 minutes: 4 items x 4–5 sentences across sections
    wanted = {"markets": 4, "logistics": 4, "science": 4, "geopolitics": 3}
    bag = {}
    for section, feeds in RSS.items():
        need = wanted[section]
        items = []
        for _, url in feeds:
            if need <= 0: break
            pull = min(need, 3)
            items += get_entries(url, pull)
            need = wanted[section] - len(items)
        bag[section] = items[:wanted[section]]
    return bag

def vignette(title, desc):
    # Build 4–5 short sentences, with natural pauses.
    bits = []
    if title: bits.append(title.rstrip(".") + ".")
    if desc:
        # break long summaries into 2–3 plain sentences
        s = re.split(r"(?<=[.!?])\s+", desc)
        for part in s[:3]:
            if 8 <= len(part.split()) <= 32:
                bits.append(part)
    # pad if too short
    while len(bits) < 4:
        bits.append("More details are expected in official releases.")
    return " ".join(bits)

def build_script(data):
    today = dt.date.today().strftime("%A %d %B %Y")
    out = []
    out += [
        f"{SHOW} — {today}.",
        "A sharp, plain-English briefing in five parts.",
        "",
        "Section one: Markets and Economics.",
    ]
    for t, d in data["markets"]:
        out.append(vignette(t, d))
        out.append("")  # pause

    out += ["Section two: Logistics and Industry."]
    for t, d in data["logistics"]:
        out.append(vignette(t, d))
        out.append("")

    out += ["Section three: Science and Technology."]
    for t, d in data["science"]:
        out.append(vignette(t, d))
        out.append("")

    out += ["Section four: Critical Geopolitics."]
    for t, d in data["geopolitics"]:
        out.append(vignette(t, d))
        out.append("")

    # Synthesis / Closing
    out += [
        "Section five: Synthesis.",
        "Theme: alignment — money, movement, science and policy pull in one direction.",
        "Red flag: trust but verify any single data point; look for corroboration across sources.",
        "Smart line: resilient operators turn volatility into margin.",
    ]
    # Force breathing room with blank lines (gTTS pauses on punctuation and breaks)
    script = "\n".join(out)
    # gentle pacing: add extra commas/em dashes to slow the read a touch
    script = script.replace(". ", ".  ")
    return script

# --- RSS helpers with owner email for verification ---
def rss_header(title, link, desc):
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
        f"<itunes:owner><itunes:name>{OWNER_NAME}</itunes:name><itunes:email>{OWNER_EMAIL}</itunes:email></itunes:owner>\n"
    )

def rss_item(title, mp3_url, pub_dt):
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

def rss_footer():
    return "</channel>\n</rss>\n"

def write_feed(items):
    xml = rss_header(SHOW, SITE_BASE, "Private daily briefing")
    for it in items:
        xml += rss_item(it["title"], it["url"], it["date"])
    xml += rss_footer()
    os.makedirs(os.path.dirname(FEED_PATH), exist_ok=True)
    with open(FEED_PATH, "w", encoding="utf-8") as f:
        f.write(xml)

if __name__ == "__main__":
    data = collect()
    text = build_script(data)

    os.makedirs(EP_DIR, exist_ok=True)
    today = dt.date.today()
    ep_name = f"{today:%Y-%m-%d}-morning-brief.mp3"
    ep_path = os.path.join(EP_DIR, ep_name)

    # Generate MP3 (gTTS en-GB); longer text => longer audio
    tts = gTTS(text, lang=VOICE_LANG, tld=VOICE_TLD)
    tts.save(ep_path)

    # Rebuild feed (cumulative)
    items = []
    for fn in sorted(os.listdir(EP_DIR)):
        if fn.endswith(".mp3"):
            date_part = "-".join(fn.split("-")[:3])
            try:
                pub_dt = dt.datetime.strptime(date_part, "%Y-%m-%d")
            except ValueError:
                pub_dt = dt.datetime.combine(dt.date.today(), dt.time(4, 0))
            items.append({
                "title": f"{SHOW} — {date_part}",
                "url": f"{SITE_BASE}/episodes/{fn}",
                "date": pub_dt,
            })
    write_feed(items)
    print(f"Created: {ep_path}")
