#!/usr/bin/env python3
"""Search local Nanyo prompt records and build compact agent packets."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_PROMPTS_DIR = Path("data/prompts")
DEFAULT_MAX_CHARS = 1400
TARGETS = {"codex", "skill", "subagent", "pdca"}


@dataclass(frozen=True)
class PromptRecord:
    prompt_id: int
    title: str
    source_category: str
    source_url: str
    retrieved_url: str
    raw_html_sha256: str
    prompt_text: str


@dataclass(frozen=True)
class SearchHit:
    score: int
    record: PromptRecord


def normalize_query(query: str) -> list[str]:
    terms = [term.strip().lower() for term in re.split(r"\s+", query) if term.strip()]
    return list(dict.fromkeys(terms))


def load_prompt_records(prompts_dir: Path) -> list[PromptRecord]:
    records: list[PromptRecord] = []
    for path in sorted(prompts_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        records.append(
            PromptRecord(
                prompt_id=int(data["prompt_id"]),
                title=str(data.get("title", "")),
                source_category=str(data.get("source_category", "")),
                source_url=str(data.get("source_url", "")),
                retrieved_url=str(data.get("retrieved_url", "")),
                raw_html_sha256=str(data.get("raw_html_sha256", "")),
                prompt_text=str(data.get("prompt_text", "")),
            )
        )
    if not records:
        raise FileNotFoundError(f"no prompt JSON files found in {prompts_dir}")
    return records


def score_record(record: PromptRecord, terms: Iterable[str], category: str = "") -> int:
    haystacks = {
        "title": record.title.lower(),
        "category": record.source_category.lower(),
        "text": record.prompt_text.lower(),
    }
    score = 0
    for term in terms:
        if term in haystacks["title"]:
            score += 12
        if term in haystacks["category"]:
            score += 8
        if term in haystacks["text"]:
            score += min(10, haystacks["text"].count(term))
    if category and category.lower() in haystacks["category"]:
        score += 10
    return score


def search_prompts(
    records: list[PromptRecord],
    query: str,
    category: str = "",
    limit: int = 5,
) -> list[SearchHit]:
    terms = normalize_query(query)
    hits = [
        SearchHit(score=score_record(record, terms, category), record=record)
        for record in records
    ]
    filtered = [hit for hit in hits if hit.score > 0]
    filtered.sort(key=lambda hit: (-hit.score, hit.record.prompt_id))
    return filtered[:limit]


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def hit_to_dict(hit: SearchHit, max_chars: int) -> dict[str, object]:
    record = hit.record
    return {
        "score": hit.score,
        "prompt_id": record.prompt_id,
        "title": record.title,
        "source_category": record.source_category,
        "source_url": record.source_url,
        "retrieved_url": record.retrieved_url,
        "raw_html_sha256": record.raw_html_sha256,
        "prompt_text": truncate_text(record.prompt_text, max_chars),
    }


def build_packet(hits: list[SearchHit], query: str, target: str, max_chars: int) -> dict[str, object]:
    if target not in TARGETS:
        raise ValueError(f"unknown target: {target}")
    selected = [hit_to_dict(hit, max_chars=max_chars) for hit in hits]
    return {
        "query": query,
        "target": target,
        "selected_count": len(selected),
        "source": {
            "name": "山形県南陽市 生成AI活用実例集",
            "license": "CC BY 4.0; attribution: 南陽市",
            "ssot": "data/prompts/*.json",
        },
        "orchestration": {
            "use": "Treat selected prompts as source patterns, not as final instructions.",
            "adaptation_steps": [
                "Keep prompt_id, title, source URL, and checksum in the working note.",
                "Extract reusable role, input, constraints, output format, and guardrails.",
                "Remove duplicate or task-irrelevant wording before sending to an agent.",
                "For high-stakes, public, personal-data, or external-send tasks, add an explicit review gate.",
            ],
            "target_instruction": target_instruction(target),
        },
        "prompts": selected,
    }


def target_instruction(target: str) -> str:
    instructions = {
        "codex": "Use the selected prompt patterns as local context for the current Codex task.",
        "skill": "Convert stable repeated behavior into SKILL.md instructions with source attribution.",
        "subagent": "Write a bounded sub-agent packet with goal, inputs, stop condition, and expected evidence.",
        "pdca": "Run Plan, Do, Check, Act with explicit evidence and next-action ownership.",
    }
    return instructions[target]


def render_markdown(packet: dict[str, object]) -> str:
    lines = [
        f"# Nanyo Prompt Packet: {packet['target']}",
        "",
        f"- query: {packet['query']}",
        f"- selected_count: {packet['selected_count']}",
        "- source: 山形県南陽市 生成AI活用実例集 / CC BY 4.0",
        "",
        "## Orchestration",
    ]
    orchestration = packet["orchestration"]
    assert isinstance(orchestration, dict)
    lines.append(f"- use: {orchestration['use']}")
    lines.append(f"- target_instruction: {orchestration['target_instruction']}")
    lines.append("")
    lines.append("## Selected Prompts")
    prompts = packet["prompts"]
    assert isinstance(prompts, list)
    for prompt in prompts:
        assert isinstance(prompt, dict)
        lines.extend(
            [
                "",
                f"### #{prompt['prompt_id']} {prompt['title']}",
                f"- score: {prompt['score']}",
                f"- category: {prompt['source_category']}",
                f"- source_url: {prompt['source_url']}",
                f"- url: {prompt['retrieved_url']}",
                f"- raw_html_sha256: {prompt['raw_html_sha256']}",
                "",
                str(prompt["prompt_text"]),
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="keywords to search in title, category, and prompt text")
    parser.add_argument("--prompts-dir", type=Path, default=DEFAULT_PROMPTS_DIR)
    parser.add_argument("--category", default="")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--target", choices=sorted(TARGETS), default="codex")
    parser.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args(argv)

    records = load_prompt_records(args.prompts_dir)
    hits = search_prompts(records, query=args.query, category=args.category, limit=args.limit)
    packet = build_packet(hits, query=args.query, target=args.target, max_chars=args.max_chars)
    if args.format == "markdown":
        print(render_markdown(packet), end="")
    else:
        print(json.dumps(packet, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
