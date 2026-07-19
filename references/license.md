# ライセンスメモ

[事実: 2026-07-19 に公式ページ (city.nanyo.yamagata.jp/dxchosei/5793) の「著作権について」を実測確認。公式サイトは https 非対応 (TLS 接続不可) で http のみ 200。表記確認は Wayback Machine 2026-06-10 スナップショット + http ライブページで実施: 著作権は南陽市に帰属し、特に断りのない限り CC BY 4.0 で提供、出典 (南陽市) 明記で営利利用・複製・改変・再配布可] 本リポジトリは、南陽市公開プロンプトのローカルミラーと活用補助ラインです。

標準表記:

```text
出典: 山形県南陽市「一発OK!! 市民も使える！生成AI活用実例集（プロンプト集）」
出典URL: http://www.city.nanyo.yamagata.jp/dxchosei/5793
ライセンス: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/deed.ja)
```

運用:

- `data/prompts/*.json` は公式由来の raw mirror として扱う。
- ローカル改変版を作る場合は `source_original` と `nexus_adapted` を分ける。
- 生成AIの出力結果は利用者側でファクトチェックする。
