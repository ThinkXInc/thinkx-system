#!/usr/bin/env bash
# thinkx-system/infra/scripts/health_check.sh
# 【分類: 観測系(サイトの死活を見て Discord に通知する。変えるのは自前の状態ファイルと通知だけ)】
#
#   使い方: HEALTH_CONFIG=infra/health_check/loadbalancer.yaml bash infra/scripts/health_check.sh
#           (HEALTH_CONFIG 省略時は同リポジトリの infra/health_check/loadbalancer.yaml)
#
# 設定はリポジトリ内の YAML(infra/health_check/loadbalancer.yaml / local.yaml)に置く
# (オーナー指示 2026-09-18「なるべくレポジトリに入れる」「.envとは秘密情報を意味する」)。
# **秘密の webhook URL だけは git に入れず**、設定の webhook_env が指す既存の .env に相乗りする
# (新しい秘密ファイルは作らない — オーナー指示 2026-09-18。置き方は infra/runbooks/health-check.md)。
# YAML のキー:
#   sites:               監視対象。「  名前: URL」を並べる
#   webhook_env          HEALTH_DISCORD_WEBHOOK_URL=... を含む git 管理外の .env のパス。
#                        LB は /src/loadbalancer/.env(LB の .env はこれが最初)、local は thinkx/web-server/.env。
#                        webhook 先は専用チャンネル。他と混ぜない(オーナー指示 2026-09-18)
#   staging_gated_url    任意。EC2 の staging が running のときだけ死活を見る URL
#                        (stopped は意図した停止なので正常扱い。aws CLI と権限が要る)
#   state_dir            状態ファイルの置き場(既定 /var/lib/supercom-health)
#   renotify_sec         落ち続けている間の再通知間隔秒(既定 3600)
#
# 判定: curl 15 秒 timeout を 5 秒空けて 2 回。2 回とも 2xx/3xx/401 以外なら down
#       (401 は Basic 認証つきサイトの「生きている」応答)。
# 通知: up→down で 1 回・down→up で 1 回(復旧)・down 継続中は RENOTIFY_SEC ごとに 1 回。

__health_now() { date +%s; }

__health_notify() {
  local msg="$1"
  if [ -z "${DISCORD_WEBHOOK_URL:-}" ]; then
    echo "NOTIFY(未設定のため標準出力のみ): $msg"
    return 0
  fi
  curl -sS --fail -m 10 -H 'Content-Type: application/json' \
    -d "$(printf '{"content":"%s"}' "$msg")" "$DISCORD_WEBHOOK_URL" >/dev/null 2>&1 ||
    echo "WARN: Discord への送信に失敗(URL 誤りか到達不能): $msg"
}

# $1=URL。生きていれば 0。2 回試す(瞬断で騒がないため)
__health_probe() {
  local url="$1" code try
  for try in 1 2; do
    code="$(curl -sS -o /dev/null -w '%{http_code}' -m 15 "$url" 2>/dev/null || true)"
    case "$code" in 2??|3??|401) return 0 ;; esac
    [ "$try" = 1 ] && sleep 5
  done
  HEALTH_LAST_CODE="$code"
  return 1
}

# $1=名前 $2=生死(up/down)。状態ファイルと突き合わせて通知を決める
__health_report() {
  local name="$1" now_state="$2" file="$STATE_DIR/$name" host
  local prev=up since=0 last=0 now mins
  host="$(hostname 2>/dev/null || echo unknown)"
  now="$(__health_now)"
  [ -f "$file" ] && read -r prev since last < "$file" 2>/dev/null

  if [ "$now_state" = up ]; then
    if [ "$prev" = down ]; then
      mins=$(( (now - since) / 60 ))
      __health_notify "🟢 $name 復旧しました(${mins}分ぶり。checker=$host)"
    fi
    echo "up $now 0" > "$file"
    return 0
  fi

  if [ "$prev" != down ]; then
    __health_notify "🔴 $name が落ちています(HTTP ${HEALTH_LAST_CODE:-?}。checker=$host)"
    echo "down $now $now" > "$file"
    return 0
  fi
  if [ $(( now - last )) -ge "${RENOTIFY_SEC:-3600}" ]; then
    mins=$(( (now - since) / 60 ))
    __health_notify "🔴 $name はまだ落ちています(${mins}分経過。checker=$host)"
    echo "down $since $now" > "$file"
  else
    echo "down $since $last" > "$file"
  fi
}

