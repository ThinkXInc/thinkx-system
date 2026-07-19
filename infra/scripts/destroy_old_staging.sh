#!/usr/bin/env bash
# thinkx-system/infra/scripts/destroy_old_staging.sh   【分類: 変更系(破壊・オーナー実行専用・一回きり)】
#
# 旧 staging(terraform state を失った supercom-staging VPC 一式)を aws CLI で撤去する。
#   背景: 旧 infra リポジトリのこの Mac 上の clone に tfstate が無く、terraform destroy 不可(2026-07-19)。
#   D-51 の「destroy 先行 → monorepo terraform(workspace staging)で新規作成」の destroy 側を担う。
#   撤去対象を全件表示 → yes 入力までは何も変更しない。
#   注: supercom.internal の private hosted zone は IAM 権限の都合でここでは消せない。
#       残っても新 staging とは競合しない(課金 $0.50/月のみ)。掃除は Route53 コンソールで任意。
#
#   使い方: bash infra/scripts/destroy_old_staging.sh

set -euo pipefail

destroy_old_staging() {
  local G=$'\033[32m' R=$'\033[31m' Y=$'\033[33m' Z=$'\033[0m'
  local vpc ids eips sgs subnets igw rts ans

  vpc="$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=supercom-staging" --query "Vpcs[0].VpcId" --output text)"
  [ "$vpc" != "None" ] && [ -n "$vpc" ] || { printf '%b\n' "${R}FAIL: destroy_old_staging supercom-staging VPC が見つからない(撤去済み?)${Z}"; return 1; }

  ids="$(aws ec2 describe-instances --filters "Name=vpc-id,Values=$vpc" "Name=instance-state-name,Values=running,stopped" --query "Reservations[].Instances[].InstanceId" --output text)"
  eips="$(aws ec2 describe-addresses --filters "Name=tag:Name,Values=supercom-staging-eip-web,supercom-staging-eip-lb" --query "Addresses[].AllocationId" --output text)"
  sgs="$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$vpc" --query "SecurityGroups[?GroupName!='default'].GroupId" --output text)"
  subnets="$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$vpc" --query "Subnets[].SubnetId" --output text)"
  igw="$(aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$vpc" --query "InternetGateways[].InternetGatewayId" --output text)"
  rts="$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$vpc" --query "RouteTables[?Associations[0].Main!=\`true\`].RouteTableId" --output text)"

  echo "── 撤去対象(supercom-staging / $vpc)──"
  echo "instances : $ids"
  echo "EIPs      : $eips ($(aws ec2 describe-addresses --allocation-ids $eips --query "Addresses[].PublicIp" --output text 2>/dev/null))"
  echo "SGs       : $sgs"
  echo "subnets   : $subnets"
  echo "IGW       : $igw"
  echo "routetbls : $rts"
  echo "IAM       : role/instance-profile supercom-staging-lb"
  echo

  printf '%b' "${Y}上記を全て削除する? [yes/N] ${Z}"
  read -r ans
  [ "$ans" = yes ] || { echo "中止(何も変更していない)"; return 1; }

  echo "== instances terminate =="
  aws ec2 terminate-instances --instance-ids $ids --query "TerminatingInstances[].[InstanceId,CurrentState.Name]" --output text
  aws ec2 wait instance-terminated --instance-ids $ids
  echo "terminated"

  echo "== EIP release =="
  local a; for a in $eips; do aws ec2 release-address --allocation-id "$a" && echo "released $a"; done

  echo "== SG / subnet / IGW / route table / VPC 削除 =="
  # SG は相互参照(web-sg が lb-sg を許可元に持つ)で削除順依存があるため 2 パスで消す(2026-07-19 実測)
  local s pass
  for pass in 1 2; do for s in $sgs; do aws ec2 delete-security-group --group-id "$s" 2>/dev/null && echo "deleted $s" || true; done; done
  for s in $subnets; do aws ec2 delete-subnet --subnet-id "$s" && echo "deleted $s"; done
  for s in $igw; do aws ec2 detach-internet-gateway --internet-gateway-id "$s" --vpc-id "$vpc"; aws ec2 delete-internet-gateway --internet-gateway-id "$s" && echo "deleted $s"; done
  for s in $rts; do aws ec2 delete-route-table --route-table-id "$s" && echo "deleted $s"; done
  aws ec2 delete-vpc --vpc-id "$vpc" && echo "deleted $vpc"

  echo "== IAM(supercom-staging-lb)削除 =="
  aws iam remove-role-from-instance-profile --instance-profile-name supercom-staging-lb --role-name supercom-staging-lb
  aws iam delete-instance-profile --instance-profile-name supercom-staging-lb
  aws iam delete-role-policy --role-name supercom-staging-lb --policy-name certbot-dns-route53
  aws iam delete-role --role-name supercom-staging-lb

  # verify
  aws ec2 describe-vpcs --vpc-ids "$vpc" > /dev/null 2>&1 \
    && printf '%b\n' "${R}FAIL: destroy_old_staging VPC $vpc がまだ存在する${Z}" \
    || printf '%b\n' "${G}OK: destroy_old_staging 旧 staging 撤去完了(EIP 2 個解放・IAM 名 supercom-staging-lb 解放)${Z}"
}

destroy_old_staging "$@"
