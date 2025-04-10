import feedparser
import json
import sys
from datetime import datetime, timezone, timedelta

RSS_URL = "https://yutkat.github.io/new-neovim-plugin-rss/feed.xml"

if len(sys.argv) != 2:
    print("Usage: python fetch_rss.py <output_filename.json>")
    sys.exit(1)

output_filename = sys.argv[1]

feed = feedparser.parse(RSS_URL)

now_jst = datetime.now(timezone(timedelta(hours=9)))

latest_entries = []
for entry in feed.entries:
    entry_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=0)))
    
    if entry_date.date() == now_jst.date():
        latest_entries.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published
        })

with open(output_filename, "w") as f:
    json.dump(latest_entries, f, indent=2, ensure_ascii=False)

