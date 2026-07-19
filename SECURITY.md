# Security Policy

nanyo-prompt-orchestrator は、山形県南陽市が公開している生成AIプロンプト集の
ローカルミラーと活用補助ラインです。公開データのみを扱います。

## Supported Boundary

- 入力は南陽市の公開ページから取得した公開プロンプトだけです。
- credential を要求せず、外部サービスへの送信も行いません。
- `data/` 配下は公式由来の mirror (CC BY 4.0、出典: `references/license.md`) です。
- スクリプトはローカル実行前提です。ネットワークアクセスは公開プロンプトの取得のみで、
  接続先は次の 3 ホストに限定されます (`scripts/nanyo_prompt_mirror.py` の候補 URL 参照)。
  - `www.city.nanyo.yamagata.jp` (公式ページ)
  - `nanyo-city.jpn.org` (プロンプト配信フォーム)
  - `nanyo-line.github.io` (フォールバックミラー)

## Sensitive Data

次のものを commit しません。

- API key、token、cookie、browser profile。
- `nexus_ai` の private 文脈、公開前提でない運用メモ。
- Discord raw / 個人ログ / ローカル環境依存設定。
- local absolute path、個人を特定できる情報。

## Reporting

sensitive data や脆弱性を発見した場合は、次のいずれかで報告してください。

- GitHub の Private vulnerability reporting (本リポジトリの Security タブ → Report a vulnerability)
- 上記が使えない場合は GitHub Issue (sensitive な詳細は Issue 本文に貼らず、連絡希望の旨のみ記載)

報告を受けたメンテナ側は、公開を止め、必要なら credential を rotate し、
該当データを取り除いてから public release checklist を再実行します。
