# 読み出しオーケストレーション設計

## 目的

南陽市公開プロンプトを、公開可能な素材庫から Codex / skill / sub-agent / PDCA に渡せる運用 packet へ変換する。

## 境界

| layer | 責務 | SSOT |
|---|---|---|
| source mirror | 公開プロンプト本文、出典、取得 URL、checksum を保持する | `data/prompts/*.json` |
| search router | 目的語から候補 prompt を抽出し、score つき packet にする | `scripts/nanyo_prompt_router.py` |
| adapter skill | 候補 prompt を作業用の役割、入力、制約、出力形式、検証条件へ再構成する | `skills/nanyo-prompt-adapter/SKILL.md` |
| execution lane | Codex / skill / sub-agent / PDCA で実タスクに適用する | 呼び出し側の task / repo |

## 基本フロー

```text
user intent
  -> nanyo_prompt_router.py query
  -> selected prompt packet
  -> nanyo-prompt-adapter
  -> task-specific instruction
  -> evidence / review / PDCA
```

## ガード

- `data/prompts/*.json` を source original として扱い、改変版は混ぜない。
- packet には `prompt_id`、`retrieved_url`、`raw_html_sha256` を残す。
- high-stakes、個人情報、公開、外部送信は呼び出し側で明示 review gate を追加する。
- router は候補抽出までであり、実行や外部送信はしない。

## 運用保証の境界

この repo が保証するのは、ローカル prompt records から候補 packet を生成できることまで。
任意の AI runtime が必要時に自動で読むことは、呼び出し側の integration が必要。
