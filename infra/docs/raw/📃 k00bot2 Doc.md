# 📃 k00bot2 Doc

_created: 20251220T235553Z / updated: 20251221T062439Z_

k00bot2

```
xbot-project/
  settings.yaml
  prompts.yaml
  requirements.txt
  .env.example

  data/
    urls/
      sitemap/                      # sitemap抽出結果（ドメイン別txt）
      page_urls.jsonl               # 記事URL一覧（メタ付き）
      page_urls.txt                 # 記事URL一覧（URLだけ）
    pages/                          # 記事ごとの抽出結果（1ページ=1json）
      example.com/
    candidates/
      article_candidates.jsonl      # 記事由来の投稿候補
      xposts.jsonl                  # X過去投稿由来の投稿候補
      candidates.jsonl              # 上2つを統合した最終候補
      manual_candidates.jsonl       # 手動候補（追記型・消えない運用にする場合）
    state/
      page_fetched.jsonl            # HTML取得済みURL
      page_llm_done.jsonl           # LLM抽出済みページID
      processed_tweet_ids.jsonl     # 収集・判定済みtweet_id（アーカイブ/最新100共通）
      posted_candidate_ids.jsonl    # 実際に投稿したcandidate_id
      overrides.jsonl               # 手動上書き（任意）
      markers/
        x_archive_import_done.txt   # アーカイブ処理済みの印

  scripts/
    __init__.py
    config.py
    utils/
      __init__.py
      io.py
      text.py
      dedup.py
      html.py
      llm.py
      x_api.py
    pipeline/
      __init__.py
      sitemap_to_urls.py
      build_page_urls.py
      fetch_pages.py
      extract_article_candidates.py
      import_x_archive.py
      fetch_x_latest.py
      merge_candidates.py
      post_daily.py
      add_manual_candidate.py

  run/
    monthly.sh
    daily.sh
```

Setup

environment

```
cd k00bot2
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x run/monthly.sh run/daily.sh
```

settings

.env APIキー
settings.yaml ブログやインタビュー記事、Xアカウント、使用するLLM種類をセット
prompts.yaml LLMのプロンプト
data/state/overrides.jsonl スコアの調整と無効化

```
{"candidate_id":"abc123...","manual_score":5}
{"candidate_id":"abc123...","status":"disabled"}
```

Posting config

post_
daily.py
 は settings.yaml の posting を参照します。

例（1日3投稿、15分間隔）

```
posting:
  min_score: 2
  pick_strategy: "weighted_random"
  daily_post_limit: 3
  interval_seconds: 900
```

crontab

```
crontab -e
```

```
#!/usr/bin/env bash
set -euo pipefail
cd /src/k00bot2
source .venv/bin/activate

python -m scripts.pipeline.post_daily
```

例：毎日 06:10 に投稿、毎月1日 03:20 に候補更新

```
10 6 * * * /src/k00bot2/run/daily.sh >> /src/k00bot2/data/log_daily.txt 2>&1
20 3 1 * * /src/k00bot2/run/monthly.sh >> /src/k00bot2/data/log_monthly.txt 2>&1
```

注意事項

candidates.jsonl を直接編集しない

data/candidates/candidates.jsonl は merge_
candidates.py
 が 毎回作り直すため、 ここを直接編集すると次回 merge_candidates 実行で消えます。

手動で投稿候補をつくる

data/candidates/manual_candidates.jsonlに追記し、下記の統合を実行。

```
python -m scripts.pipeline.merge_candidates
```

X Archive

```
# data/x_archive にアーカイブを置いた後に実行
python -m scripts.pipeline.import_x_archive
# （以降は marker により自動でスキップされます）
```

Monthly

```
# 1) sitemap.xml -> ドメイン別URL抽出（独立プログラム）
python -m scripts.pipeline.sitemap_to_urls --all

# 2) sitemap抽出結果 + interviews を結合して page_urls を作成
python -m scripts.pipeline.build_page_urls

# 3) HTML取得 + 本文抽出（ページごとにJSON作成）
python -m scripts.pipeline.fetch_pages

*取得

# 4) LLMで名言抽出 → article_candidates.jsonl へ
python -m scripts.pipeline.extract_article_candidates

*編集後に jsonl を作り直す（LLMなし）
python -m scripts.pipeline.extract_article_candidates --build-only

# 5) Xの最新100件を取得 → LLM採点 → xposts.jsonl へ
python -m scripts.pipeline.fetch_x_latest

# 6) 2種の候補を統合 → candidates.jsonl
python -m scripts.pipeline.merge_candidates
```

Daily

```
python -m scripts.pipeline.post_daily
# テスト
python -m scripts.pipeline.post_daily --dry-run
```
