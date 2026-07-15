# findings — auth 前倒しトラック (Phase 4a)

形式: `ファイル:行 / 事実`。解釈・修正方針は書かない。Phase 4b / Phase 3 の入力。
セキュリティ疑い (D-22) は本ファイルに流さず即停止・人間報告する運用。本セッションで D-22 該当なし。

## 起動足場の確立中に観測した事実

- `.claude/settings.json:4-56` / deny 配列に `quantz-web/web-server/libcommon/**` 等はあるが、auth 自身の
  `web-server/libcommon/**`(vendored)への Edit/Write deny は無い。auth/CLAUDE.md 前倒し条件3 は
  「vendored コピーは .claude/settings.json の deny と VERSION のハッシュ照合で強制」と記す。
- `docs/AUTH_TRACK.md` / 不在。DECISIONS D-25・D-26 と `auth/CLAUDE.md`(改訂版・前倒し実装の条件)が
  参照するが、workspace・auth いずれにもファイルが無い。
- `web-server/config.py.example:1-56` / `PASSWORD_ENCRYPT_KEY` を含まない。
  `web-server/libcommon/cipher.py:36` が `REQUIRED_KEYS_IN_CONFIG=['PASSWORD_ENCRYPT_KEY']` を要求し、
  `models/data/user.py:25` の `from libcommon.cipher import Cipher` 経由で import 時に check_config が落ちる。
  本セッションで `config.py`(example の複製)に `PASSWORD_ENCRYPT_KEY`(ダミー値)を追加した。
- `web-server/models/data/user.py:48-52` / `UnauthorizedAccessError` が未定義だった。
  `web-server/libcommon/web/flask_helpers.py:8` が `from models.data.user import User, UnauthorizedAccessError, UserNotFoundError`
  を import する(同8行に `# NEEDSFIX: don't depend on data.user`)。本セッションで同名例外クラスを追加した。
- `web-server/requirements.txt` / 元は `Flask redis mongoengine pymongo pytz pydantic msgpack google-auth` の
  8件のみで、`pycryptodome`・`requests` が未列挙だった。
  `web-server/libcommon/cipher.py:21` `from Crypto import Random`(pycryptodome)、
  `web-server/libcommon/web/google_oauth_helper.py` の `google.auth.transport.requests`(requests)が import 時に要求する。
  本セッションで両者を追加・ピンした。
- `web-server/requirements.txt` / `redis` を `5.2.1` にピンした。`redis==8.0.1`(pip 既定で入る最新)は
  `fakeredis==2.26.2` と実行時非互換で、`web-server/libcommon/web/session.py:83` の `self.__redis.ping()` が
  fakeredis 接続で `ResponseError`(RESP3 HELLO ハンドシェイク)を出す。`fakeredis 2.26.2` の宣言依存は
  `redis>=4.3`(緩い)で pip は 8.0.1 を許容する。
- `web-server/sso.py:53` `Locale('sso.json')` / `web-server/accounts.py:45` `Locale('accounts.json')` /
  bare ファイル名。`web-server/libcommon/locale.py:99` は与えられたパスを cwd 相対で `open()` する。
  実体は `web-server/locales/sso.json`・`web-server/locales/accounts.json`。
  quantz-web は `Config.LOCALES_ROOT`(`quantz-web/web-server/config.py:67` = `join(SRC_ROOT,'locales')`、絶対)
  で Locale を呼ぶ。quantz-web の uwsgi は `chdir=../web-server`(`quantz-web/web-server/uwsgi/uwsgi.ini:9`)。
  本セッションは `tests/conftest.py` で import 時 cwd を `web-server/locales` に移して解決した(app ソースは未変更)。
- `web-server/libcommon/web/http_response_formatter.py:54,56` / `Field(default=None, example='user_id')` /
  `Field(..., example='Error message here.')` が pydantic V2 の `PydanticDeprecatedSince20` warning を出す。
- 環境 / 既定 `python3` は `3.9.2rc1`(workspace CLAUDE.md 記載の要件 3.10+ 未満)。
  `/opt/homebrew/bin/python3.11`(3.11.15)が存在。本セッションの `.venv` は python3.11 で作成した。
