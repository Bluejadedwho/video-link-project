import csv
from datetime import datetime

INPUT_FILE = "records_summary.csv"
OUTPUT_FILE = "records_summary.html"

# Only these columns will appear in the HTML table, in this order
VISIBLE_COLUMNS = ["platform", "title", "url", "uploader", "timestamp", "transcript_source"]

def format_timestamp(raw):
    """Convert ISO timestamp like 2024-03-15T10:30:00 to Mar 15 2024."""
    if not raw:
        return ""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%b %d %Y")
        except ValueError:
            continue
    return raw  # return as-is if parsing fails

def make_link(url):
    if url and url.startswith("http"):
        # Shorten display text to just the domain + path start
        display = url.replace("https://", "").replace("http://", "")
        if len(display) > 40:
            display = display[:37] + "..."
        return f'<a href="{url}" target="_blank">{display}</a>'
    return url or ""

def load_rows(filepath):
    rows = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def build_html(rows):
    row_count = len(rows)

    # Build table rows
    table_rows = []
    for row in rows:
        cells = []
        for col in VISIBLE_COLUMNS:
            value = row.get(col, "")
            if col == "timestamp":
                value = format_timestamp(value)
            elif col == "url":
                value = make_link(value)
            else:
                value = value.strip() if value else ""
            cells.append(f"<td>{value}</td>")
        table_rows.append("<tr>" + "".join(cells) + "</tr>")

    headers = "".join(f"<th>{col}</th>" for col in VISIBLE_COLUMNS)
    rows_html = "\n        ".join(table_rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Video Catalogue</title>
  <style>
    body {{
      background: #1a1a1a;
      color: #e0e0e0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
      padding: 20px;
    }}
    h1 {{
      color: #ffffff;
      font-size: 20px;
      margin-bottom: 4px;
    }}
    .meta {{
      color: #888;
      font-size: 13px;
      margin-bottom: 16px;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      table-layout: fixed;
    }}
    th {{
      background: #2c2c2c;
      color: #aaaaaa;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.05em;
      padding: 8px 10px;
      text-align: left;
      border-bottom: 2px solid #444;
    }}
    td {{
      padding: 8px 10px;
      border-bottom: 1px solid #2e2e2e;
      vertical-align: top;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    tr:hover td {{
      background: #242424;
    }}
    a {{
      color: #6ab0f5;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
    /* Column widths */
    th:nth-child(1), td:nth-child(1) {{ width: 80px;  }}  /* platform */
    th:nth-child(2), td:nth-child(2) {{ width: 28%;   }}  /* title */
    th:nth-child(3), td:nth-child(3) {{ width: 22%;   }}  /* url */
    th:nth-child(4), td:nth-child(4) {{ width: 14%;   }}  /* uploader */
    th:nth-child(5), td:nth-child(5) {{ width: 100px; }}  /* timestamp */
    th:nth-child(6), td:nth-child(6) {{ width: 120px; }}  /* transcript_source */
  </style>
</head>
<body>
  <h1>Video Catalogue</h1>
  <p class="meta">{row_count} records &mdash; generated {datetime.now().strftime("%b %d %Y")}</p>
  <table>
    <thead>
      <tr>{headers}</tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
  </table>
</body>
</html>"""
    return html

def main():
    rows = load_rows(INPUT_FILE)
    html = build_html(rows)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Done. {len(rows)} records written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
