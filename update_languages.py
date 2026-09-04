#!/usr/bin/env python3
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER = "v01dst"
README = Path("README.md")
REPOS_API = f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed"
PROFILE_API = f"https://api.github.com/users/{USER}"
TOP = 6
BAR_WIDTH = 22


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USER}-profile-updater",
        },
    )
    token = os.getenv("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as response:
        return json.load(response)


def pct_bar(value, width=BAR_WIDTH):
    filled = round(value / 100 * width)
    return "█" * filled + "░" * (width - filled)


def replace_block(text, tag, content):
    start = f"<!-- {tag}:START -->"
    end = f"<!-- {tag}:END -->"
    a = text.index(start)
    b = text.index(end) + len(end)
    return text[:a] + f"{start}\n\n{content}\n\n{end}" + text[b:]


def language_block(repos):
    blocks = []
    for repo in repos:
        languages = get_json(repo["languages_url"])
        total = sum(languages.values())
        if not total:
            continue
        ranked = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        rows = [
            f"**{name}**  {pct_bar(amount / total * 100)} `{amount / total * 100:.1f}%`"
            for name, amount in ranked[:5]
        ]
        description = (repo.get("description") or "No description").replace("|", "/")
        blocks.append(
            f"### [{repo['name']}]({repo['html_url']})\n"
            f"{description}\n\n" + "\n".join(rows)
        )
        if len(blocks) >= TOP:
            break
    return "\n\n---\n\n".join(blocks) if blocks else "_No language data available yet._"


def status_block(repos, profile):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stars = sum(r["stargazers_count"] for r in repos)
    latest_push = repos[0]["pushed_at"][:10] if repos else "—"
    lines = [
        f"**⚡ {len(repos)} public repos · ⭐ {stars} total stars · 👥 {profile['followers']} followers · 🚀 latest push `{latest_push}`**",
        "",
        "| Repo | What it is | Lang | ★ | Last push |",
        "| --- | :--- | :--- | :---: | :---: |",
    ]
    for repo in repos[:TOP]:
        description = (repo.get("description") or "No description").replace("|", "/")
        language = repo.get("language") or "—"
        lines.append(
            f"| [{repo['name']}]({repo['html_url']}) | {description} | {language} "
            f"| {repo['stargazers_count']} | {repo['pushed_at'][:10]} |"
        )
    return "\n".join(lines)


def main():
    repos = get_json(REPOS_API)
    repos = [r for r in repos if not r.get("fork") and not r.get("archived")]
    repos.sort(key=lambda r: r["pushed_at"], reverse=True)
    profile = get_json(PROFILE_API)
    text = README.read_text(encoding="utf-8")
    text = replace_block(text, "STATUS", status_block(repos, profile))
    text = replace_block(text, "LANGUAGES", language_block(repos[:TOP]))
    README.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
