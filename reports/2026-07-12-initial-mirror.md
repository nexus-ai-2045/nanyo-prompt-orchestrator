# 2026-07-12 初期ミラー

## 目的

`nexus_ai` から切り離した独立 repo として、南陽市公開プロンプトをローカルで検索・分類・変換・PDCAできる状態にする。

## 完了条件

- `data/inventory-unique.csv` が 825 prompt を持つ。
- `data/prompts/*.json` が 825 files。
- `data/prompt-bodies.jsonl` が 825 lines。
- `data/mirror-summary.json` の `error_count` が 0。
- `python3 -m py_compile scripts/nanyo_prompt_inventory.py scripts/nanyo_prompt_mirror.py` が通る。

## 実行結果

[実測: command output] `python3 scripts/nanyo_prompt_inventory.py --out-dir data`

```text
{"source_rows": 826, "unique_prompt_ids": 825, "out_dir": "data"}
```

[実測: command output] `python3 scripts/nanyo_prompt_mirror.py --base-dir data --delay 0.02 --timeout 25`

```text
{"retrieved_at": "2026-07-12T01:29:34.392730+00:00", "inventory_count": 825, "mirrored_count": 825, "error_count": 0, "empty_prompt_text_count": 0, "prompts_dir": "data/prompts", "prompt_bodies_jsonl": "data/prompt-bodies.jsonl"}
```

[実測: command output] 追加検証:

```text
data/prompts/*.json: 825 files
data/prompt-bodies.jsonl: 825 lines
data/inventory-unique.csv: 825 rows + header
python3 -m py_compile scripts/nanyo_prompt_inventory.py scripts/nanyo_prompt_mirror.py: pass
sample IDs 1 / 370 / 573 / 656 / 799 / 825: raw_html_sha256 and prompt_text present
repo size: 35M
```

## 2026-08-05 更新

- `data/prompts/*.json` から `raw_html` 本文を削除した。
- `raw_html_sha256`、取得 URL、取得日時、抽出済み `prompt_text` は保持した。
- 取得 HTML が必要な場合は `scripts/nanyo_prompt_mirror.py --include-raw-html` または
  `--raw-html-dir data/raw-html` で再取得する。

## 未実施

- GitHub 作成、push、公開範囲変更は未実施。
- `nexus_ai` private 文脈、Discord raw、個人ログ、API key、cookie は入れていない。
- ローカル改変版 prompt の生成は未実施。生成する場合は `source_original` と `nexus_adapted` を分ける。
