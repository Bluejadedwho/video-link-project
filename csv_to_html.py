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
    m = re.search(r'(\w+)\.jpg$', path)
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

    row_count = len(rows)
    generated = datetime.now().strftime("%b %d %Y")

    table_rows = []
    for row in rows:
        title     = (row.get("title", "") or "").strip()
        url       = (row.get("url", "") or "").strip()
        platform  = (row.get("platform", "") or "").strip()
        uploader  = (row.get("uploader", "") or "").strip()
        ts        = (row.get("timestamp", "") or "").strip()
        tsrc      = (row.get("transcript_source", "") or "").strip()
        thumb     = (row.get("thumbnail_file", "") or "").strip()
        desc      = (row.get("description_preview", "") or "").strip()

        # Shorten title for display (strip view counts prefix for Facebook)
        display_title = title
        if " | " in title:
            parts = title.split(" | ")
            display_title = " | ".join(parts[1:]) if len(parts) > 1 else title

        cells = [
            f'<td class="col-thumb">{make_thumb(thumb)}</td>',
            f'<td class="col-platform">{html.escape(platform)}</td>',
            f'<td class="col-title">{make_link(url, display_title)}'
            + (f'<div class="desc">{html.escape(desc[:120])}{"…" if len(desc)>120 else ""}</div>' if desc else "")
            + '</td>',
            f'<td class="col-uploader">{html.escape(uploader)}</td>',
        ]
        table_rows.append("<tr>" + "".join(cells) + "</tr>")

    rows_html = "\n    ".join(table_rows)

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
      font-size: 13px;
      padding: 16px;
      margin: 0;
    }}
    .header {{ display: flex; align-items: center; justify-content: center; gap: 14px; margin-bottom: 4px; }}
    .header img {{ width: 72px; height: 72px; border-radius: 16px; }}
    h1 {{ color: #fff; font-size: 26px; margin: 0; }}
    .meta {{ color: #666; font-size: 12px; margin-bottom: 12px; text-align: center; }}
    #search {{
      width: 100%;
      max-width: 100%;
      padding: 10px 14px;
      margin-bottom: 14px;
      background: #1e1e1e;
      border: 1px solid #333;
      border-radius: 6px;
      color: #e0e0e0;
      font-size: 15px;
      box-sizing: border-box;
    }}
    #search::placeholder {{ color: #555; }}
    #search:focus {{ outline: none; border-color: #555; }}

    .wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      table-layout: auto;
    }}
    th {{
      background: #1a1a1a;
      color: #888;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.05em;
      padding: 8px 10px;
      text-align: left;
      border-bottom: 2px solid #2a2a2a;
      position: sticky;
      top: 0;
      z-index: 1;
    }}
    td {{
      padding: 6px 10px;
      border-bottom: 1px solid #1e1e1e;
      vertical-align: middle;
    }}
    tr:hover td {{ background: #181818; }}
    a {{ color: #5aadff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    .col-thumb    {{ width: 70px; text-align: center; }}
    .col-platform {{ width: 80px; }}
    .col-title    {{ }}
    .col-uploader {{ width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}

    @media (max-width: 600px) {{
      .col-platform {{ display: none; }}
      .col-uploader {{ display: none; }}
      th.col-platform {{ display: none; }}
      th.col-uploader {{ display: none; }}
    }}

    .col-title td, td.col-title {{
      overflow: hidden;
    }}
    td.col-title a {{
      display: block;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .desc {{
      color: #666;
      font-size: 11px;
      margin-top: 3px;
      line-height: 1.3;
      white-space: normal;
    }}
    img {{
      width: 72px;
      height: 48px;
      object-fit: cover;
      border-radius: 3px;
      display: block;
      margin: auto;
    }}
    .hidden {{ display: none; }}
    #count {{ color: #555; font-size: 12px; margin-bottom: 8px; }}
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
  <div class="wrap">
    <table id="catalogue">
      <thead>
        <tr>
          <th class="col-thumb"></th>
          <th class="col-platform">Platform</th>
          <th class="col-title">Title</th>
          <th class="col-uploader">Uploader</th>
        </tr>
      </thead>
      <tbody>
    {rows_html}
      </tbody>
    </table>
  </div>

  <script>
    function filterTable() {{
      const q = document.getElementById('search').value.toLowerCase();
      const rows = document.querySelectorAll('#catalogue tbody tr');
      let visible = 0;
      rows.forEach(row => {{
        const match = row.textContent.toLowerCase().includes(q);
        row.classList.toggle('hidden', !match);
        if (match) visible++;
      }});
      const total = rows.length;
      document.getElementById('count').textContent =
        q ? visible + ' of ' + total + ' matching' : '';
    }}
  </script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Done. {row_count} records written to {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
