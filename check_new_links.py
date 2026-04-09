"""
Find links from your Messages database that are not yet in the catalogue.

Default behavior:
- Only queues Instagram links, because Facebook share links have been noisy
  and unreliable in this project.
- Normalizes links before comparison so the same reel shared with different
  tracking query strings is not treated as new again.

Optional:
- Set INCLUDE_FACEBOOK=1 in your shell before running if you want Facebook links.
  Example: INCLUDE_FACEBOOK=1 python3 check_new_links.py
"""
import csv
import os
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

CATALOGUE_CSV = "records_summary.csv"
MESSAGES_DB = Path.home() / "Library" / "Messages" / "chat.db"
NEW_LINKS_FILE = Path("new_links.txt")
SKIPPED_FILE = Path("skipped_non_instagram_links.txt")

APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
URL_RE = re.compile(r"https?://[^\s<>'\")]+", re.IGNORECASE)
INCLUDE_FACEBOOK = os.getenv("INCLUDE_FACEBOOK", "").strip().lower() in {"1", "true", "yes", "y"}


def clean_url(url: str) -> str:
    return url.rstrip('.,)\]}>\"\'')


def is_supported_url(url: str) -> bool:
    low = url.lower()
    if "instagram.com" in low:
        return True
    if INCLUDE_FACEBOOK and ("facebook.com" in low or "fb.watch" in low):
        return True
    return False


def normalize_url(url: str) -> str:
    url = clean_url(url)
    parts = urlsplit(url)
    netloc = parts.netloc.lower().replace("m.instagram.com", "www.instagram.com")
    netloc = netloc.replace("instagram.com", "www.instagram.com") if netloc.endswith("instagram.com") else netloc
    netloc = netloc.replace("m.facebook.com", "www.facebook.com")
    path = re.sub(r"/+", "/", parts.path or "/")
    path = path.rstrip("/")
    if not path:
        path = "/"

    # Drop tracking query strings. For this project they have caused duplicate detection issues.
    query = ""
    fragment = ""

    # Canonicalize some common Instagram/Facebook paths.
    low_path = path.lower()
    if "instagram.com" in netloc:
        for prefix in ("/reel/", "/p/", "/tv/"):
            if low_path.startswith(prefix):
                slug = path.split("/")
                if len(slug) >= 3:
                    path = f"{prefix}{slug[2]}"
                break
    elif "facebook.com" in netloc or "fb.watch" in netloc:
        path = path.rstrip("/")

    return urlunsplit((parts.scheme.lower() or "https", netloc, path, query, fragment))



def extract_urls(text: str):
    if not text:
        return []
    return [clean_url(m.group(0)) for m in URL_RE.finditer(text)]



def load_catalogue_urls():
    urls = set()
    try:
        with open(CATALOGUE_CSV, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                raw = row.get("url", "").strip()
                if raw:
                    urls.add(normalize_url(raw))
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
            if not urls:
                continue
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

            for url in urls:
                links.append((url, date_str))
    finally:
        conn.close()
    return links



def main():
    platform_note = "Instagram only" if not INCLUDE_FACEBOOK else "Instagram + Facebook"
    print(f"Loading catalogue ({platform_note})...")
    existing = load_catalogue_urls()
    print(f"  {len(existing)} normalized URLs already in catalogue\n")

    print("Reading iMessages...")
    all_links = get_message_links()

    seen_norm = set()
    new_links = []
    skipped = []
    skipped_duplicates = 0

    for url, date in all_links:
        if not is_supported_url(url):
            if "facebook.com" in url.lower() or "fb.watch" in url.lower():
                skipped.append((url, date))
            continue

        norm = normalize_url(url)
        if norm in existing or norm in seen_norm:
            skipped_duplicates += 1
            continue

        new_links.append((url, date))
        seen_norm.add(norm)

    if skipped and not INCLUDE_FACEBOOK:
        with open(SKIPPED_FILE, "w", encoding="utf-8") as f:
            for url, date in skipped:
                f.write(f"[{date}] {url}\n")
        print(f"  Ignored {len(skipped)} Facebook link(s). Saved list to {SKIPPED_FILE.name}.")

    if skipped_duplicates:
        print(f"  Skipped {skipped_duplicates} duplicate/already-catalogued link variant(s).")

    if not new_links:
        NEW_LINKS_FILE.write_text("", encoding="utf-8")
        print("\nNo new supported links found. new_links.txt was cleared.")
        return

    print(f"\nFound {len(new_links)} new supported link(s) not yet in catalogue:\n")
    for url, date in new_links:
        print(f"  [{date}] {url}")

    with open(NEW_LINKS_FILE, "w", encoding="utf-8") as f:
        for url, _ in new_links:
            f.write(url + "\n")

    print(f"\nSaved to {NEW_LINKS_FILE.name} — ready for yt-dlp")


if __name__ == "__main__":
    main()
