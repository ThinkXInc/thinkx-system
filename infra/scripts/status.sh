#!/usr/bin/env bash
# 今立っているリソースと月額を表示する(見るだけ・非破壊)。
#   ./scripts/status.sh [staging|prod]  /  source しても安全(exit も set -e も使わない)

ENV="${1:-staging}"
REGION="ap-northeast-1"
RATE=162
EBS_GB_MONTH=0.096
HOURS=730
TF_DIR="$(dirname "${BASH_SOURCE[0]:-$0}")/../terraform"

# 時間単価(USD/h)。macOS の bash 3.2 には連想配列が無いので case で持つ
hourly() {
  case "$1" in
    t3.micro)  echo 0.0104 ;;
    t3.small)  echo 0.0208 ;;
    t3.medium) echo 0.0416 ;;
    t3.large)  echo 0.0832 ;;
    m7i.large) echo 0.1176 ;;
    *)         echo 0 ;;
  esac
}

printf -- "── supercom [%s] ─ %s ──\n\n" "$ENV" "$(date '+%Y-%m-%d %H:%M %Z')"

# ---- terraform(ローカル状態) ----
#if [ -d "$TF_DIR" ]; then
#  if (cd "$TF_DIR" && terraform fmt -check >/dev/null 2>&1); then
#    echo "  terraform fmt : OK"
#  else
#    echo "  terraform fmt : ⚠ 整形が崩れています(terraform fmt で修正)"
#  fi
#
#  STATE=$( (cd "$TF_DIR" && terraform state list) 2>/dev/null )
#  if [ -z "$STATE" ]; then
#    echo "  terraform state: 空(未作成)"
#  else
#    echo "  terraform state: $(echo "$STATE" | grep -c .) リソース"
#    echo "$STATE" | sed 's/^/                   /'
#  fi
#  echo
#fi

# ---- AWS(実物) ----
FILT=(--region "$REGION"
  --filters "Name=tag:Project,Values=supercom" "Name=tag:Env,Values=$ENV")
TOTAL=0

VPC=$(aws ec2 describe-vpcs "${FILT[@]}" --query 'Vpcs[0].CidrBlock' --output text 2>/dev/null)
[ -n "$VPC" ] && [ "$VPC" != "None" ] && printf "  %-12s %-34s \$%s/月\n" "VPC" "$VPC" "0.00"

aws ec2 describe-subnets "${FILT[@]}" --query 'Subnets[].CidrBlock' --output text 2>/dev/null \
| tr '\t' '\n' | while read -r c; do
    [ -n "$c" ] && printf "  %-12s %-34s \$%s/月\n" "Subnet" "$c" "0.00"
  done

aws ec2 describe-security-groups "${FILT[@]}" --query 'SecurityGroups[].GroupName' --output text 2>/dev/null \
| tr '\t' '\n' | while read -r n; do
    [ -n "$n" ] && printf "  %-12s %-34s \$%s/月\n" "SG" "$n" "0.00"
  done

aws ec2 describe-addresses "${FILT[@]}" --query 'Addresses[].[PublicIp,InstanceId]' --output text 2>/dev/null \
| while read -r ip inst; do
    [ -z "$ip" ] && continue
    if [ -z "$inst" ] || [ "$inst" = "None" ]; then
      printf "  %-12s %-34s \$%s/月  ← 未使用は課金\n" "EIP" "$ip (unattached)" "3.60"
    else
      printf "  %-12s %-34s \$%s/月\n" "EIP" "$ip (attached)" "0.00"
    fi
  done

# EC2 + EBS(合計を持ち回すのでプロセス置換で本体シェルに残す)
RUNNING=0
while read -r name type state vol; do
  [ -z "$name" ] && continue
  if [ "$state" = "running" ]; then
    COST=$(echo "$(hourly "$type") * $HOURS" | bc -l)
    RUNNING=1
  else
    COST=0
  fi
  printf "  %-12s %-10s %-18s %-8s \$%.2f/月\n" "EC2" "$type" "$name" "$state" "$COST"
  TOTAL=$(echo "$TOTAL + $COST" | bc -l)

  if [ -n "$vol" ] && [ "$vol" != "None" ]; then
    GB=$(aws ec2 describe-volumes --region "$REGION" --volume-ids "$vol" \
          --query 'Volumes[0].Size' --output text 2>/dev/null)
    EC=$(echo "${GB:-0} * $EBS_GB_MONTH" | bc -l)
    NOTE=""; [ "$state" != "running" ] && NOTE="  ← 停止中も課金"
    printf "  %-12s %-10s %-18s %-8s \$%.2f/月%s\n" "EBS gp3" "${GB}GB" "($name)" "" "$EC" "$NOTE"
    TOTAL=$(echo "$TOTAL + $EC" | bc -l)
  fi
done < <(aws ec2 describe-instances "${FILT[@]}" \
    --filters "Name=tag:Project,Values=supercom" "Name=tag:Env,Values=$ENV" \
              "Name=instance-state-name,Values=pending,running,stopping,stopped" \
    --query 'Reservations[].Instances[].[Tags[?Key==`Name`]|[0].Value,InstanceType,State.Name,BlockDeviceMappings[0].Ebs.VolumeId]' \
    --output text 2>/dev/null)

echo "  ──────────────────────────────────────────────"
printf "  %-12s %-34s \$%.2f/月  (≒ %.0f円)\n" "合計" "" "$TOTAL" "$(echo "$TOTAL * $RATE" | bc -l)"

if [ -d "$TF_DIR" ]; then
  LB=$( (cd "$TF_DIR" && terraform output -raw lb_public_ip)  2>/dev/null )
  WEB=$( (cd "$TF_DIR" && terraform output -raw web_public_ip) 2>/dev/null )
  [ -n "$LB" ] && { echo; echo "  LB  public : $LB"; echo "  web public : $WEB"; }
fi

[ "$RUNNING" = "0" ] && [ "$TOTAL" != "0" ] && \
  echo && echo "  ⚠ EC2 は停止中だが EBS 課金は継続。消すなら terraform destroy"