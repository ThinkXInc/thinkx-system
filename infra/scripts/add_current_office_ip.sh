#!/usr/bin/env bash
# thinkx-system/infra/scripts/add_current_office_ip.sh   【分類: 変更系(SG と tfvars を書き換える)】
#
# ルーターの動的 IP が変わって SSH(22) が締め出されたとき、現在の IP を許可し直す。
#   - prod: terraform.tfvars の my_office_ip を書き換え → terraform apply(承認プロンプトで yes)
#   - staging: SG の 22 番ルールを aws CLI で入れ替え(state は旧 infra リポジトリ管轄のため直接)
#
#   使い方: bash infra/scripts/add_current_office_ip.sh

set -euo pipefail

G=$'\033[32m' Y=$'\033[33m' R=$'\033[31m' Z=$'\033[0m'
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
TF="$HERE/../terraform"

IP="$(curl -s --max-time 10 https://checkip.amazonaws.com)"
[ -n "$IP" ] || { printf '%b\n' "${R}FAIL: add_current_office_ip 現在の IP を取得できない${Z}"; exit 1; }
printf '現在の IP: %s\n' "$IP"

# prod: tfvars のリストに現在 IP を追記して terraform apply(SG は in-place 更新)
# (旧単数形 my_office_ip が残っていればリスト形式へ自動移行)
sed -i.bak 's|^my_office_ip = "\(.*\)"|my_office_ips = ["\1"]|' "$TF/terraform.tfvars"
if grep -q "\"$IP/32\"" "$TF/terraform.tfvars"; then
  :
else
  sed -i.bak "/^my_office_ips/s|\]|, \"$IP/32\"]|" "$TF/terraform.tfvars"
  printf '# %s を追加 %s\n' "$IP/32" "$(date +%F)" >> "$TF/terraform.tfvars"
fi

# 知りたいことは1つ「この IP はどの SG で SSH を許可されているか」。
# それを ✓/✗ の一覧で先に見せ、✗ の分だけが追加される、と1行で言い切る。
# tfvars にあっても前回の apply が完走していなければ SG は ✗ のまま(手元の設定と
# AWS の実態は別物)なので、判定は必ず AWS 側(describe-security-groups)で行う。
sg_ssh_cidrs() {
  aws ec2 describe-security-groups --filters "Name=group-name,Values=$1" \
    --query "SecurityGroups[0].IpPermissions[?ToPort==\`22\`].IpRanges[].CidrIp" \
    --output text 2>/dev/null | tr '\t' '\n' | grep -v '^None$' | LC_ALL=C sort || true
}

echo
printf 'この IP(%s)から SSH できるか:\n' "$IP"
PROD_DELTA=0
for sg in supercom-prod-web-sg supercom-prod-lb-sg supercom-staging-web-sg supercom-staging-lb-sg; do
  if sg_ssh_cidrs "$sg" | grep -q "^$IP/32$"; then
    printf '  %b✓ 許可済み%b  %s\n' "$G" "$Z" "$sg"
  else
    printf '  %b✗ 未許可%b    %s → これから追加する\n' "$R" "$Z" "$sg"
    case "$sg" in supercom-prod-*) PROD_DELTA=1 ;; esac
  fi
done
echo '  (既存の許可 IP は消さない。追加だけ)'

# 例外(削除)が起きるときだけ注意を出す: prod の SG は terraform が tfvars の
# リストに揃えるため、tfvars から消した IP は SG からも消える。通常は出ない。
DESIRED="$(grep '^my_office_ips' "$TF/terraform.tfvars" | grep -o '[0-9][0-9.]*/32' | LC_ALL=C sort)"
for sg in supercom-prod-web-sg supercom-prod-lb-sg; do
  DEL="$(comm -13 <(printf '%s\n' "$DESIRED") <(sg_ssh_cidrs "$sg") | tr '\n' ' ')"
  if [ -n "${DEL// /}" ]; then
    PROD_DELTA=1
    printf '  %b注意%b: %s からは %sが削除される(tfvars に無いため)\n' "$Y" "$Z" "$sg" "$DEL"
  fi
