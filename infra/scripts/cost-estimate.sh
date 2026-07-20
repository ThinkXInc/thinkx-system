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
#     HOURS=3 infra/scripts/cost-estimate.sh staging     # 実稼働 3h だけの想定
#     JPY_RATE=160 infra/scripts/cost-estimate.sh prod   # 円換算も表示
#
#   ★terraform の instance_type / volume_size / EIP を変えたら、
#    下の「構成」ブロックも合わせて更新すること(唯一の同期ポイント)。
# ============================================================
set -euo pipefail

ENVX="${1:-staging}"
HOURS="${HOURS:-730}"      # 稼働時間/月。既定 730h = 24/7。停止が長いなら実稼働 h を渡す
HRS_MONTH=730             # 1 ヶ月の標準時間

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
    echo "usage: cost-estimate.sh [prod|staging]   (HOURS=<稼働h> 省略時 730)" >&2
    exit 2
    ;;
esac

calc() { awk "BEGIN{printf \"%.2f\", $1}"; }

WEB_COMPUTE=$(calc "$WEB_PRICE * $HOURS")
LB_COMPUTE=$(calc "$LB_PRICE * $HOURS")
WEB_EBS=$(calc "$WEB_DISK * $P_GP3_GB")     # EBS は停止中も課金 → 満額(destroy まで残る)
LB_EBS=$(calc "$LB_DISK * $P_GP3_GB")
IPV4=$(calc "$PUBLIC_IPV4 * $P_IPV4_HR * $HRS_MONTH")  # EIP は台帳(D-53)保持で停止中も満額課金 → HOURS 非依存
XFER=0.00                                   # 標準的な静的サイトは 100GB/月 無料枠内と仮定
R53=$(calc "$P_R53_ZONE")                   # private zone は稼働時間と無関係に月額固定
TOTAL=$(calc "$WEB_COMPUTE + $LB_COMPUTE + $WEB_EBS + $LB_EBS + $IPV4 + $XFER + $R53")

# 稼働率と無関係に毎月かかる固定費(EBS + EIP + Route53)。段階見積もりの土台
FIXED=$(calc "$WEB_EBS + $LB_EBS + $IPV4 + $R53")
COMPUTE_100=$(calc "($WEB_PRICE + $LB_PRICE) * $HRS_MONTH")   # 24/7 稼働時の compute

if [ "$HOURS" = "$HRS_MONTH" ]; then USAGE="24/7"; else USAGE="停止考慮"; fi

echo "============================================================"
echo " ThinkX インフラ月額概算   env=${ENVX}   稼働=${HOURS}h/月 (${USAGE})"
echo " region=ap-northeast-1(東京) / Linux on-demand / 2026-07 snapshot"
echo "============================================================"
printf "%-34s %-9s %10s\n" "サービス" "区分" "月額USD"
printf "%-34s %-9s %10s\n" "----------------------------------" "-------" "--------"
printf "%-34s %-9s %10s\n" "EC2 web  (${WEB_TYPE}, ${HOURS}h)"  "compute" "$WEB_COMPUTE"
printf "%-34s %-9s %10s\n" "EC2 lb   (${LB_TYPE}, ${HOURS}h)"   "compute" "$LB_COMPUTE"
printf "%-34s %-9s %10s\n" "EBS web  (gp3 ${WEB_DISK}GB)"        "storage" "$WEB_EBS"
printf "%-34s %-9s %10s\n" "EBS lb   (gp3 ${LB_DISK}GB)"         "storage" "$LB_EBS"
printf "%-34s %-9s %10s\n" "Public IPv4(EIP) x${PUBLIC_IPV4} (${HOURS}h)" "network" "$IPV4"
printf "%-34s %-9s %10s\n" "Route53 zone (supercom.internal)"   "network" "$R53"
printf "%-34s %-9s %10s\n" "データ転送(送信, 100GB無料枠内)"   "network" "$XFER"
printf "%-34s %-9s %10s\n" "VPC/Subnet/IGW/RouteTable"          "network" "0.00"
printf "%-34s %-9s %10s\n" "----------------------------------" "-------" "--------"
printf "%-44s %10s USD/月\n" "合計" "$TOTAL"

if [ -n "${JPY_RATE:-}" ]; then
  printf "%-44s %10s JPY/月  (@ %s円/USD)\n" "合計(円換算)" "$(calc "$TOTAL * $JPY_RATE")" "$JPY_RATE"
fi

# --- 段階見積もり(稼働率別・停止で節約できるのは compute だけ) ---------
echo
echo "--- 稼働率別 月額(固定費 \$${FIXED} + compute×稼働率) ------------"
printf "%-8s %12s %12s %14s\n" "稼働率" "compute" "固定費" "合計USD/月"
printf "%-8s %12s %12s %14s\n" "------" "-------" "------" "----------"
for P in 10 30 60 100; do
  C=$(calc "$COMPUTE_100 * $P / 100")
  T=$(calc "$C + $FIXED")
  if [ -n "${JPY_RATE:-}" ]; then
    printf "%-7s%% %12s %12s %11s USD  (%s円)\n" "$P" "$C" "$FIXED" "$T" "$(calc "$T * $JPY_RATE")"
  else
    printf "%-7s%% %12s %12s %11s USD\n" "$P" "$C" "$FIXED" "$T"
  fi
done
echo "  ※固定費(EBS+EIP+Route53)は停止中も課金。EIP は台帳(D-53)保持のため常に満額"

cat <<'NOTE'

--- 標準的な使用の注記 -------------------------------------
* EBS は「停止中」でも課金される。HOURS を減らしても EBS は満額
  (ディスクは terraform destroy まで残るため)。
* staging はリハーサル(作成→試験→destroy)が標準運用。数時間で消すなら
  実額は僅少 →  例:  HOURS=3 infra/scripts/cost-estimate.sh staging
* terraform destroy 後は全サービス $0(消し忘れゼロが合格条件)。
* パブリック IPv4 は 2024-02 以降、インスタンスに付いていても課金。
* データ転送(送信)は最初 100GB/月 無料。超過は $0.114/GB(東京)。
* 料金は 2026-07 の on-demand スナップショット。実費は AWS 料金ページで要確認。
NOTE
