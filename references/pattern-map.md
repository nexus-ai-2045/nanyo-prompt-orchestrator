# 南陽市生成AIプロンプト活用マップ

## 中核パターン

| pattern | 使いどころ | 代表 ID | 活用 |
|---|---|---:|---|
| prompt-finder | やりたいことから適切な prompt を探す | 370 | 大量 prompt / skill / docs のルーター |
| prompt-converter | 雑な要望を実行可能な prompt に変換する | 583 | ユーザー発話を task / ticket へ変換 |
| autonomous-driver | 1文の目的から分解、実行、自己評価まで回す | 656 | thin slice / PDCA 併走 |
| role-thinking-trainer | 役職・立場ごとの思考訓練を設計する | 799 | role 別レビュー |
| fact-check | 情報の信頼性、根拠、注意点を検証する | 573 | source first / hallucination gate |
| draft-starter | 良いたたき台を作る | 801 | report、note、提案文、仕様書の初稿 |
| anxiety-support | AI利用が不安な人向けに安全な始め方へ落とす | 802 | onboarding |
| decision-helper | 判断に迷った時、選択肢・基準・次手を整理する | 803 | decision packet |
| scenario-builder | 部門別に活用シナリオと推奨 prompt を作る | 622 | 顧客・部門別 AI 導入支援 |
| ai-dialogue-agent | 生成AI対話エージェントとして聞き返しながら支援する | 539 | sub-agent 初期プロンプト |

## PDCA

```text
Plan: inventory と mirror-summary を読む
Do: ローカル prompt から目的に合う候補を抽出する
Check: high-stakes / 対人 / fact / source / outdated を検査する
Act: prompt、sub-agent ticket、report、skill 更新案へ落とす
```
