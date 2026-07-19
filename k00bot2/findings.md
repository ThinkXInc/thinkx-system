# k00bot2 findings

- **2026-07-19 monthly バグ修正 + data の git 管理化(オーナー裁定)。** ①utils/io.py に欠落していた `read_lines` / `write_lines` を追加(sitemap_to_urls と build_page_urls の ImportError 解消)。②.gitignore を縮小し data を track(除外は x_archive 294MB とログのみ)。③run/daily.sh・monthly.sh の末尾で data を自動 commit + push(push 失敗でも投稿/候補生成は成立済みなので警告のみ)。push には書込み可 deploy key `deploy_thinkx-system-rw` が必要 — **D-1(deploy key は read-only)の意図的例外**。鍵は EC2 上で生成し GitHub へ手動登録(deploy_ec2.md 手順7)。投稿時刻は朝6時 JST で確定(15:10 JST だった実挙動は採らない)。

- **2026-07-19 monthly パイプラインは 1月以降ずっと失敗している(コードバグ・EC2 でも再現)。** `scripts/pipeline/sitemap_to_urls.py` が `from ..utils.io import ensure_dir, write_lines` するが、`write_lines` は utils/io.py に存在しない(HEAD cfa8d5b でも欠落。1/14 の io.py 改修で落ちたとみられる — 履歴は凍結原本 kazukiotsuka/k00bot2 側)。このため monthly.sh は手順1で ImportError 即死(supercom2 の log_monthly.txt: 最終試行 7/1 03:20 も失敗)。candidates.jsonl は 1/14、xposts.jsonl も 1/14 から未更新で、daily は古い候補プールから投稿し続けている。修正は io.py への write_lines 追加(数行)だがコード変更のためオーナー判断待ち。
- **2026-07-19 ライブデータの移行は git を介さない(取り込み不要)。** 毎月/毎日更新されるデータ(candidates/*.jsonl・state/*.jsonl・pages/・urls/)は .gitignore 済みで repo には元々入らない。supercom2 → EC2 へ tar で直接移行済み(7/19)。tracked のデータファイル(overrides.jsonl 空・12月の .bak 群)は supercom2 と同一で、EC2 worktree の `git status -- k00bot2/data` はクリーン(pull に支障なし)。

- **2026-07-19 supercom2 の実投稿時刻は 06:10 UTC(= 15:10 JST)だった。** data 移行で持ち込んだ log_daily.txt の実行痕跡が 7/17 06:10:03 UTC(403 で全滅)・7/18 06:10:12 UTC(2/2 成功)と、いずれも UTC の 06:10 ちょうど。supercom2 の `date` は JST を返すが、cron はドキュメント意図(JST 06:10 = 朝)でなく UTC 06:10 で発火していた(cron デーモンが timezone 変更前の環境のままだった型とみられる)。EC2 の /etc/cron.d/k00bot2 はドキュメント意図どおり 21:10 UTC(= JST 06:10)に設定。近過去の実挙動(15:10 JST)に合わせるかはオーナー判断。
- **2026-07-19 EC2 切替直後の log_daily.txt tail は supercom2 時代の履歴。** mtime 2026-07-18 06:10:12 UTC(tar が mtime 保存)< 切替 2026-07-19 02:41 UTC。末尾の 403 traceback と posted 2/2 はいずれも移行前の記録で、EC2 初回実行は 2026-07-19 21:10 UTC。
- **2026-07-19 7/17 の run は 1 候補目の X API 403(You are not permitted)で raise し当日全滅、7/18 は 2/2 成功。** 单発の 403 は重複コンテンツ拒否か一時制限の可能性。EC2 初回実行後に再発しないか監視。
- **venv 名の不整合(元からある)**: docs/k00bot2.md と README は `.venv` だが run/daily.sh は `venv` を source。実配備(supercom2・EC2 とも)は `venv`。コードは変更しない。
