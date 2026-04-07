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


def run(cmd, capture=False, check=True, **kwargs):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=capture,
        **kwargs,
    )
    if check and result.returncode != 0:
        if capture and result.stderr:
            print(result.stderr.strip())
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result


def tracked_changes_excluding(paths_to_ignore=None):
    paths_to_ignore = set(paths_to_ignore or [])
    result = run(["git", "status", "--porcelain", "--untracked-files=no"], capture=True, check=False)
    bad = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if path in paths_to_ignore:
            continue
        bad.append(line)
    return bad


def has_changes(paths=None):
    cmd = ["git", "status", "--porcelain"]
    if paths:
        cmd.extend(paths)
    result = run(cmd, capture=True, check=False)
    return bool(result.stdout.strip())


def commit_if_needed(message, paths):
    if has_changes(paths):
        run(["git", "add", *paths])
        run(["git", "commit", "-m", message])
        return True
    print("  No changes to commit.")
    return False


def download_link(url):
    is_facebook = "facebook.com" in url or "fb.watch" in url

    base_cmd = [
        sys.executable, "-m", "yt_dlp",
        "-o", "raw/%(id)s.%(ext)s",
        "--write-info-json",
        "--write-thumbnail",
        "--convert-thumbnails", "jpg",
        "--skip-download",
        "--no-playlist",
    ]

    if is_facebook:
        print("  [Facebook] Using Safari cookies...")
        cmd = base_cmd + ["--cookies-from-browser", "safari", url]
    else:
        cmd = base_cmd + [url]

    result = run(cmd, check=False)
    ok = result.returncode == 0

    if not ok and not is_facebook:
        print("  Retrying with Safari cookies...")
        result = run(base_cmd + ["--cookies-from-browser", "safari", url], check=False)
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

    # Allow new_links.txt to be the only tracked change before we start.
    dirty = tracked_changes_excluding({str(NEW_LINKS_FILE)})
    if dirty:
        print("Your git working tree has tracked changes besides new_links.txt. Commit or stash them first, then rerun.")
        for line in dirty:
            print(line)
        sys.exit(1)

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

    NEW_LINKS_FILE.write_text("")

    if failed:
        print(f"\n  {len(failed)} link(s) could not be downloaded (skipped):")
        for u in failed:
            print(f"    {u}")

    print("\nStep 2: Building records from downloaded files...")
    run(["python3", "build_records.py"])

    print("\nStep 3: Generating HTML catalogue...")
    run(["python3", "csv_to_html.py"])

    print("\nStep 4: Saving data to current branch...")
    changed_current = commit_if_needed(
        "Add new videos to catalogue",
        ["new_links.txt", "raw/", "records.json", "records_summary.csv", "records_summary.html"],
    )
    if changed_current:
        run(["git", "push", "-u", "origin", current_branch])

    print("\nStep 5: Pushing deployable files to Netlify branch...")
    run(["git", "fetch", "origin", DEPLOY_BRANCH])

    check = run(["git", "show-ref", "--verify", f"refs/heads/{DEPLOY_BRANCH}"], capture=True, check=False)
    if check.returncode != 0:
        run(["git", "checkout", "-b", DEPLOY_BRANCH, f"origin/{DEPLOY_BRANCH}"])
    else:
        run(["git", "checkout", DEPLOY_BRANCH])
        run(["git", "reset", "--hard", f"origin/{DEPLOY_BRANCH}"])

    run([
        "git", "checkout", current_branch, "--",
        "records.json", "records_summary.csv", "records_summary.html"
    ])

    changed_deploy = commit_if_needed(
        "Deploy updated catalogue",
        ["records.json", "records_summary.csv", "records_summary.html"],
    )
    if changed_deploy:
        run(["git", "push", "-u", "origin", DEPLOY_BRANCH])

    run(["git", "checkout", current_branch])

    print("\nAll done. Your catalogue should update shortly.")
    print("Open: https://video-links-project.netlify.app/records_summary.html")


if __name__ == "__main__":
    main()
