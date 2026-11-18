---
name: nanyo-prompt-adapter
description: "Use when selecting, adapting, mirroring, or PDCA-reviewing prompts from Nanyo City's public generated-AI prompt collection for Codex tasks, sub-agent tickets, reports, drafts, fact checks, workflow design, Japanese business prompts, or municipal/DX support."
---

# Nanyo Prompt Adapter

## 役割

南陽市公開プロンプト集のローカルミラーから、目的に合う prompt を選び、Codex / sub-agent 用に再構成する。

## 必ず見るファイル

- `data/inventory-unique.csv`
- `data/mirror-summary.json`
- `references/pattern-map.md`

必要な時だけ見る:

- `data/prompts/<id>.json`: 個別 prompt の全文と抽出フィールド。
- `data/prompt-bodies.jsonl`: 全文検索や候補抽出。
- `references/license.md`: 出典・CC BY 4.0 表記。

## 手順

1. ユーザーの目的を `search / implement / review / operate / ideate / decide` のどれかに置く。
2. `references/pattern-map.md` の中核パターンから近いものを選ぶ。
3. まず `scripts/nanyo_prompt_router.py "<query>" --target codex|skill|subagent|pdca` を使い、候補 ID を最大 10 件に絞る。
4. CLI が足りない場合だけ、`data/inventory-unique.csv` または `data/prompt-bodies.jsonl` を直接検索する。
5. 候補が必要十分なら `data/prompts/<id>.json` を読む。
6. prompt 本文をそのまま使うか、役割・入力変数・制約・出力形式・検証条件へ再構成する。

## 停止線

- 医療、法律、金融、採用、人事評価、個人の心理状態判断は high-stakes として扱う。
- 対人文面は相手の余白を増やす gate を通す。
- 公開・投稿・共有・外部送信は、現在会話で対象と操作の明示承認があるまで実行しない。
- ローカル改変版を作る時は `source_original` と `nexus_adapted` を分ける。
