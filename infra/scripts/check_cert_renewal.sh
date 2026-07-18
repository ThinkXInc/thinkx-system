#!/usr/bin/env bash
# thinkx-system/infra/scripts/check_cert_renewal.sh   【分類: 観測系(見るだけ・状態を変えない)】
#
# TLS 証明書の自動更新が本当に機能するかを LB 上で検証する。
#   [1] 証明書一覧と有効期限(certbot certificates)
#   [2] renewal 設定の authenticator(全件 dns-route53 であること)
#   [3] certbot.timer の稼働(次回実行予定)
#   [4] certbot renew --dry-run(Route53 への TXT 書込→検証まで本番同経路で通す。約1〜2分)
#
#   使い方: bash infra/scripts/check_cert_renewal.sh <LB_alias>
#   例:     bash infra/scripts/check_cert_renewal.sh supercom-lb1

check_cert_renewal() {
  local lb="${1:-}"
  local G=$'\033[32m' R=$'\033[31m' Z=$'\033[0m'
  local manual dry rc
  [ -n "$lb" ] || { printf '%b\n' "${R}FAIL: check_cert_renewal usage: check_cert_renewal.sh <LB_alias>${Z}"; return 1; }

  echo "── [1] 証明書一覧と有効期限($lb)──"
  ssh -o BatchMode=yes -o ConnectTimeout=8 "$lb" 'sudo certbot certificates 2>/dev/null' | grep -E "Certificate Name|Domains|Expiry"

  echo "── [2] renewal の authenticator ──"
  manual="$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$lb" 'sudo grep -H "^authenticator" /etc/letsencrypt/renewal/*.conf' 2>/dev/null)"
  printf '%s\n' "$manual"

  echo "── [3] certbot.timer ──"
  ssh -o BatchMode=yes -o ConnectTimeout=8 "$lb" 'systemctl list-timers certbot.timer --no-pager' | head -2

  echo "── [4] certbot renew --dry-run(1〜2分)──"
  dry="$(ssh -o BatchMode=yes -o ConnectTimeout=8 "$lb" 'sudo certbot renew --dry-run 2>&1')"
  rc=$?
  printf '%s\n' "$dry"

  echo
  printf '%s' "$manual" | grep -q "= manual" && { printf '%b\n' "${R}FAIL: check_cert_renewal $lb に authenticator=manual が残存(自動更新不可)${Z}"; return 1; }
  [ "$rc" -eq 0 ] && printf '%s' "$dry" | grep -q "Congratulations, all simulated renewals succeeded" \
    && printf '%b\n' "${G}OK: check_cert_renewal $lb 全ドメイン自動更新可能(dry-run 成功)${Z}" \
    || printf '%b\n' "${R}FAIL: check_cert_renewal $lb dry-run 失敗(rc=$rc)。上の出力を確認${Z}"
}

check_cert_renewal "$@"
