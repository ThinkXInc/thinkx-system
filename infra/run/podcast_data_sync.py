#!/usr/bin/env python3
"""podcast 編集データの保存トリガー同期(D-52)。systemd timer が60秒ごとに呼ぶ。

編集サイト(main.py)は保存のたびに「実際に書いたファイルのパス」を
/src/thinkx-system/podcast/data/.pending_sync.jsonl に追記する。
このスクリプトはそのキューだけを見て、載っているファイルのみを
git add → commit → push する。ディレクトリ単位の add はしない。

手で消した・動かしたファイルはキューに載らないので push されない。
その場合ツリーは dirty のまま残り、deploy timer が止まって通知する
(既存の安全装置がそのまま事故検知器になる)。

flush する条件(どちらか):
  - 最後の保存から 120 秒以上静止した
  - 最古の未 push が 600 秒を超えた(編集し続けても最終状態が定期的に出る)

push 先は今いるブランチ(staging=develop / prod=production)。
rebase や push に失敗したらキューを残したまま終了し、次の tick で再試行する。

前提: root で動く。git は必ず kaz として実行する(sync_from_origin.sh と同じ理由)。
"""
import os
import sys
import json
import datetime
import subprocess

REPO = "/src/thinkx-system"
DATA = os.path.join(REPO, "podcast", "data")
QUEUE = os.path.join(DATA, ".pending_sync.jsonl")
PROCESSING = QUEUE + ".processing"
QUIET_SEC = 120
FORCE_SEC = 600


def g(*args, check=True, capture=False):
    return subprocess.run(["sudo", "-H", "-u", "kaz", "git", "-C", REPO, *args],
                          check=check, capture_output=capture, text=True)


def load_entries(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for ln in f:
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return out


def parse_at(entry):
    try:
        return datetime.datetime.fromisoformat(entry.get("at", ""))
    except ValueError:
        return None


def push_leftover(branch):
    """前回 push に失敗して残ったコミットがあれば先に押し出す。"""
    ahead = subprocess.run(["sudo", "-H", "-u", "kaz", "git", "-C", REPO,
                            "rev-list", "--count", "@{u}..HEAD"],
                           capture_output=True, text=True)
    if ahead.returncode != 0 or int(ahead.stdout.strip() or 0) == 0:
        return
    try:
        g("pull", "--rebase", "origin", branch)
        g("push", "origin", branch)
        print("[podcast-sync] 前回の未 push コミットを押し出した")
    except subprocess.CalledProcessError:
        g("rebase", "--abort", check=False)
        print("[podcast-sync] 未 push コミットの押し出しに失敗。次の tick で再試行する",
              file=sys.stderr)


def main():
    branch = g("symbolic-ref", "--short", "HEAD", capture=True).stdout.strip()
    push_leftover(branch)

    # 前回失敗して残った processing があれば、それを今回の対象にする
    entries = load_entries(PROCESSING)
    if not entries:
        fresh = load_entries(QUEUE)
        if not fresh:
            return 0
        stamps = [t for t in (parse_at(e) for e in fresh) if t]
        if stamps:
            now = datetime.datetime.now()
            quiet = (now - max(stamps)).total_seconds()
            age = (now - min(stamps)).total_seconds()
            if quiet < QUIET_SEC and age < FORCE_SEC:
                return 0  # まだ編集中。次の tick で見る
        # キューを processing へ移す(アプリは新しいキューへ追記を続けられる)
        os.replace(QUEUE, PROCESSING)
        entries = load_entries(PROCESSING)

    paths, ids = [], []
    for e in entries:
        p = os.path.realpath(e.get("path") or "")
        if not p.startswith(DATA + os.sep) or not os.path.isfile(p):
            continue  # data の外・消えたファイルは対象にしない
        if p not in paths:
            paths.append(p)
            idv = os.path.relpath(p, DATA).split(os.sep)[0]
            if idv not in ids:
                ids.append(idv)
    if not paths:
        os.unlink(PROCESSING)
        return 0

    g("add", "--", *paths)
    staged = subprocess.run(["sudo", "-H", "-u", "kaz", "git", "-C", REPO,
                             "diff", "--cached", "--quiet"]).returncode
    if staged == 0:
        os.unlink(PROCESSING)  # 内容に差分なし(同じ状態を保存し直しただけ)
        return 0

    host = os.uname().nodename
    g("commit", "-m", f"data(podcast): edit保存 {' '.join(ids)} @{host}")
    try:
        g("pull", "--rebase", "origin", branch)
    except subprocess.CalledProcessError:
        g("rebase", "--abort", check=False)
        print(f"[podcast-sync] rebase が衝突。コミット済みのまま次の tick で再試行する", file=sys.stderr)
        os.unlink(PROCESSING)  # commit 済みなのでキューの役目は終わり
        return 1
    try:
        g("push", "origin", branch)
    except subprocess.CalledProcessError:
        print(f"[podcast-sync] push に失敗。次の tick で再試行する", file=sys.stderr)
        os.unlink(PROCESSING)  # commit 済み。push は次回 rebase なしで再試行される
        return 1

    os.unlink(PROCESSING)
    print(f"[podcast-sync] {len(paths)} ファイル({' '.join(ids)})を {branch} へ push した")
    return 0


if __name__ == "__main__":
    sys.exit(main())
