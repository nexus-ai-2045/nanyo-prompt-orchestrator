# Security Policy

nanyo-prompt-orchestrator は、山形県南陽市が公開している生成AIプロンプト集の
ローカルミラーと活用補助ラインです。公開データのみを扱います。

## Supported Boundary

- 入力は南陽市の公開ページから取得した公開プロンプトだけです。
- credential を要求せず、外部サービスへの送信も行いません。
- `data/` 配下は公式由来の raw mirror (CC BY 4.0、出典: `references/license.md`) です。
- スクリプトはローカル実行前提で、ネットワークアクセスは公式ページの取得のみです。

## Sensitive Data

次のものを commit しません。

- API key、token、cookie、browser profile。
- `nexus_ai` の private 文脈、公開前提でない運用メモ。
- Discord raw / 個人ログ / ローカル環境依存設定。
- local absolute path、個人を特定できる情報。

## Reporting

sensitive data が見つかった場合は公開を止め、必要なら credential を rotate し、
該当データを取り除いてから public release checklist を再実行します。