done

# apply は SG のみに限定(-target)+人間の yes 必須。
# 2026-08-06 の事故: -auto-approve の全体 apply が AMI 追従の「インスタンス要再作成」
# 差分を巻き込み、prod/staging の全4台を破壊再作成した。IP 追加で触ってよいのは
# SG だけであり、それ以外の差分をこのスクリプトから適用してはならない。
#
# terraform の生の plan は SG ルールをセット丸ごと -旧/+新 で出すため、どこが変わるのか
# 読めない(2026-10-16 オーナー指摘)。plan をファイルに保存して JSON から人間語の差分に
# 要約し、yes ならその保存した plan をそのまま適用する。見せた内容と適用される内容が
# 同一であることは plan ファイルが保証する。承認は terraform のプロンプトではなく
# このスクリプト自身の yes/no で取る。
if [ "$PROD_DELTA" -eq 0 ]; then
  echo
  echo 'prod の SG は変更不要。terraform は実行しない'
else
  for E in prod staging; do
    [ -f "$TF/envs/$E/terraform.tfstate" ] || continue
    PLANF="$(mktemp)"; PLANJ="$(mktemp)"
    terraform -chdir="$TF/envs/$E" plan -input=false \
      -target=aws_security_group.web -target=aws_security_group.lb \
      -out="$PLANF" > /dev/null
    terraform -chdir="$TF/envs/$E" show -json "$PLANF" > "$PLANJ"
    echo
    printf '==== これから適用される変更 %s ====\n' "$E"
    SUMRC=0
    python3 - "$PLANJ" <<'PY' || SUMRC=$?
import json, sys

def ports(r):
    if r.get("protocol") in ("-1", None):
        return "全ポート"
    f, t = r.get("from_port"), r.get("to_port")
    return f"ポート{f}" if f == t else f"ポート{f}-{t}"

def key(r):
    return (r.get("protocol"), r.get("from_port"), r.get("to_port"))

def diff_rules(before, after, label, out):
    bmap, amap = {}, {}
    for r in before or []:
        bmap.setdefault(key(r), r)
    for r in after or []:
        amap.setdefault(key(r), r)
    for k, ar in amap.items():
        br = bmap.get(k)
        if br is None:
            continue
        for field, word in (("cidr_blocks", "IP"), ("security_groups", "SG")):
            add = sorted(set(ar.get(field) or []) - set(br.get(field) or []))
            dele = sorted(set(br.get(field) or []) - set(ar.get(field) or []))
            if add:
                out.append(f"  {label}{ports(ar)}: 許可{word}に追加 {' '.join(add)}")
            if dele:
                out.append(f"  {label}{ports(ar)}: 許可{word}から削除 {' '.join(dele)}")
    bonly = [r for k, r in bmap.items() if k not in amap]
    aonly = [r for k, r in amap.items() if k not in bmap]
    for ar in list(aonly):
        m = [br for br in bonly if (br.get("description") or "") == (ar.get("description") or "")]
        if m:
            br = m[0]
            bonly.remove(br)
            aonly.remove(ar)
            d = ar.get("description") or ""
            out.append(f"  {label}{ports(br)} → {ports(ar)} に変更" + (f": {d}" if d else ""))
    for ar in aonly:
        allow = " ".join((ar.get("cidr_blocks") or []) + (ar.get("security_groups") or []))
        out.append(f"  {label}ルール追加: {ports(ar)} 許可 {allow}")
    for br in bonly:
        out.append(f"  {label}ルール削除: {ports(br)}")

