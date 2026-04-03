#!/usr/bin/env python3
import csv
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

def apple_time_to_iso(value):
    if value is None:
        return ""
    try:
        v = int(value)
    except Exception:
        return ""

    av = abs(v)

    # Apple Messages dates may appear as seconds, microseconds, or nanoseconds since 2001-01-01
    if av > 10**16:
        seconds = v / 1_000_000_000
    elif av > 10**13:
        seconds = v / 1_000_000
    else:
        seconds = v

    try:
        dt = APPLE_EPOCH + timedelta(seconds=seconds)
        return dt.isoformat()
    except Exception:
        return ""

def export_messages(db_path: Path, out_csv: Path):
    query = """
    SELECT
        m.ROWID AS message_id,
        m.guid AS guid,
        m.service AS service,
        m.is_from_me AS is_from_me,
        m.date AS raw_date,
        CASE
            WHEN m.is_from_me = 1 THEN 'me'
            ELSE COALESCE(h.id, '')
        END AS sender,
        COALESCE(c.chat_identifier, '') AS chat_identifier,
        COALESCE(c.display_name, '') AS chat_name,
        COALESCE(
            (
                SELECT GROUP_CONCAT(h2.id, ' | ')
                FROM chat_handle_join chj
                JOIN handle h2 ON h2.ROWID = chj.handle_id
                WHERE chj.chat_id = c.ROWID
            ),
            ''
        ) AS participants,
        COALESCE(m.text, '') AS text,
        COALESCE(
            (
                SELECT GROUP_CONCAT(a.filename, ' | ')
                FROM message_attachment_join maj
                JOIN attachment a ON a.ROWID = maj.attachment_id
                WHERE maj.message_id = m.ROWID
            ),
            ''
        ) AS attachments
    FROM message m
    LEFT JOIN handle h
        ON h.ROWID = m.handle_id
    LEFT JOIN chat_message_join cmj
        ON cmj.message_id = m.ROWID
    LEFT JOIN chat c
        ON c.ROWID = cmj.chat_id
    ORDER BY m.date;
    """

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    rows_written = 0
    with conn, open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "message_id",
                "guid",
                "service",
                "timestamp",
                "is_from_me",
                "sender",
                "chat_identifier",
                "chat_name",
                "participants",
                "text",
                "attachments",
            ],
        )
        writer.writeheader()

        for row in conn.execute(query):
            writer.writerow(
                {
                    "message_id": row["message_id"],
                    "guid": row["guid"],
                    "service": row["service"],
                    "timestamp": apple_time_to_iso(row["raw_date"]),
                    "is_from_me": row["is_from_me"],
                    "sender": row["sender"],
                    "chat_identifier": row["chat_identifier"],
                    "chat_name": row["chat_name"],
                    "participants": row["participants"],
                    "text": row["text"],
                    "attachments": row["attachments"],
                }
            )
            rows_written += 1

    conn.close()
    return rows_written

def main():
    default_db = Path.home() / "Library" / "Messages" / "chat.db"
    default_out = Path.home() / "Desktop" / "apple_messages.csv"

    db_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else default_db
    out_csv = Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else default_out

    if not db_path.exists():
        print(f"Messages database not found: {db_path}")
        sys.exit(1)

    try:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        count = export_messages(db_path, out_csv)
        print(f"Exported {count} rows to {out_csv}")
    except sqlite3.OperationalError as e:
        print("Could not read the Messages database.")
        print("Try these:")
        print("1. Quit the Messages app")
        print("2. Give Terminal Full Disk Access")
        print(f"3. Run again")
        print("")
        print(f"SQLite error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()

