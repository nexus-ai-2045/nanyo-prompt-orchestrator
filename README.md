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

## 3分で使う

このリポジトリは、公開プロンプトをそのまま眺めるだけでなく、AI に渡す前の「候補抽出」「要約」「組み替え」に使うための素材庫です。

```bash
git clone https://github.com/nexus-ai-2045/nanyo-prompt-orchestrator.git
cd nanyo-prompt-orchestrator
python3 - <<'PY'
import json
from pathlib import Path

for line in Path("data/prompt-bodies.jsonl").open():
    row = json.loads(line)
    if "議事録" in row.get("prompt_text", "") or "要約" in row.get("prompt_text", ""):
        print(row["prompt_id"], row.get("title", ""))
        print(row["prompt_text"][:300].replace("\\n", " "))
        print()
        break
PY
```

## 探す

キーワードで探す:

```bash
python3 - <<'PY'
import json
from pathlib import Path

keyword = "アンケート"
for line in Path("data/prompt-bodies.jsonl").open():
    row = json.loads(line)
    text = row.get("prompt_text", "")
    if keyword in text or keyword in row.get("title", ""):
        print(f'{row["prompt_id"]}: {row.get("title", "")}')
PY
```

カテゴリ一覧を確認する:

```bash
python3 - <<'PY'
import csv
from collections import Counter

with open("data/inventory-unique.csv", newline="") as f:
    rows = list(csv.DictReader(f))

for category, count in Counter(row.get("source_category", "") for row in rows).most_common():
    print(f"{count:>3} {category}")
PY
```

## AI に渡す

1. `data/prompt-bodies.jsonl` から近い用途のプロンプトを 3-10 件だけ選ぶ。
2. そのまま貼らず、目的・入力・出力形式・禁止事項を今のタスクに合わせて短くする。
3. `skills/nanyo-prompt-adapter/SKILL.md` の手順で、重複除去、出典保持、リスク確認、PDCA に分ける。

AI への依頼例:

```text
この JSONL から「議事録要約」に近いプロンプトを最大5件選び、
共通する型、使い回せる指示、今の業務に合わせて削るべき文を分けてください。
出典の prompt_id は残してください。
```

## 更新する

```bash
python3 scripts/nanyo_prompt_inventory.py --out-dir data
python3 scripts/nanyo_prompt_mirror.py --base-dir data --delay 0.02 --timeout 25
```

更新後は件数と空本文を確認します。

```bash
python3 - <<'PY'
import json
from pathlib import Path

summary = json.loads(Path("data/mirror-summary.json").read_text())
print({
    "inventory_count": summary["inventory_count"],
    "mirrored_count": summary["mirrored_count"],
    "error_count": summary["error_count"],
    "empty_prompt_text_count": summary["empty_prompt_text_count"],
})
PY
```

## 使い分け

| やりたいこと | 見る場所 |
|---|---|
| まず読む | `README.md` |
| 全文検索や候補抽出 | `data/prompt-bodies.jsonl` |
| 個別プロンプトの HTML / checksum まで確認 | `data/prompts/*.json` |
| 出典とライセンス確認 | `references/license.md` |
| パターン別に整理 | `references/pattern-map.md` |
| AI / sub-agent へ運用手順として渡す | `skills/nanyo-prompt-adapter/SKILL.md` |

## ライセンスと出典

### コード (scripts/ / skills/ ほか)

MIT License (`LICENSE` 参照)。

### ミラーデータ (data/)

- 出典: 山形県南陽市「一発OK!! 市民も使える！生成AI活用実例集（プロンプト集）」
- 出典URL: https://www.city.nanyo.yamagata.jp/dxchosei/5793
- ライセンス: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.ja)。
  公式ページ「著作権について」に基づく (著作権は南陽市に帰属。出典を明記することで
  営利目的での利用・複製・改変・再配布が可能。「特に断りのない限り」の留保あり)。
- 各プロンプトの取得 URL・取得日時・checksum は `data/prompts/*.json` に保持。
- 変更の有無: `data/prompts/*.json` は無改変の raw mirror。改変版を作る場合は
  `source_original` と `nexus_adapted` を分離する (`references/license.md` 参照)。

`LICENSE` (MIT) はコード部分のみに適用され、`data/` 配下には適用されません。
