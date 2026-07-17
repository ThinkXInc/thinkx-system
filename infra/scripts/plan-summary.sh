#!/usr/bin/env bash
# ============================================================
# infra/scripts/plan-summary.sh   【分類: 観測系(見るだけ・状態を変えない)】
#   terraform plan から:
#     - 構成図 = 模範 runbooks/diagram.md を env 置換して表示。
#       ★変更のあるリソースの行だけ色づけ(+追加=緑 / ~変更=黄 / -削除=赤)。
#       変更なしは普通に表示(色なし)。
#     - 月額概算(cost-estimate.sh)
#   変更検出 = terraform plan(config と実 state の差)。git 差分ではない。
#
#   使い方: infra/scripts/plan-summary.sh [prod|staging]   # 既定 staging
#
#   bash.md 観測系準拠: set -e/-u/pipefail・exit 不使用/関数+return/cd はサブシェルに閉じる/
#     依存は `|| return`/スクリプトパスは ${BASH_SOURCE[0]:-$0}。
# ============================================================

plan_summary() {
  local envx="${1:-staging}"
  local here tfdir plan json diagram
  here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
  tfdir="$here/../terraform"

  command -v terraform >/dev/null 2>&1 || { echo "terraform が見つからない" >&2; return 0; }
  command -v python3   >/dev/null 2>&1 || { echo "python3 が見つからない"   >&2; return 0; }

  plan="$(mktemp)"
  json="$(mktemp)"
  local err lockinfo
  err="$(mktemp)"
  lockinfo="$tfdir/.terraform.tfstate.lock.info"

  # 実行前: 別の terraform が state ロックを握っていれば、その持ち主を先に見せる
  # (ローカル backend はロック中だけ .terraform.tfstate.lock.info を置く)。
  if [ -f "$lockinfo" ]; then
    echo "── state ロック中(別の terraform が実行中)───────────────────" >&2
    python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print("\n".join(f"  {k}: {d.get(k)}" for k in ("Who","Operation","ID","Created")))' "$lockinfo" 2>/dev/null \
      || sed 's/^/  /' "$lockinfo" >&2
    echo "  → その端末で Ctrl-C。残るなら: terraform -chdir=$tfdir force-unlock <上の ID>" >&2
    echo "────────────────────────────────────────────────────────────" >&2
  fi

  # -input=false: 未設定の必須変数(my_office_ip 等)で対話プロンプトに固まらせない。
  # -lock-timeout=10s: ロック中でも無限待ちせず 10 秒で諦めて理由を出す(観測系はハングさせない)。
  # 値は terraform.tfvars(自動読込・gitignore 済み)から取る想定。env だけ実行ごとに渡す。
  if ! terraform -chdir="$tfdir" plan -input=false -lock-timeout=10s \
        -var="env=$envx" -out="$plan" >/dev/null 2>"$err"; then
    echo "── terraform plan 失敗。以下が理由 ───────────────────────────" >&2
    if grep -qi "state lock" "$err"; then
      echo "★ state ロックを別プロセスが保持(上/下の Who・Operation が持ち主)。Ctrl-C か force-unlock。" >&2
    fi
    if grep -qiE "my_office_ip|No value for required variable" "$err"; then
      echo "★ 必須変数が未設定。terraform.tfvars 未作成の可能性:" >&2
      echo "    cd $tfdir && cp terraform.tfvars.example terraform.tfvars  # IP を埋める" >&2
    fi
    echo "── terraform の生エラー ─────────────────────────────────────" >&2
    sed 's/^/  /' "$err" >&2
    rm -f "$plan" "$json" "$err"
    return 0
  fi
  rm -f "$err"
  terraform -chdir="$tfdir" show -json "$plan" > "$json" 2>/dev/null || true

  diagram="$here/../runbooks/diagram.md"

  # 図(模範)を env 置換し、変更のあるリソース行だけ色づけして表示
  python3 - "$json" "$envx" "$diagram" <<'PY' 2>/dev/null || true
import json, sys
data = json.load(open(sys.argv[1]))
envx  = sys.argv[2] if len(sys.argv) > 2 else "staging"
dpath = sys.argv[3] if len(sys.argv) > 3 else ""
G="\033[32m"; Y="\033[33m"; R="\033[31m"; Z="\033[0m"

act = {rc["address"]: rc["change"]["actions"] for rc in data.get("resource_changes", [])}
def col(addr):
    a = act.get(addr)
    if a == ["create"]:                            return G
    if a == ["update"]:                            return Y
    if a == ["delete"] or (a and set(a) == {"create", "delete"}): return R
    return None

# 先頭サマリ(1行)
def cnt(pred): return sum(1 for a in act.values() if pred(a))
add  = cnt(lambda a: a == ["create"])
upd  = cnt(lambda a: a == ["update"])
dele = cnt(lambda a: a == ["delete"] or set(a) == {"create", "delete"})
if add or upd or dele:
    print(f"変更: {G}+{add} 追加{Z}  {Y}~{upd} 変更{Z}  {R}-{dele} 削除{Z}   (下図の該当リソースを色表示。図に無いものは下記のみ)")
    for addr in sorted(act):
        a = act[addr]
        if a == ["create"]:
            print(f"  {G}+ {addr}{Z}")
        elif a == ["update"]:
            print(f"  {Y}~ {addr}{Z}")
        elif a == ["delete"] or set(a) == {"create", "delete"}:
            print(f"  {R}- {addr}{Z}")
else:
    print("変更なし")

# 図: env 置換 + 変更リソースの行を着色(distinctive な名前で対応付け・具体的な順に)
p = "supercom-" + envx
octet = "1" if envx == "prod" else "2"
MAP = [
    (p + "-lb-sg",  "aws_security_group.lb"),
    (p + "-web-sg", "aws_security_group.web"),
    (p + "-igw",    "aws_internet_gateway.igw"),
    (p + "-rt",     "aws_route_table.public"),
    (p + "-lan",    "aws_subnet.lan"),
    (p + "-lb",     "aws_instance.lb"),
    (p + "-web",    "aws_instance.web"),
    ("aws_eip",     "aws_eip.lb[0]"),
]
try:
    fh = open(dpath, encoding="utf-8")
except OSError:
    fh = None
if fh:
    current = None   # 直近に入った(色付き)リソースの色。次のリソースまでブロック全体に及ぶ
    for raw in fh:
        line = raw.rstrip("\n")
        if line.startswith("```"):
            continue
        line = line.replace("{env}", envx).replace("{1|2}", octet)
        matched = False
        for sub, addr in MAP:
            if sub in line:
                current = col(addr)   # no-op/不在なら None(=以降は無色に戻る)
                matched = True
                break
        if not matched and ("Name: supercom-" + envx) in line:  # VPC 行(サフィックス無し)
            current = col("aws_vpc.main")
        print(f"{current}{line}{Z}" if current else line)
        # VPC 最外箱の閉じ(行頭 └)以降は resource でない(SES/Route53/表/月額)→ 無色に戻す
        if line[:1] == "└":  # └
            current = None
    fh.close()
PY

  rm -f "$plan" "$json"

  # 料金
  "$here/cost-estimate.sh" "$envx" 2>/dev/null || true
}

plan_summary "$@"
