#!/usr/bin/env python3
"""Deploy key の配置と GitHub 認証を検証する。

setup 本体とは別の独立コマンドとして、setup の前に実行する(preflight)。
出力の最後の行が結果 ── OK: … か、登録すべき公開鍵。setup を止める分岐を
setup 内に持たせないための分離(exit も set -e も使わずに「メッセージが末尾」を実現)。

    (Mac) ssh supercom-web "tar xzf /tmp/secrets.tgz -C /tmp 2>/dev/null; python3 /tmp/check_deploykey.py <repo>"
    → OK なら setup を流す。NG なら表示された公開鍵を GitHub に登録して再実行。

戻り値: 0=OK / 1=NG(理由と対処は stderr)。

鍵の真実は Mac の infra/deploykeys/(.gitignore)。setup 前に tgz で /tmp へ配る:
    (Mac) tar czf /tmp/secrets.tgz -C infra certs deploykeys
          scp /tmp/secrets.tgz /tmp/check_deploykey.py ubuntu@<host>:/tmp/
    (script 冒頭) tar xzf /tmp/secrets.tgz -C /tmp
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RUN_USER = "kaz"
SSH_DIR = Path(f"/home/{RUN_USER}/.ssh")
STAGE = Path("/tmp/deploykeys")   # secrets.tgz(-C infra … deploykeys)を -C /tmp で展開した先


def sudo_u(cmd, **kw):
    # input= を渡すとき stdin は指定できない(併用不可)。渡さないときだけ stdin を塞ぐ
    if "input" not in kw:
        kw.setdefault("stdin", subprocess.DEVNULL)
    return subprocess.run(["sudo", "-u", RUN_USER, "-H"] + cmd,
                          capture_output=True, text=True, **kw)


def install_key(repo: str) -> Path | None:
    """staging から kaz の .ssh へ配置(上書き=冪等)。無ければ None。"""
    src = STAGE / f"deploy_{repo}"
    if not src.exists():
        return None
    dst = SSH_DIR / f"deploy_{repo}"
    subprocess.run(["sudo", "install", "-o", RUN_USER, "-g", RUN_USER,
                    "-m", "600", str(src), str(dst)], check=True)
    subprocess.run(["sudo", "install", "-o", RUN_USER, "-g", RUN_USER,
                    "-m", "644", f"{src}.pub", f"{dst}.pub"], check=True)
    return dst


def write_alias(repo: str, key: Path) -> None:
    """config.d/github-<repo> を上書き(冪等)。親 config の Include を保証。"""
    sudo_u(["mkdir", "-p", str(SSH_DIR / "config.d")])
    entry = (f"Host github-{repo}\n    HostName github.com\n"
             f"    User git\n    IdentityFile {key}\n    IdentitiesOnly yes\n")
    sudo_u(["tee", str(SSH_DIR / f"config.d/github-{repo}")], input=entry)
    config = SSH_DIR / "config"
    head = sudo_u(["cat", str(config)]).stdout
    if "Include config.d/*" not in head:
        sudo_u(["tee", str(config)], input=f"Include config.d/*\n{head}")


def auth_ok(repo: str) -> bool:
    p = sudo_u(["ssh", "-T", "-o", "StrictHostKeyChecking=accept-new",
                "-o", "ConnectTimeout=10", f"git@github-{repo}"])
    return "successfully authenticated" in (p.stdout + p.stderr)


def main() -> int:
    repo = sys.argv[1]
    key = install_key(repo)
    if key is None:
        print(f"""!! deploy_{repo} が /tmp/deploykeys/ にない。Mac 側で:
   ssh-keygen -t ed25519 -N '' -C 'supercom:{RUN_USER}:{repo}' \\
     -f infra/deploykeys/deploy_{repo}
   → .pub を GitHub > {repo} > Deploy keys に登録(初回のみ)
   → tar czf /tmp/secrets.tgz -C infra certs deploykeys && scp して再実行
""", file=sys.stderr)
        return 1
    write_alias(repo, key)
    if auth_ok(repo):
        print(f"OK: github-{repo} authenticated")
        return 0
    pub = sudo_u(["cat", f"{key}.pub"]).stdout.strip()
    print(f"""!! 鍵は配置済みだが GitHub 認証に失敗: ThinkXInc/{repo}
   Deploy keys に以下が登録されているか確認(Allow write access 外す):

{pub}
""", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
