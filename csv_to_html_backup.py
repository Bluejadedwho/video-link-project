import csv
import html
from pathlib import Path

src = Path("records_summary.csv")
dst = Path("records_summary.html")

with src.open("r", encoding="utf-8", errors="ignore", newline="") as f:
    rows = list(csv.reader(f))

parts = []
parts.append("<html><head><meta charset='utf-8'>")
parts.append("<title>Records Summary</title>")
parts.append("<style>")
parts.append("body{font-family:Arial,Helvetica,sans-serif;margin:20px;background:#111;color:#eee;}")
parts.append("table{border-collapse:collapse;width:100%;font-size:14px;}")
parts.append("th,td{border:1px solid #444;padding:8px;vertical-align:top;text-align:left;}")
parts.append("th{position:sticky;top:0;background:#222;}")
parts.append("tr:nth-child(even){background:#1a1a1a;}")
parts.append("a{color:#7db7ff;}")
parts.append("</style></head><body>")
parts.append("<h1>Records Summary</h1>")
parts.append("<table>")

if rows:
    header = rows[0]
    parts.append("<tr>" + "".join(f"<th>{html.escape(cell)}</th>" for cell in header) + "</tr>")
    for row in rows[1:]:
        cells = []
        for cell in row:
            cell = cell or ""
            if cell.startswith("http://") or cell.startswith("https://"):
                cells.append(f"<td><a href='{html.escape(cell)}' target='_blank'>{html.escape(cell)}</a></td>")
            else:
                cells.append(f"<td>{html.escape(cell)}</td>")
        parts.append("<tr>" + "".join(cells) + "</tr>")

parts.append("</table></body></html>")

dst.write_text("\n".join(parts), encoding="utf-8")

print("Created records_summary.html")
