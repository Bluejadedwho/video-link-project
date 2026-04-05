"""
Run this on your Mac to add new videos and update the catalogue.
Usage: python3 update_catalogue.py
"""
import subprocess
import sys
from pathlib import Path

NEW_LINKS_FILE = Path("new_links.txt")
RAW_DIR = Path("raw")
DEPLOY_BRANCH = "claude/video-catalogue-v1-ZJvHx"

def run(cmd, capture=False, **kwargs):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    return subprocess.run(cmd, **kwargs)

def download_link(url):
    is_facebook = "facebook.com" in url or "fb.watch" in url

    base_cmd = [
        "yt-dlp",
        "-o", "raw/%(id)s.%(ext)s",
        "--write-info-json",
        "--write-thumbnail",
        "--convert-thumbnails", "jpg",
        "--skip-download",
        "--no-playlist",
    ]

    if is_facebook:
        print(f"  [Facebook] Using Safari cookies...")
        cmd = base_cmd + ["--cookies-from-browser", "safari", url]
    else:
        cmd = base_cmd + [url]

    result = run(cmd)
    ok = result.returncode == 0

    if not ok and not is_facebook:
        print(f"  Retrying with Safari cookies...")
        result = run(base_cmd + ["--cookies-from-browser", "safari", url])
        ok = result.returncode == 0

    return ok

def main():
    if not NEW_LINKS_FILE.exists():
        print("No new_links.txt found. Run check_new_links.py first.")
        sys.exit(1)

    links = [l.strip() for l in NEW_LINKS_FILE.read_text().splitlines() if l.strip()]
    if not links:
        print("new_links.txt is empty. Nothing to do.")
        sys.exit(0)

    # Check we're on master
    result = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture=True)
    current_branch = result.stdout.strip()

    print(f"\nStep 1: Downloading metadata for {len(links)} new link(s)...")
    RAW_DIR.mkdir(exist_ok=True)
    failed = []
    for url in links:
        print(f"\n  {url}")
        if not download_link(url):
            failed.append(url)
            print(f"  FAILED: {url}")

    if failed:
        print(f"\n  {len(failed)} link(s) could not be downloaded:")
        for u in failed:
            print(f"    {u}")
        print("  (Facebook share links need you logged into Facebook in Safari first)")

    print("\nStep 2: Building records from downloaded files...")
    run(["python3", "build_records.py"])

    print("\nStep 3: Generating HTML catalogue...")
    run(["python3", "csv_to_html.py"])

    # Save updated files to master first
    print(f"\nStep 4: Saving data to master branch...")
    run(["git", "add", "raw/", "records.json", "records_summary.csv", "records_summary.html"])
    run(["git", "commit", "-m", "Add new videos to catalogue"])
    run(["git", "push", "-u", "origin", current_branch])

    # Now push the deployable files to the claude branch (no raw/ folder)
    print(f"\nStep 5: Pushing to deploy branch for Netlify...")
    run(["git", "fetch", "origin", DEPLOY_BRANCH])
    run(["git", "checkout", DEPLOY_BRANCH])
    run(["git", "checkout", current_branch, "--",
         "records.json", "records_summary.csv", "records_summary.html"])
    run(["git", "add", "records.json", "records_summary.csv", "records_summary.html"])
    run(["git", "commit", "-m", "Deploy updated catalogue"])
    run(["git", "push", "-u", "origin", DEPLOY_BRANCH])
    run(["git", "checkout", current_branch])

    print("\nAll done! Your catalogue will update on your phone in ~30 seconds.")
    print("Open: https://video-links-project.netlify.app/records_summary.html")

if __name__ == "__main__":
    main()
