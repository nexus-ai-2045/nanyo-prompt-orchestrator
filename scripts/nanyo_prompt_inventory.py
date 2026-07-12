#!/usr/bin/env python3
"""Build a compact inventory from Nanyo City's public prompt list."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import sys
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_URL = "http://www.city.nanyo.yamagata.jp/dxchosei/5793"


class ArticleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []
        self.href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a":
            self.href = attrs_dict.get("href")
        elif tag == "h2":
            self.out.append("\n## ")
        elif tag == "h3":
            self.out.append("\n### ")
        elif tag == "br":
            self.out.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self.href = None
        elif tag in {"h2", "h3"}:
            self.out.append("\n")

    def handle_data(self, data: str) -> None:
        text = html.unescape(data)
        if self.href:
            self.out.append(f"[{text}]({self.href})")
        else:
            self.out.append(text)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode("utf-8", "replace")


def extract_article(html_text: str) -> str:
    match = re.search(r"<article>(.*?)</article>", html_text, re.S | re.I)
    return match.group(1) if match else html_text


def parse_rows(html_text: str, source_url: str, retrieved_at: str) -> list[dict[str, str]]:
    parser = ArticleTextParser()
    parser.feed(extract_article(html_text))
    rows: list[dict[str, str]] = []
    category = "未分類"
    for raw_line in "".join(parser.out).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading = re.match(r"###\s*(.+?)[:：]?$", line)
        if heading:
            category = heading.group(1).strip("：: ")
            continue
        row = re.match(r"-\s*(\d+)\s*\[(.+?)\]\((.+?)\)", line)
        if not row:
            continue
        prompt_id, title, url = row.groups()
        rows.append(
            {
                "source_url": source_url,
                "retrieved_at": retrieved_at,
                "source_category": category,
                "prompt_id": str(int(prompt_id)),
                "title": title.strip(),
                "prompt_url": url.strip(),
            }
        )
    counts = Counter(row["prompt_id"] for row in rows)
    for row in rows:
        row["duplicate_in_source"] = "yes" if counts[row["prompt_id"]] > 1 else "no"
        row["source_highlight"] = "yes" if row["source_category"] == "未分類" else "no"
    return rows


def unique_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        current = by_id.get(row["prompt_id"])
        if current is None:
            by_id[row["prompt_id"]] = dict(row)
            continue
        if current["source_category"] == "未分類" and row["source_category"] != "未分類":
            merged = dict(row)
            merged["also_highlighted"] = "yes"
            by_id[row["prompt_id"]] = merged
        else:
            current["also_highlighted"] = "yes"
    for row in by_id.values():
        row.setdefault("also_highlighted", "yes" if row["source_highlight"] == "yes" else "no")
    return sorted(by_id.values(), key=lambda row: int(row["prompt_id"]))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("no rows to write")
    fieldnames = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(path: Path, rows: list[dict[str, str]], unique: list[dict[str, str]]) -> None:
    summary = {
        "source_url": rows[0]["source_url"] if rows else None,
        "retrieved_at": rows[0]["retrieved_at"] if rows else None,
        "source_rows": len(rows),
        "unique_prompt_ids": len(unique),
        "duplicate_prompt_ids": sorted(
            prompt_id for prompt_id, count in Counter(row["prompt_id"] for row in rows).items() if count > 1
        ),
        "category_counts": dict(Counter(row["source_category"] for row in rows)),
        "note": "Run nanyo_prompt_mirror.py to mirror individual prompt bodies locally.",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_inventory(url: str, out_dir: Path) -> dict[str, int]:
    retrieved_at = dt.datetime.now(dt.timezone.utc).isoformat()
    html_text = fetch(url)
    rows = parse_rows(html_text, url, retrieved_at)
    unique = unique_rows(rows)
    write_csv(out_dir / "inventory-all.csv", rows)
    write_csv(out_dir / "inventory-unique.csv", unique)
    write_summary(out_dir / "inventory-summary.json", rows, unique)
    return {"source_rows": len(rows), "unique_prompt_ids": len(unique)}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--out-dir", default="data")
    args = parser.parse_args(argv)

    result = build_inventory(args.url, Path(args.out_dir))
    result["out_dir"] = args.out_dir
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
