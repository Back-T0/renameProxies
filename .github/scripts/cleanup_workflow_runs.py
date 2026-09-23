#!/usr/bin/env python3
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


def parse_span(span: str) -> dt.timedelta:
    m = re.fullmatch(r"\s*(\d+)\s*([hdwmy])\s*", span or "")
    if not m:
        raise ValueError(
            "Invalid maintain-span format. Use like: 12h, 3d, 2w, 1m, 1y."
        )
    value = int(m.group(1))
    unit = m.group(2).lower()
    if unit == "h":
        return dt.timedelta(hours=value)
    if unit == "d":
        return dt.timedelta(days=value)
    if unit == "w":
        return dt.timedelta(weeks=value)
    if unit == "m":
        return dt.timedelta(days=value * 30)
    return dt.timedelta(days=value * 365)


def request_json(url: str, token: str):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "cleanup-workflow-runs-script",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def delete_run(owner: str, repo: str, run_id: int, token: str) -> bool:
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}"
    req = urllib.request.Request(
        url,
        method="DELETE",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "cleanup-workflow-runs-script",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 204
    except urllib.error.HTTPError as e:
        print(f"[WARN] delete run {run_id} failed: HTTP {e.code}")
        return False


def parse_iso8601(s: str) -> dt.datetime:
    # GitHub format: 2026-04-14T12:34:56Z
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def main() -> int:
    repo_full = os.getenv("GITHUB_REPOSITORY", "").strip()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    maintain_span = os.getenv("MAINTAIN_SPAN", "3d").strip()

    if not repo_full or "/" not in repo_full:
        print("GITHUB_REPOSITORY is missing or invalid.")
        return 2
    if not token:
        print("GITHUB_TOKEN is missing.")
        return 2

    owner, repo = repo_full.split("/", 1)
    cutoff = dt.datetime.now(dt.timezone.utc) - parse_span(maintain_span)

    print(f"Repository: {repo_full}")
    print(f"Maintain span: {maintain_span}")
    print(f"Delete runs older than: {cutoff.isoformat()}")

    deleted = 0
    scanned = 0
    page = 1
    per_page = 100

    while True:
        query = urllib.parse.urlencode({"per_page": per_page, "page": page})
        list_url = (
            f"https://api.github.com/repos/{owner}/{repo}/actions/runs?{query}"
        )
        data = request_json(list_url, token)
        runs = data.get("workflow_runs", [])
        if not runs:
            break

        for run in runs:
            scanned += 1
            run_id = run.get("id")
            created_at = run.get("created_at")
            if not run_id or not created_at:
                continue
            run_time = parse_iso8601(created_at)
            if run_time >= cutoff:
                continue
            if delete_run(owner, repo, int(run_id), token):
                deleted += 1
                print(f"Deleted run: {run_id} ({created_at})")

        page += 1

    print(f"Scanned: {scanned}, Deleted: {deleted}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"[ERROR] {e}")
        raise