# staging の EC2 が running かどうか。running=0 / stopped 等=1 / 分からない=2
__health_staging_running() {
  local states
  command -v aws >/dev/null 2>&1 || return 2
  states="$(aws ec2 describe-instances \
    --filters "Name=tag:Project,Values=supercom" "Name=tag:Env,Values=staging" \
    --query "Reservations[].Instances[].State.Name" --output text 2>/dev/null || true)"
  [ -n "$states" ] || return 2
  case "$states" in *running*) return 0 ;; esac
  return 1
}

# 設定 YAML を読む。sites: の下の「  名前: URL」を SITES("名前=URL" の空白区切り)に、
# トップレベルの「キー: 値」を対応する変数に入れる(素朴な行パース。ネストは sites の 1 段だけ)
__health_load_config() {
  local file="$1" section="" line key val
  while IFS= read -r line; do
    case "$line" in
      "#"*|"") ;;
      "sites:") section=sites ;;
      "  "*)
        [ "$section" = sites ] || continue
        line="${line#"${line%%[![:space:]]*}"}"
        key="${line%%:*}"; val="${line#*: }"
        SITES="$SITES $key=$val" ;;
      *": "*)
        section=""
        key="${line%%:*}"; val="${line#*: }"
        case "$key" in
          webhook_env)       WEBHOOK_ENV="$val" ;;
          staging_gated_url) STAGING_GATED_URL="$val" ;;
          state_dir)         STATE_DIR="$val" ;;
          renotify_sec)      RENOTIFY_SEC="$val" ;;
          *) echo "WARN: 知らない設定キー: $key($file)" ;;
        esac ;;
    esac
  done < "$file"
}

health_check() {
  local here config entry name url
  here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
  config="${HEALTH_CONFIG:-$here/../health_check/loadbalancer.yaml}"

  [ -f "$config" ] || { echo "WARN: 設定 YAML が無い: $config(runbooks/health-check.md を見て作る)"; return 0; }
  SITES=""
  __health_load_config "$config"
  if [ -n "${WEBHOOK_ENV:-}" ]; then
    if [ -f "$WEBHOOK_ENV" ]; then
      DISCORD_WEBHOOK_URL="$(grep -E '^HEALTH_DISCORD_WEBHOOK_URL=' "$WEBHOOK_ENV" 2>/dev/null | tail -1 | cut -d= -f2- | tr -d "\"'")"
      [ -n "$DISCORD_WEBHOOK_URL" ] || echo "WARN: $WEBHOOK_ENV に HEALTH_DISCORD_WEBHOOK_URL が無い(通知は標準出力のみ。runbooks/health-check.md)"
    else
      echo "WARN: webhook_env が無い: $WEBHOOK_ENV(通知は標準出力のみ。runbooks/health-check.md を見て作る)"
    fi
  fi
  STATE_DIR="${STATE_DIR:-/var/lib/supercom-health}"
  mkdir -p "$STATE_DIR" 2>/dev/null || { echo "WARN: STATE_DIR を作れない: $STATE_DIR"; return 0; }

  for entry in ${SITES:-}; do
    name="${entry%%=*}"; url="${entry#*=}"
    HEALTH_LAST_CODE=""
    if __health_probe "$url"; then
      __health_report "$name" up
    else
      __health_report "$name" down
    fi
  done

  if [ -n "${STAGING_GATED_URL:-}" ]; then
    __health_staging_running
    case "$?" in
      0) HEALTH_LAST_CODE=""
         if __health_probe "$STAGING_GATED_URL"; then
           __health_report staging up
         else
           __health_report staging down
         fi ;;
      1) echo "up $(__health_now) 0" > "$STATE_DIR/staging" ;;
      2) echo "WARN: staging の EC2 状態が取れない(aws CLI か権限)。staging の判定を飛ばした" ;;
    esac
  fi
}

health_check "$@"
