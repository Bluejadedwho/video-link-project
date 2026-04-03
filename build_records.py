import csv
import json
import re
from pathlib import Path

raw_dir = Path("raw")
json_out = Path("records.json")
csv_out = Path("records_summary.csv")

def clean_caption_text(text):
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s == "WEBVTT":
            continue
        if "-->" in s:
            continue
        if s.isdigit():
            continue
        if s.startswith("Kind:") or s.startswith("Language:") or s.startswith("NOTE"):
            continue
        lines.append(s)
    joined = " ".join(lines)
    joined = re.sub(r"\s+", " ", joined).strip()
    return joined

def find_caption(base_name):
    candidates = []
    for p in raw_dir.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() not in (".vtt", ".srt"):
            continue
        if p.name.startswith(base_name):
            candidates.append(p)

    for p in sorted(candidates):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
            cleaned = clean_caption_text(text)
            if cleaned:
                return cleaned, p.name
        except Exception:
            pass

    return "", ""

records = []

for info_file in sorted(raw_dir.iterdir()):
    if not info_file.is_file():
        continue
    if not info_file.name.endswith(".info.json"):
        continue

    base_path = info_file.with_suffix("")
    if base_path.suffix == ".info":
        base_path = base_path.with_suffix("")
    base_name = base_path.name

    try:
        info = json.loads(info_file.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        continue

    description = ""
    description_file = raw_dir / f"{base_name}.description"
    if description_file.exists():
        description = description_file.read_text(encoding="utf-8", errors="ignore").strip()
    else:
        description = (info.get("description") or "").strip()

    thumbnail_file = ""
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = raw_dir / f"{base_name}{ext}"
        if p.exists():
            thumbnail_file = f"raw/{p.name}"
            break

    transcript, transcript_file = find_caption(base_name)
    transcript_source = "captions" if transcript else "none"

    url = (
        info.get("webpage_url")
        or info.get("original_url")
        or info.get("url")
        or ""
    )

    low = url.lower()
    if "instagram.com" in low:
        platform = "instagram"
    elif "facebook.com" in low or "fb.watch" in low:
        platform = "facebook"
    else:
        platform = "unknown"

    title = (info.get("title") or "").strip()
    uploader = (info.get("uploader") or info.get("channel") or "").strip()
    timestamp = info.get("timestamp") or ""

    record = {
        "url": url,
        "platform": platform,
        "title": title,
        "description": description,
        "thumbnail_file": thumbnail_file,
        "transcript": transcript,
        "transcript_source": transcript_source,
        "transcript_file": transcript_file,
        "uploader": uploader,
        "timestamp": timestamp
    }

    records.append(record)

json_out.write_text(
    json.dumps(records, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

with csv_out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "platform",
        "title",
        "url",
        "thumbnail_file",
        "uploader",
        "timestamp",
        "transcript_source",
        "description_preview",
        "transcript_preview"
    ])

    for r in records:
        writer.writerow([
            r["platform"],
            r["title"],
            r["url"],
            r["thumbnail_file"],
            r["uploader"],
            r["timestamp"],
            r["transcript_source"],
            r["description"][:200],
            r["transcript"][:200]
        ])

with_transcripts = sum(1 for r in records if r["transcript"])

print("Done.")
print("Created:", json_out)
print("Created:", csv_out)
print("Total records:", len(records))
print("Records with transcripts:", with_transcripts)
