
from datetime import datetime
from email.utils import formatdate

def rss_header(title, link, description):
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
<title>{}</title>
<link>{}</link>
<description>{}</description>
<language>en-gb</language>
<lastBuildDate>{}</lastBuildDate>
<itunes:explicit>false</itunes:explicit>
""".format(title, link, description, formatdate(localtime=True))

def rss_item(title, mp3_url, pub_date, guid):
    return """<item>
<title>{}</title>
<description>{}</description>
<pubDate>{}</pubDate>
<guid isPermaLink="false">{}</guid>
<enclosure url="{}" length="0" type="audio/mpeg"/>
</item>
""".format(title, title, formatdate(pub_date.timestamp(), localtime=True), guid, mp3_url)

def rss_footer():
    return "</channel></rss>\n"

def write_feed(base_url, docs_dir, items):
    import os
    feed_path = os.path.join(docs_dir, "feed.xml")
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(rss_header("Morning Brief", base_url, "Private daily briefing"))
        for it in items:
            f.write(rss_item(it['title'], it['url'], it['date'], it['guid']))
        f.write(rss_footer())
    return feed_path
