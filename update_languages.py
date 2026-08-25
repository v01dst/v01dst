#!/usr/bin/env python3
import json
import os
import urllib.request
from pathlib import Path

USER = "v01dst"
README = Path("README.md")
API = f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=updated"

def get_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "v01dst-profile-updater",
        },
    )
    token = os.getenv("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as response:
        return json.load(response)

def pct_bar(value, width=22):
    filled = round(value / 100 * width)
    return "█" * filled + "░" * (width - filled)

def main():
    repos = get_json(API)
    blocks = []

    for repo in repos:
        if repo.get("fork") or repo.get("archived"):
            continue

        languages = get_json(repo["languages_url"])
        total = sum(languages.values())

        if not total:
            continue

        ranked = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        rows = []
        for name, amount in ranked[:5]:
            percentage = amount / total * 100
            rows.append(f"**{name}**  {pct_bar(percentage)} `{percentage:.1f}%`")

        blocks.append(
            f"### [{repo['name']}]({repo['html_url']})\n"
            f"{repo.get('description') or 'No description'}\n\n"
            + "\n".join(rows)
        )

    content = "\n\n---\n\n".join(blocks) if blocks else "_No language data available yet._"
    replacement = f"<!-- LANGUAGES:START -->\n\n{content}\n\n<!-- LANGUAGES:END -->"

    text = README.read_text(encoding="utf-8")
    start = "<!-- LANGUAGES:START -->"
    end = "<!-- LANGUAGES:END -->"
    a = text.index(start)
    b = text.index(end) + len(end)
    text = text[:a] + replacement + text[b:]
    README.write_text(text, encoding="utf-8")

if __name__ == "__main__":
    main()
