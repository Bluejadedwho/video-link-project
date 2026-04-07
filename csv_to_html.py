import csv
import html
import os
from datetime import datetime, timezone
from urllib.parse import quote

INPUT_CSV = "records_summary.csv"
OUTPUT_HTML = "records_summary.html"

VISIBLE_COLUMNS = ["thumbnail_file", "platform", "title", "uploader"]

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Bluejadedwho/video-link-project/master/raw/"


def format_timestamp(raw):
    if not raw:
        return ""
    try:
        ts = int(float(raw.strip()))
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%b %d %Y")
    except (ValueError, OSError):
        return raw


def make_link(url, title):
    url = url.strip() if url else ""
    if not url.startswith("http"):
        return html.escape(title)
    return f'<a href="{html.escape(url)}" target="_blank">{html.escape(title)}</a>'


def make_thumb(path):
    import re
    path = path.strip() if path else ""
    if not path:
        return ""
    # Try to extract ID from bracket format: [1580908823328389].jpg
    m = re.search(r'\[([A-Za-z0-9_\-]+)\]\.jpg$', path)
    if not m:
        # Fall back to plain ID format: 1580908823328389.jpg
        m = re.search(r'([A-Za-z0-9_\-]+)\.jpg$', path)
    if m:
        url = GITHUB_RAW_BASE + m.group(1) + ".jpg"
        return f'<img src="{url}" alt="" loading="lazy">'
    return ""


def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Error: {INPUT_CSV} not found.")
        return

    with open(INPUT_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Sort newest first by timestamp
    def sort_key(r):
        try:
            return int(float(r.get("timestamp", "") or 0))
        except ValueError:
            return 0
    rows.sort(key=sort_key, reverse=True)

    row_count = len(rows)
    generated = datetime.now().strftime("%b %d %Y")

    table_rows = []
    for row in rows:
        title    = (row.get("title", "") or "").strip()
        url      = (row.get("url", "") or "").strip()
        uploader = (row.get("uploader", "") or "").strip()
        thumb    = (row.get("thumbnail_file", "") or "").strip()
        desc     = (row.get("description_preview", "") or "").strip()

        # Strip view count prefix from Facebook titles
        display_title = title
        if " | " in title:
            parts = title.split(" | ")
            display_title = " | ".join(parts[1:]) if len(parts) > 1 else title

        thumb_html = make_thumb(thumb)
        link = make_link(url, display_title)
        desc_html = f'<div class="desc">{html.escape(desc)}</div>' if desc else ""
        uploader_html = f'<div class="uploader">{html.escape(uploader)}</div>' if uploader else ""

        table_rows.append(
            f'<div class="card" data-search="{html.escape((display_title + " " + uploader + " " + desc).lower())}">'
            f'<div class="thumb">{thumb_html}</div>'
            f'<div class="info">{link}{uploader_html}{desc_html}</div>'
            f'</div>'
        )

    rows_html = "\n".join(table_rows)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Video Catalogue</title>
  <link rel="apple-touch-icon" href="icon.png">
  <link rel="icon" href="icon.png">
  <style>
    body {{
      background: #111;
      color: #e0e0e0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
      padding: 16px;
      margin: 0;
      overflow-x: hidden;
      word-break: break-word;
    }}
    .header {{ display: flex; align-items: center; justify-content: center; gap: 14px; margin-bottom: 4px; }}
    .header img {{ width: 72px; height: 72px; border-radius: 16px; }}
    h1 {{ color: #fff; font-size: 26px; margin: 0; }}
    .meta {{ color: #666; font-size: 12px; margin-bottom: 12px; text-align: center; }}
    #search {{
      width: 100%;
      padding: 10px 14px;
      margin-bottom: 8px;
      background: #1e1e1e;
      border: 1px solid #333;
      border-radius: 6px;
      color: #e0e0e0;
      font-size: 15px;
      box-sizing: border-box;
    }}
    #search::placeholder {{ color: #555; }}
    #search:focus {{ outline: none; border-color: #555; }}
    #count {{ color: #555; font-size: 12px; margin-bottom: 10px; }}
    .card {{
      display: flex;
      gap: 12px;
      padding: 10px 0;
      border-bottom: 1px solid #222;
      align-items: flex-start;
    }}
    .card:hover {{ background: #161616; }}
    .thumb {{ flex-shrink: 0; width: 90px; }}
    .thumb img {{ width: 90px; height: 60px; object-fit: cover; border-radius: 4px; display: block; }}
    .info {{ flex: 1; min-width: 0; }}
    .info a {{ color: #5aadff; text-decoration: none; font-size: 14px; font-weight: 500; line-height: 1.3; display: block; }}
    .info a:hover {{ text-decoration: underline; }}
    .uploader {{ color: #888; font-size: 12px; margin-top: 2px; }}
    .desc {{ color: #666; font-size: 12px; margin-top: 4px; line-height: 1.4; }}
    .hidden {{ display: none; }}
  </style>
</head>
<body>
  <div class="header">
    <img src="icon.png" alt="icon">
    <h1>Video Catalogue</h1>
  </div>
  <p class="meta">{row_count} records &mdash; generated {generated}</p>
  <input id="search" type="text" placeholder="Search titles, uploaders, platforms…" oninput="filterTable()">
  <div id="count"></div>
  <div id="catalogue">
{rows_html}
  </div>

  <script>
    function filterTable() {{
      const q = document.getElementById('search').value.toLowerCase();
      const cards = document.querySelectorAll('#catalogue .card');
      let visible = 0;
      cards.forEach(card => {{
        const match = card.dataset.search.includes(q);
        card.classList.toggle('hidden', !match);
        if (match) visible++;
      }});
      document.getElementById('count').textContent =
        q ? visible + ' of ' + cards.length + ' matching' : '';
    }}
  </script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Done. {row_count} records written to {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
