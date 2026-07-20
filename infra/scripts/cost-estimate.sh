#!/usr/bin/env bash
# ============================================================
# infra/scripts/cost-estimate.sh
#   このリポジトリ(infra/terraform)が構築する AWS インフラの月額概算。
#   ネットワーク不要・AWS 認証不要(静的な料金表 + terraform 構成の写経)。
#
#   料金スナップショット: region=ap-northeast-1(東京) / Linux / on-demand
#                         取得時点 2026-07。★料金は変動する。定期的に更新すること★
#
#   使い方:
#     infra/scripts/cost-estimate.sh [prod|staging]      # 既定 staging
#     JPY_RATE=160 infra/scripts/cost-estimate.sh prod   # 円レート上書き(既定 162)
#
#   ★terraform の instance_type / volume_size / EIP を変えたら、
#    下の「構成」ブロックも合わせて更新すること(唯一の同期ポイント)。
# ============================================================
set -euo pipefail

ENVX="${1:-staging}"
HRS_MONTH=730             # 1 ヶ月の標準時間(24/7)

# --- 静的料金表(東京・on-demand・USD) -----------------------
P_T3_MICRO=0.0136         # t3.micro  /h
P_T3_SMALL=0.0272         # t3.small  /h
P_T3_MEDIUM=0.0544        # t3.medium /h
P_GP3_GB=0.096            # EBS gp3 ストレージ /GB-月
P_IPV4_HR=0.005           # パブリック IPv4 /h(2024-02 以降 使用中でも課金。EIP も同額)
P_XFER_GB=0.114           # データ転送(送信)超過分 /GB。最初 100GB/月 無料
P_R53_ZONE=0.50           # Route53 hosted zone /月(private zone supercom.internal。クエリは $0.40/100万で無視)

# --- 構成(terraform/instances.tf + variables.tf を写経) -----
case "$ENVX" in
  prod)
    WEB_TYPE=t3.small;  WEB_PRICE=$P_T3_SMALL;  WEB_DISK=50
    LB_TYPE=t3.micro;   LB_PRICE=$P_T3_MICRO;   LB_DISK=20
    PUBLIC_IPV4=2       # web(EIP) + lb(EIP)
    ;;
  staging)
    WEB_TYPE=t3.medium; WEB_PRICE=$P_T3_MEDIUM; WEB_DISK=20   # 開発箱(D-57)= RAM 余裕
    LB_TYPE=t3.micro;   LB_PRICE=$P_T3_MICRO;   LB_DISK=20
    PUBLIC_IPV4=2       # web(EIP) + lb(EIP)。EIP は台帳(D-53)が保持=停止中も課金
    ;;
  *)
    echo "usage: cost-estimate.sh [prod|staging]" >&2
    exit 2
    ;;
esac

calc() { awk "BEGIN{printf \"%.2f\", $1}"; }
comma() { printf "%.0f" "$1" | awk '{x=$0;r="";while(length(x)>3){r=","substr(x,length(x)-2)r;x=substr(x,1,length(x)-3)}print x r}'; }

JPY_RATE="${JPY_RATE:-162}"

# 標準稼働率: staging は開発箱でこまめ停止する前提で 60% を内訳の基準に。prod は 24/7 = 100%
if [ "$ENVX" = staging ]; then STD_UTIL=60; else STD_UTIL=100; fi

WEB_COMPUTE=$(calc "$WEB_PRICE * $HRS_MONTH * $STD_UTIL / 100")
LB_COMPUTE=$(calc "$LB_PRICE * $HRS_MONTH * $STD_UTIL / 100")
WEB_EBS=$(calc "$WEB_DISK * $P_GP3_GB")     # EBS は停止中も課金 → 満額
LB_EBS=$(calc "$LB_DISK * $P_GP3_GB")
IPV4=$(calc "$PUBLIC_IPV4 * $P_IPV4_HR * $HRS_MONTH")  # EIP は台帳(D-53)保持で停止中も満額
R53=$(calc "$P_R53_ZONE")

FIXED=$(calc "$WEB_EBS + $LB_EBS + $IPV4 + $R53")         # 稼働率と無関係の固定費
COMPUTE_100=$(calc "($WEB_PRICE + $LB_PRICE) * $HRS_MONTH")  # 24/7 稼働時の compute

echo "============================================================"
echo " ThinkX インフラ月額概算   env=${ENVX}"
echo " region=ap-northeast-1(東京) / Linux on-demand / 2026-07 snapshot"
echo " 内訳は稼働率 ${STD_UTIL}% 基準(compute のみ稼働率に比例。EBS/EIP/Route53 は固定)"
echo "============================================================"
printf "%-34s %-9s %10s\n" "サービス" "区分" "月額USD"
printf "%-34s %-9s %10s\n" "----------------------------------" "-------" "--------"
printf "%-34s %-9s %10s\n" "EC2 web  (${WEB_TYPE}, ${STD_UTIL}%)"  "compute" "$WEB_COMPUTE"
printf "%-34s %-9s %10s\n" "EC2 lb   (${LB_TYPE}, ${STD_UTIL}%)"   "compute" "$LB_COMPUTE"
printf "%-34s %-9s %10s\n" "EBS web  (gp3 ${WEB_DISK}GB)"        "storage" "$WEB_EBS"
printf "%-34s %-9s %10s\n" "EBS lb   (gp3 ${LB_DISK}GB)"         "storage" "$LB_EBS"
printf "%-34s %-9s %10s\n" "Public IPv4(EIP) x${PUBLIC_IPV4}"    "network" "$IPV4"
printf "%-34s %-9s %10s\n" "Route53 zone (supercom.internal)"   "network" "$R53"
printf "%-34s %-9s %10s\n" "データ転送(送信, 100GB無料枠内)"   "network" "0.00"
printf "%-34s %-9s %10s\n" "VPC/Subnet/IGW/RouteTable"          "network" "0.00"
printf "%-34s %-9s %10s\n" "----------------------------------" "-------" "--------"
if [ "$ENVX" = staging ]; then TIERS="10 30 60 100"; else TIERS="100"; fi
for P in $TIERS; do
  T=$(calc "$FIXED + $COMPUTE_100 * $P / 100")
  printf "%-34s %10s USD/月   %10s 円\n" "合計 (${ENVX} ${P}% 稼働)" "$T" "$(comma "$(calc "$T * $JPY_RATE")")"
done
echo "  (@ ${JPY_RATE}円/USD ・ 固定費 \$${FIXED} = EBS+EIP+Route53 は停止中も課金)"

cat <<'NOTE'

--- 注記 -------------------------------------
* staging は stop_staging.sh でこまめ停止する前提。止めると compute だけ減り、固定費は残る。
* 固定費(EBS+EIP+Route53)は停止中も課金。EIP は台帳(D-53)保持のため常に満額。
* terraform destroy まですれば EBS も消えて $0(EIP は台帳側に残る)。
* データ転送(送信)は最初 100GB/月 無料。超過は $0.114/GB(東京)。
* 料金は 2026-07 の on-demand スナップショット。実費は AWS 料金ページで要確認。
NOTE
