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

# apply は SG のみに限定(-target)+承認プロンプト必須。
# 2026-08-06 の事故: -auto-approve の全体 apply が AMI 追従の「インスタンス要再作成」
# 差分を巻き込み、prod/staging の全4台を破壊再作成した。IP 追加で触ってよいのは
# SG だけであり、それ以外の差分をこのスクリプトから適用してはならない。
# -input=false を付けない: 付けると terraform は承認を聞けず「承認されなかった」として
# apply を失敗させる(公式 docs)。差分があるときは必ず "Enter a value:" で yes を打つ。
# 期待する差分は env ごとに「0 to add, 2 to change, 0 to destroy」(web/lb の SG のみ・
# update in-place)。それ以外が出たら no で止める(何も変わらない)。
if [ "$PROD_DELTA" -eq 0 ]; then
  echo
  echo 'prod の SG は変更不要。terraform は実行しない'
else
  echo
  printf '%bこれから terraform を実行する。確認プロンプトが出たら、上の一覧どおり(追加だけ)なら yes。%b\n' "$Y" "$Z"
  for E in prod staging; do
    [ -f "$TF/envs/$E/terraform.tfstate" ] || continue
    terraform -chdir="$TF/envs/$E" apply \
      -target=aws_security_group.web -target=aws_security_group.lb
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
