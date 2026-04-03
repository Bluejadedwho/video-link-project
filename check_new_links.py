"""
Run this to see which links from your iMessages are NOT yet in your catalogue.
Usage: python3 check_new_links.py
"""
import csv
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta

CATALOGUE_CSV = "records_summary.csv"
MESSAGES_DB = Path.home() / "Library" / "Messages" / "chat.db"

APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

VIDEO_PATTERNS = [
    r'https?://(?:www\.|m\.)?facebook\.com/\S+',
    r'https?://(?:www\.)?instagram\.com/\S+',
    r'https?://(?:www\.)?youtube\.com/\S+',
    r'https?://youtu\.be/\S+',
    r'https?://(?:www\.)?tiktok\.com/\S+',
    r'https?://(?:www\.)?vimeo\.com/\S+',
]

def extract_urls(text):
    urls = []
    for pattern in VIDEO_PATTERNS:
        found = re.findall(pattern, text or "")
        urls.extend(u.rstrip('.,)"\'>') for u in found)
    return urls

def load_catalogue_urls():
    urls = set()
    try:
        with open(CATALOGUE_CSV, encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                u = row.get('url', '').strip()
                if u:
                    urls.add(u)
    except FileNotFoundError:
        print(f"Warning: {CATALOGUE_CSV} not found")
    return urls

def get_message_links():
    if not MESSAGES_DB.exists():
        print("Messages database not found. Make sure Terminal has Full Disk Access.")
        return []

    conn = sqlite3.connect(f"file:{MESSAGES_DB}?mode=ro", uri=True)
    links = []
    try:
        rows = conn.execute(
            "SELECT text, date FROM message WHERE is_from_me=1 AND text IS NOT NULL ORDER BY date DESC"
        ).fetchall()
        for text, date in rows:
            urls = extract_urls(text)
            for url in urls:
                # Convert Apple timestamp
                try:
                    v = int(date)
                    av = abs(v)
                    if av > 10**16:
                        seconds = v / 1_000_000_000
                    elif av > 10**13:
                        seconds = v / 1_000_000
                    else:
                        seconds = v
                    dt = APPLE_EPOCH + timedelta(seconds=seconds)
                    date_str = dt.strftime("%b %d %Y")
                except Exception:
                    date_str = "unknown"
                links.append((url, date_str))
    finally:
        conn.close()
    return links

def main():
    print("Loading catalogue...")
    existing = load_catalogue_urls()
    print(f"  {len(existing)} URLs already in catalogue\n")

    print("Reading iMessages...")
    all_links = get_message_links()

    seen = set()
    new_links = []
    for url, date in all_links:
        if url not in existing and url not in seen:
            new_links.append((url, date))
            seen.add(url)

    if not new_links:
        print("No new links found — your catalogue is up to date!")
        return

    print(f"Found {len(new_links)} new links not yet in catalogue:\n")
    for url, date in new_links:
        print(f"  [{date}] {url}")

    # Also save to a file for yt-dlp
    out = Path("new_links.txt")
    with open(out, "w") as f:
        for url, _ in new_links:
            f.write(url + "\n")
    print(f"\nSaved to new_links.txt — ready for yt-dlp")

if __name__ == "__main__":
    main()