d = json.load(open(sys.argv[1]))
changed = 0
for rc in d.get("resource_changes", []):
    ch = rc.get("change") or {}
    actions = set(ch.get("actions") or [])
    if actions & {"create", "delete"}:
        changed += 1
        print(f"  注意: {rc.get('address')} の作成/削除が含まれる。想定外なので no で止めて調べること")
        continue
    if "update" not in actions:
        continue
    before, after = ch.get("before") or {}, ch.get("after") or {}
    name = ((after.get("tags") or {}).get("Name")) or after.get("name") or rc.get("address")
    out = []
    diff_rules(before.get("ingress"), after.get("ingress"), "", out)
    diff_rules(before.get("egress"), after.get("egress"), "外向き ", out)
    if out:
        changed += 1
        print(f"{name}:")
        print("\n".join(out))
sys.exit(3 if changed else 0)
PY
    if [ "$SUMRC" -eq 0 ]; then
      echo '変更なし'
      rm -f "$PLANF" "$PLANJ"
      continue
    elif [ "$SUMRC" -ne 3 ]; then
      echo '要約に失敗したので terraform の生の差分を出す:'
      terraform -chdir="$TF/envs/$E" show "$PLANF"
    fi
    printf 'この変更を適用するか (yes/no): '
    read -r ANS
    if [ "$ANS" = "yes" ]; then
      terraform -chdir="$TF/envs/$E" apply "$PLANF"
    else
      echo '適用しない。何も変わっていない'
    fi
    rm -f "$PLANF" "$PLANJ"
  done
fi

# staging: SG の 22 番に現在 IP を追加(既存の許可は残す)
for sg in supercom-staging-web-sg supercom-staging-lb-sg; do
  gid="$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$sg" --query "SecurityGroups[0].GroupId" --output text)"
  if sg_ssh_cidrs "$sg" | grep -q "^$IP/32$"; then
    printf '%s: %s/32 は既に許可済み(変更なし)\n' "$sg" "$IP"
  else
    aws ec2 authorize-security-group-ingress --group-id "$gid" --protocol tcp --port 22 --cidr "$IP/32" > /dev/null
    printf '%s: %s/32 を追加した\n' "$sg" "$IP"
  fi
done

# インスタンスを作り直すとホスト鍵が変わり(2026-08-06 の全損復旧で実際に変わった)、
# known_hosts が古いままだと SG を直しても ssh は繋がらない。人間に ssh-keygen -R を
# 手打ちさせると、このスクリプトの verify が「NG」を出したまま原因が SG に見える。
# 鍵の不一致に当たったときだけ古い鍵を捨てて張り直す(毎回捨てると成りすましも黙って通る)。
reach_host() {
  local h="$1" out
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 "$h" true 2>/dev/null && return 0
  out="$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$h" true 2>&1 || true)"
  case "$out" in
    *"REMOTE HOST IDENTIFICATION HAS CHANGED"*|*"Host key verification failed"*) ;;
    *) return 1 ;;
  esac
  printf '%b\n' "${Y}$h: ホスト鍵が変わっている。作り直した覚えが無ければ止めて調べること${Z}"
  ssh-keygen -R "$h" >/dev/null 2>&1 || true
  ssh-keygen -R "$(ssh -G "$h" 2>/dev/null | awk '/^hostname /{print $2}')" >/dev/null 2>&1 || true
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 "$h" true 2>/dev/null
}

# verify(4台へ SSH 到達確認。末尾に色で成否)
fail=0
for h in supercom-web1 supercom-lb1 supercom-web1-stg supercom-lb1-stg; do
  if reach_host "$h"; then
    printf '%b\n' "${G}ok  $h${Z}"
  else
    printf '%b\n' "${R}NG  $h${Z}"; fail=$((fail+1))
  fi
done
if [ "$fail" -eq 0 ]; then
  printf '%b\n' "${G}OK: add_current_office_ip 4台とも SSH 到達($IP/32)${Z}"
else
  printf '%b\n' "${R}FAIL: add_current_office_ip SSH 不達 $fail 台${Z}"
  exit 1
fi
