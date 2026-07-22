#!/usr/bin/env bash
# thinkx-system/infra/scripts/acceptance-sweep.sh   【分類: 観測系(見るだけ・状態を変えない)】
#
# 受け入れ試験: 各サイトの tests/golden/route_sweep.json の全 GET ルートを
# LB へ https で当て、(ルート, ステータス) をゴールデンと全件照合する。
# DNS には依存しない(--resolve で Host→LB IP を固定)。
#
#   使い方: infra/scripts/acceptance-sweep.sh <LB_IP>
#   例:     infra/scripts/acceptance-sweep.sh 52.197.179.70
#
# ルール→具体 URL は test_route_sweep.py の _concrete と同一(<lang>→en / 他→x)。
# 出力は全ルート分を丸めず表示。末尾に site ごとの pass/fail と総合判定。

acceptance_sweep() {
  local lb_ip="${1:?usage: acceptance-sweep.sh <LB_IP>}"
  local here ws
  here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
  ws="$(cd "$here/../.." && pwd)"
  command -v python3 >/dev/null 2>&1 || { echo "python3 が見つからない" >&2; return 0; }
  command -v curl    >/dev/null 2>&1 || { echo "curl が見つからない"    >&2; return 0; }

  local total_fail=0 site host golden line path expect got mark fail count
  local G=$'\033[32m' R=$'\033[31m' Z=$'\033[0m'

  # 受け入れ試験の対象外ルート(site:path)。公開 Host での sweep では意味を持たないもの。
  # golden(サイト単体テストが正)には残す。増えたらここに1行足すだけ。
  local -a exclude=(
    "thinkx:/filedrop"   # main.py:787: -stg ホスト時のみ有効。公開 Host では常に 404
  )

  for site_host in "thinkx:thinkxinc.com" "kazukiotsukacom:kazukiotsuka.com" "transformism:transformism.art"; do
    site="${site_host%%:*}"; host="${site_host##*:}"
    golden="$ws/$site/web-server/tests/golden/route_sweep.json"
    [ -f "$golden" ] || { echo "${R}FAIL: $golden が無い${Z}"; total_fail=$((total_fail+1)); continue; }

    echo "===== $site (Host: $host -> $lb_ip) ====="
    fail=0; count=0
    while IFS=$'\t' read -r path expect; do
      # 対象外リスト(exclude)に含まれるルートは飛ばす。黙って落とさず skip 行を出す。
      case " ${exclude[*]} " in
        *" $site:$path "*) printf 'skip  %s (受け入れ対象外)\n' "$path"; continue ;;
      esac
      count=$((count+1))
      got=$(curl -sk --max-time 20 --resolve "$host:443:$lb_ip" \
              -o /dev/null -w '%{http_code}' "https://$host$path")
      if [ "$got" = "$expect" ]; then mark="${G}ok${Z}"; else mark="${R}NG${Z}"; fail=$((fail+1)); fi
      printf '%b  expect=%s got=%s  %s\n' "$mark" "$expect" "$got" "$path"
    done < <(python3 -c '
import json, re, sys
d = json.load(open(sys.argv[1]))
conc = lambda r: re.sub(r"<[^>]+>", lambda m: "en" if "lang" in m.group(0) else "x", r)
for rule in sorted(d):
    print(f"{conc(rule)}\t{d[rule]}")' "$golden")

    if [ "$fail" -eq 0 ]; then
      printf '%b\n' "${G}$site: $count/$count 一致${Z}"
    else
      printf '%b\n' "${R}$site: $fail/$count 不一致${Z}"
      total_fail=$((total_fail+fail))
    fi
    echo
  done

  if [ "$total_fail" -eq 0 ]; then
    printf '%b\n' "${G}ACCEPTANCE: 全サイト green${Z}"
  else
    printf '%b\n' "${R}ACCEPTANCE: 不一致 $total_fail 件${Z}"
  fi
}

acceptance_sweep "$@"