- `web-server/libcommon/web/flask_helpers.py:8` / libcommon が host アプリの `models.data.user` を import する
  レイヤ逆転(DECISIONS D-8 が L-1 で解消予定とする面)。auth は現行 pre-v2.0.0 スナップショットに対して
  この結合を満たす形で書かれている。
- `scripts/bake_libcommon_snapshot.sh:24` / tree_sha256 の計算が `find . -type f ! -name VERSION` で、
  `__pycache__/*.pyc` を除外しない。テスト実行や本番 import で `web-server/libcommon/**/__pycache__/*.pyc`
  (16件、`.gitignore` 済み・git 追跡0)が生成されると、`find ... | xargs sha256sum | sha256sum` の再計算が
  焼き込み時の値(`eab9e78...`)と不一致になる。`__pycache__`・`*.pyc` を除外して再計算すると一致する
  (= vendored source は無編集)。ハッシュ照合(D-25 条件3 / D-10 CI 照合)は .pyc を除外する必要がある。

## Phase 4b (libcommon v2.0.0 追随) の実施中に観測した事実

- `libcommon/scripts/bake.sh` (L-8) / tree_sha256 を `-not -path '*/__pycache__/*' -not -name '*.pyc'`
  で算出する。上の pre-v2.0.0 スクリプトの .pyc 混入問題は L-8 側で解消済み。auth 側 `scripts/bake_libcommon_snapshot.sh`
  は F-1 に従い削除した(正典は libcommon/scripts/bake.sh の1本)。
- `web-server/libcommon/VERSION` / 焼き直し後 `version: v2.0.0` / tree_sha256 `3359309a30a392a75a97b3fad594569487cb07068f770877202de3096fb57cf0`。
  この値は quantz-web(Q-6)の vendored `web-server/libcommon/VERSION` と**一致**する。同一 tag を同一 bake.sh で焼くと
  消費者間で byte 同一(再現可能 vendoring)であることの実測。
- `libcommon/scripts/bake.sh` は `.git` のみ除去し、`tests/` `tutorials/` `refactor_plan.md` `findings.md`
  `CLAUDE.md` `attic/` `ruff.toml` `pyrightconfig.json` `scripts/` を vendored 配下に含める(quantz-web Q-6 も同形)。
  auth の旧スクリプトは `tests/tutorials` を除去していたため、v2.0.0 追随で vendored 構成が増える(挙動には無影響。
  auth の pytest は `tests/` のみを対象に走るため libcommon/tests は収集されない)。
- `web-server/libcommon/web/flask_helpers.py`(pre-v2.0.0):7-8 の `from config import Config` /
  `from models.data.user import User, UnauthorizedAccessError, UserNotFoundError`(レイヤ逆転)は v2.0.0 で消滅。
  L-1 の `configure_flask_helpers()` / `make_session_helper()` 注入に置換された。auth 側は main.py で config 値を、
  app_session.py で User 取得ロジックと例外を注入する形に配線替えした。
- `web-server/libcommon/web/session.py`(v2.0.0)/ `RedisSessionInterface.__init__(host, port, db, expiration_time_sec, prefix)` /
  `Session.configure(host, port, db)`。pre-v2.0.0 の `RedisSessionInterface(prefix)`(host/port/db を内部で Config 参照)から
  署名が変わり、main.py の初期化を新署名へ機械置換した。
- `tests/golden/smoke_routes.json` / pre-v2.0.0 で凍結した golden に v2.0.0 追随後のアプリが**一致**(21 passed)。
  L-1 注入 API への配線替えは観測可能な挙動を変えない(成果物不変)ことの実測。smoke は `authorize`(Session.user_id
  経由で Session.configure を、language_wrapper 経由で configure_flask_helpers を)を駆動しており、import だけでなく
  実行経路で注入が効いていることを兼ねて確認している。
- 環境 / `web-server/libcommon/{ruff.toml,pyrightconfig.json}` は vendored libcommon 自身の lint 設定であり auth の
  ゲートではない。auth のゲートは `python3 -m pytest -q tests`(規約ゲート test_conventions.py を含む)の1本。
