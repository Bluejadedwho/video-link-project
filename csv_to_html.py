import csv
import html
import os

INPUT_CSV = "records_summary.csv"
OUTPUT_HTML = "records_summary.html"


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


def main():
    if not os.path.exists(INPUT_CSV):
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