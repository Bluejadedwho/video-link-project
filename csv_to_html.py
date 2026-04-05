import csv
import html
import os
<<<<<<< HEAD
=======
from datetime import datetime, timezone
from urllib.parse import quote
>>>>>>> 3a964e468a8fea1404d190451cc56cfaa0e7fdf8

INPUT_CSV = "records_summary.csv"
OUTPUT_HTML = "records_summary.html"

<<<<<<< HEAD

def is_url(text):
    if not text:
        return False
    text = str(text).strip().lower()
    return text.startswith("http://") or text.startswith("https://")


def shorten(text, limit=120):
    text = "" if text is None else str(text)
    return text if len(text) <= limit else text[:limit] + "..."


def format_cell(value, column_name=""):
    text = "" if value is None else str(value).strip()
    safe_full = html.escape(text)
    safe_short = html.escape(shorten(text, 120))

    col = column_name.lower()

    # Make URLs clickable
    if is_url(text):
        return f'<a href="{safe_full}" target="_blank">{safe_short}</a>'

    # Show image URLs as images if the column suggests an image
    if "thumbnail" in col or "image" in col:
        if is_url(text):
            return f'<a href="{safe_full}" target="_blank"><img src="{safe_full}" alt="thumbnail"></a>'

    return safe_full.replace("\n", "<br>")
=======
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
>>>>>>> 3a964e468a8fea1404d190451cc56cfaa0e7fdf8


def main():
    if not os.path.exists(INPUT_CSV):
<<<<<<< HEAD
        print(f"Missing file: {INPUT_CSV}")
        return

    with open(INPUT_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []

    html_parts = []

    html_parts.append("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Records Summary</title>
<style>
body {
    font-family: Arial, sans-serif;
    margin: 20px;
    background: #111;
    color: #eee;
}

h1 {
    margin-bottom: 20px;
}

.table-wrap {
    overflow-x: auto;
    border: 1px solid #333;
}

table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    min-width: 1400px;
}

th, td {
    border: 1px solid #444;
    padding: 8px;
    vertical-align: top;
    text-align: left;
    word-break: break-word;
    overflow-wrap: break-word;
    white-space: normal;
    font-size: 13px;
    line-height: 1.35;
}

th {
    background: #222;
    position: sticky;
    top: 0;
    z-index: 2;
}

tr:nth-child(even) {
    background: #1a1a1a;
}

tr:nth-child(odd) {
    background: #151515;
}

a {
    color: #66b3ff;
}

img {
    max-width: 140px;
    height: auto;
    display: block;
    border-radius: 4px;
}

.col-platform { width: 90px; }
.col-title { width: 300px; }
.col-url { width: 240px; }
.col-thumbnail_alt { width: 260px; }
.col-uploader { width: 150px; }
.col-timestamp { width: 120px; }
.col-transcript_source { width: 140px; }
.col-description { width: 260px; }

.small-note {
    color: #bbb;
    margin-bottom: 14px;
    font-size: 13px;
}
</style>
</head>
<body>
""")

    html_parts.append(f"<h1>Records Summary</h1>")
    html_parts.append(f'<div class="small-note">Rows: {len(rows)}</div>')
    html_parts.append('<div class="table-wrap">')
    html_parts.append("<table>")
    html_parts.append("<thead><tr>")

    for header in headers:
        css_class = f'col-{html.escape(header)}'
        html_parts.append(f'<th class="{css_class}">{html.escape(header)}</th>')

    html_parts.append("</tr></thead>")
    html_parts.append("<tbody>")

    for row in rows:
        html_parts.append("<tr>")
        for header in headers:
            css_class = f'col-{html.escape(header)}'
            cell_html = format_cell(row.get(header, ""), header)
            html_parts.append(f'<td class="{css_class}">{cell_html}</td>')
        html_parts.append("</tr>")

    html_parts.append("</tbody></table></div></body></html>")

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write("".join(html_parts))

    print(f"Created {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
=======
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
>>>>>>> 3a964e468a8fea1404d190451cc56cfaa0e7fdf8
