#!/usr/bin/env python3
"""Mirror Nanyo City prompt pages into local structured JSON files."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path


DEFAULT_BASE = Path("data")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def fetch(url: str, timeout: int = 30) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.geturl(), res.read().decode("utf-8", "replace")


def normalize_text(text: str) -> str:
    text = html.unescape(text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


@dataclass
class Field:
    tag: str
    name: str = ""
    field_id: str = ""
    type: str = ""
    label_hint: str = ""
    placeholder: str = ""
    value: str = ""


class PromptPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.page_title = ""
        self.headings: list[str] = []
        self.fields: list[Field] = []
        self._capture_title = False
        self._capture_heading: str | None = None
        self._heading_parts: list[str] = []
        self._capture_textarea: Field | None = None
        self._textarea_parts: list[str] = []
        self._select: Field | None = None
        self._current_option_value = ""
        self._capture_option = False
        self._option_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag == "title":
            self._capture_title = True
        elif tag in {"h1", "h2", "h3"}:
            self._capture_heading = tag
            self._heading_parts = []
        elif tag == "textarea":
            self._capture_textarea = Field(
                tag="textarea",
                name=attrs_dict.get("name", ""),
                field_id=attrs_dict.get("id", ""),
                label_hint=self.headings[-1] if self.headings else "",
                placeholder=attrs_dict.get("placeholder", ""),
            )
            self._textarea_parts = []
        elif tag == "input":
            value = attrs_dict.get("value", "")
            input_type = attrs_dict.get("type", "")
            if value or input_type == "hidden":
                self.fields.append(
                    Field(
                        tag="input",
                        name=attrs_dict.get("name", ""),
                        field_id=attrs_dict.get("id", ""),
                        type=input_type,
                        label_hint=self.headings[-1] if self.headings else "",
                        placeholder=attrs_dict.get("placeholder", ""),
                        value=normalize_text(value),
                    )
                )
        elif tag == "select":
            self._select = Field(
                tag="select",
                name=attrs_dict.get("name", ""),
                field_id=attrs_dict.get("id", ""),
                label_hint=self.headings[-1] if self.headings else "",
                value="",
            )
        elif tag == "option" and self._select is not None:
            self._capture_option = True
            self._current_option_value = attrs_dict.get("value", "")
            self._option_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._capture_title = False
        elif tag in {"h1", "h2", "h3"} and self._capture_heading == tag:
            heading = normalize_text("".join(self._heading_parts))
            if heading:
                self.headings.append(heading)
            self._capture_heading = None
            self._heading_parts = []
        elif tag == "textarea" and self._capture_textarea is not None:
            self._capture_textarea.value = normalize_text("".join(self._textarea_parts))
            self.fields.append(self._capture_textarea)
            self._capture_textarea = None
            self._textarea_parts = []
        elif tag == "option" and self._select is not None and self._capture_option:
            option_label = normalize_text("".join(self._option_parts))
            option_value = normalize_text(self._current_option_value or option_label)
            if option_value:
                self._select.value = "\n".join(part for part in [self._select.value, option_value] if part)
            self._capture_option = False
            self._current_option_value = ""
            self._option_parts = []
        elif tag == "select" and self._select is not None:
            self.fields.append(self._select)
            self._select = None

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self.page_title += data
        if self._capture_heading is not None:
            self._heading_parts.append(data)
        if self._capture_textarea is not None:
            self._textarea_parts.append(data)
        if self._capture_option:
            self._option_parts.append(data)


def parse_prompt_page(html_text: str) -> dict[str, object]:
    parser = PromptPageParser()
    parser.feed(html_text)
    fields = [
        {
            "tag": field.tag,
            "name": field.name,
            "id": field.field_id,
            "type": field.type,
            "label_hint": field.label_hint,
            "placeholder": field.placeholder,
            "value": field.value,
        }
        for field in parser.fields
        if field.value or field.placeholder
    ]
    body_parts: list[str] = []
    for field in fields:
        label = field.get("label_hint") or field.get("name") or field.get("id") or field.get("tag")
        value = field.get("value", "")
        if value:
            body_parts.append(f"## {label}\n{value}")
    return {
        "page_title": normalize_text(parser.page_title),
        "headings": parser.headings,
        "fields": fields,
        "prompt_text": "\n\n".join(body_parts).strip(),
    }


def load_inventory(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def mirror_url(row: dict[str, str], timeout: int) -> tuple[str, str, str | None]:
    prompt_id = row["prompt_id"]
    candidates = [
        row["prompt_url"],
        f"https://nanyo-city.jpn.org/download_prompt/download.php?download={prompt_id}",
        f"https://nanyo-line.github.io/prompt/{prompt_id}.html",
    ]
    seen: set[str] = set()
    errors: list[str] = []
    for url in candidates:
        if not url or url in seen:
            continue
        seen.add(url)
        try:
            final_url, html_text = fetch(url, timeout=timeout)
            return final_url, html_text, None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append(f"{url}: {exc}")
    return row["prompt_url"], "", " | ".join(errors)


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mirror(
    base_dir: Path,
    delay: float,
    limit: int | None,
    timeout: int,
    include_raw_html: bool = False,
    raw_html_dir: Path | None = None,
) -> dict[str, object]:
    inventory_path = base_dir / "inventory-unique.csv"
    if not inventory_path.exists():
        raise FileNotFoundError(f"missing inventory: {inventory_path}")
    rows = load_inventory(inventory_path)
    if limit is not None:
        rows = rows[:limit]

    retrieved_at = utc_now()
    prompts_dir = base_dir / "prompts"
    bodies_path = base_dir / "prompt-bodies.jsonl"
    errors: list[dict[str, str]] = []
    mirrored = 0
    empty_prompt_text = 0

    with bodies_path.open("w", encoding="utf-8") as bodies:
        for index, row in enumerate(rows, 1):
            prompt_id = int(row["prompt_id"])
            final_url, html_text, error = mirror_url(row, timeout=timeout)
            if error:
                errors.append({"prompt_id": row["prompt_id"], "title": row["title"], "error": error})
                continue
            parsed = parse_prompt_page(html_text)
            checksum = hashlib.sha256(html_text.encode("utf-8")).hexdigest()
            prompt_text = str(parsed["prompt_text"])
            if not prompt_text:
                empty_prompt_text += 1
            record: dict[str, object] = {
                "prompt_id": prompt_id,
                "title": row["title"],
                "source_category": row["source_category"],
                "source_url": row["prompt_url"],
                "retrieved_url": final_url,
                "retrieved_at": retrieved_at,
                "license": "CC BY 4.0; attribution: 南陽市",
                "raw_html_sha256": checksum,
                **parsed,
            }
            if include_raw_html:
                record["raw_html"] = html_text
            if raw_html_dir is not None:
                raw_html_dir.mkdir(parents=True, exist_ok=True)
                (raw_html_dir / f"{prompt_id:03d}.html").write_text(html_text, encoding="utf-8")
            write_json(prompts_dir / f"{prompt_id:03d}.json", record)
            bodies.write(
                json.dumps(
                    {
                        "prompt_id": prompt_id,
                        "title": row["title"],
                        "source_category": row["source_category"],
                        "source_url": row["prompt_url"],
                        "retrieved_url": final_url,
                        "retrieved_at": retrieved_at,
                        "license": record["license"],
                        "raw_html_sha256": checksum,
                        "prompt_text": prompt_text,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            mirrored += 1
            if delay and index < len(rows):
                time.sleep(delay)

    summary = {
        "retrieved_at": retrieved_at,
        "inventory_count": len(rows),
        "mirrored_count": mirrored,
        "error_count": len(errors),
        "empty_prompt_text_count": empty_prompt_text,
        "prompts_dir": str(prompts_dir),
        "prompt_bodies_jsonl": str(bodies_path),
        "include_raw_html": include_raw_html,
        "raw_html_dir": str(raw_html_dir) if raw_html_dir is not None else "",
        "errors": errors,
    }
    write_json(base_dir / "mirror-summary.json", summary)
    return summary


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE))
    parser.add_argument("--delay", type=float, default=0.03)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--include-raw-html",
        action="store_true",
        help="include fetched raw HTML in data/prompts/*.json; off by default",
    )
    parser.add_argument(
        "--raw-html-dir",
        type=Path,
        help="write fetched raw HTML files to this directory without embedding them in JSON",
    )
    args = parser.parse_args(argv)

    summary = mirror(
        Path(args.base_dir),
        args.delay,
        args.limit,
        args.timeout,
        include_raw_html=args.include_raw_html,
        raw_html_dir=args.raw_html_dir,
    )
    print(json.dumps({k: v for k, v in summary.items() if k != "errors"}, ensure_ascii=False))
    if summary["error_count"]:
        print(json.dumps({"errors": summary["errors"][:10]}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
