import os
import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
from gtts import gTTS
from rss_utils import rss_header, rss_item, rss_footer, write_feed

# --- Content fetchers (simple headlines only) ---
def get_yahoo_headlines():
    url = "https://finance.yahoo.com/rss/topstories"
    feed = feedparser.parse(url)
    return [entry.title for entry in feed.entries[:3]]

def get_unctad_headlines():
    url = "https://unctad.org/rss.xml"
    feed = feedparser.parse(url)
    return [entry.title for entry in feed.entries[:2]]

def get_arxiv_headlines():
    url = "http://export.arxiv.org/rss/cs"
    feed = feedparser.parse(url)
    return [entry.title for entry in feed.entries[:2]]

def get_nato_headlines():
    url = "https://www.nato.int/cps/en/natohq/news.xml"
    feed = feedparser.parse(url)
    return [entry.title for entry in feed.entries[:2]]

# --- Script builder ---
def build_script():
    today = datetime.date.today().strftime("%d %B %Y")
    lines = [f"Morning Brief – {today}", ""]

    lines.append("Markets and Economics:")
    for h in get_yahoo_headlines():
        lines.append(" - " + h)
    lines.append("Conversation line: Markets remain in focus.")

    lines.append("\nLogistics and Industry:")
    for h in get_unctad_headlines():
        lines.append(" - " + h)
    lines.append("Conversation line: Supply chains continue to shift.")

    lines.append("\nScience and Technology:")
    for h in get_arxiv_headlines():
        lines.append(" - " + h)
    lines.append("Conversation line: Innovation pace is accelerating.")

    lines.append("\nGeopolitics:")
    for h in get_nato_headlines():
        lines.append(" - " + h)
    lines.append("Conversation line: Security risks stay elevated.")

    lines.append("\nClosing: Stay sharp, one theme connects them all: resilience.")
    return "\n".join(lines)

# --- Main ---
if __name__ == "__main__":
    script = build_script()

    today = datetime.date.today().strftime("%Y-%m-%d")
    outdir = "docs/episodes"
    os.makedirs(outdir, exist_ok=True)
    mp3_path = f"{outdir}/{today}-morning-brief.mp3"

    # Use gTTS for en-GB voice
    tts = gTTS(script, lang="en", tld="co.uk")
    tts.save(mp3_path)

    # Update feed
    feed_path = "docs/feed.xml"
    rss_url = f"https://kupliauskas.github.io/Morning-Brief/episodes/{today}-morning-brief.mp3"

    items = [rss_item(f"Morning Brief – {today}", rss_url, today)]
    write_feed("Morning Brief", "https://kupliauskas.github.io/Morning-Brief", items, feed_path)

    print(f"Generated {mp3_path} and updated feed.xml")
