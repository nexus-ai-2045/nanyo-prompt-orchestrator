# nanyo-prompt-orchestrator

南陽プロンプト運用補助ライン。

山形県南陽市が公開している生成AIプロンプト集を、ローカルで検索・分類・変換・PDCAできる形にするための独立リポジトリです。

## 責務

- 南陽市公開プロンプトの一覧と本文をローカルに保存する。
- プロンプトを ID、カテゴリ、本文、取得URL、checksum で検索できるようにする。
- Codex / sub-agent 向けに、プロンプト候補抽出、再構成、リスク確認、PDCA を支援する。
- 出典、ライセンス、取得日時、抽出結果を分けて保持する。

## 入れないもの

- `nexus_ai` の private 文脈
- Discord raw / 個人ログ / ローカル環境依存設定
- API key / cookie / browser profile
- 公開前提でない運用メモ

## ディレクトリ

```text
data/
  inventory-all.csv
  inventory-unique.csv
  inventory-summary.json
  mirror-summary.json
  prompt-bodies.jsonl
  prompts/*.json
references/
  license.md
  pattern-map.md
scripts/
  nanyo_prompt_inventory.py
  nanyo_prompt_mirror.py
skills/
  nanyo-prompt-adapter/SKILL.md
reports/
  2026-07-12-initial-mirror.md
```

## 使い方

```bash
python3 scripts/nanyo_prompt_inventory.py --out-dir data
python3 scripts/nanyo_prompt_mirror.py --base-dir data --delay 0.02 --timeout 25
```

## 出典

出典: 山形県南陽市「一発OK!! 市民も使える！生成AI活用実例集（プロンプト集）」

ライセンス: CC BY 4.0。詳細は `references/license.md` を参照してください。
