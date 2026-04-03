import csv
import html
import os
from datetime import datetime, timezone

INPUT_CSV = "records_summary.csv"
OUTPUT_HTML = "records_summary.html"

# Only these columns will be shown, in this order
VISIBLE_COLUMNS = ["platform", "title", "url", "uploader", "timestamp", "transcript_source"]


def format_timestamp(raw):
    """Convert Unix timestamp (seconds) to readable date like Apr 03 2026."""
    if not raw:
        return ""
    try:
        ts = int(float(raw.strip()))
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%b %d %Y")
    except (ValueError, OSError):
        return raw


def make_link(url):
    """Turn a URL into a clickable link with shortened display text."""
    url = url.strip() if url else ""
    if not url.startswith("http"):
        return html.escape(url)
    display = url.replace("https://", "").replace("http://", "")
    if len(display) > 45:
        display = display[:42] + "..."
    return f'<a href="{html.escape(url)}" target="_blank">{html.escape(display)}</a>'


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
        cells = []
        for col in VISIBLE_COLUMNS:
            value = row.get(col, "") or ""
            if col == "timestamp":
                cell = html.escape(format_timestamp(value))
            elif col == "url":
                cell = make_link(value)
            else:
                cell = html.escape(value.strip())
            cells.append(f'<td class="col-{col}">{cell}</td>')
        table_rows.append("<tr>" + "".join(cells) + "</tr>")

    headers_html = "".join(
        f'<th class="col-{col}">{col}</th>' for col in VISIBLE_COLUMNS
    )
    rows_html = "\n    ".join(table_rows)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Video Catalogue</title>
  <style>
    body {{
      background: #111;
      color: #e0e0e0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 13px;
      padding: 20px;
    }}
    h1 {{
      color: #fff;
      font-size: 20px;
      margin-bottom: 4px;
    }}
    .meta {{
      color: #777;
      font-size: 12px;
      margin-bottom: 16px;
    }}
    .wrap {{
      overflow-x: auto;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      table-layout: fixed;
      min-width: 900px;
    }}
    th {{
      background: #1e1e1e;
      color: #aaa;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.05em;
      padding: 8px 10px;
      text-align: left;
      border-bottom: 2px solid #333;
      position: sticky;
      top: 0;
    }}
    td {{
      padding: 7px 10px;
      border-bottom: 1px solid #222;
      vertical-align: top;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    tr:hover td {{
      background: #1a1a1a;
    }}
    a {{
      color: #5aadff;
      text-decoration: none;
    }}
    a:hover {{ text-decoration: underline; }}

    /* Column widths */
    .col-platform         {{ width: 80px; }}
    .col-title            {{ width: 30%; }}
    .col-url              {{ width: 22%; }}
    .col-uploader         {{ width: 15%; }}
    .col-timestamp        {{ width: 90px; }}
    .col-transcript_source{{ width: 110px; }}
  </style>
</head>
<body>
  <h1>Video Catalogue</h1>
  <p class="meta">{row_count} records &mdash; generated {generated}</p>
  <div class="wrap">
    <table>
      <thead><tr>{headers_html}</tr></thead>
      <tbody>
    {rows_html}
      </tbody>
    </table>
  </div>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Done. {row_count} records written to {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
