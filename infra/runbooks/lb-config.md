# Runbook: LB の nginx 設定変更

無停止で設定を差し替える(restart はサービスを止めるので使わない)。

## 手順
```bash
ssh ubuntu@<lb_ip>
cd /src/loadbalancer
# conf.d/proxy.conf 等を編集(編集対象が loadbalancer 内か必ず確認)
sudo nginx -t -c /src/loadbalancer/nginx.conf     # 構文チェック(必須)
sudo systemctl reload nginx                        # 無停止リロード
```

## 確認
```bash
curl -Iv https://quantz.thinkxinc.com
# バックエンド疎通(web が listen しているか)
curl -k https://<web_ip>:8005/ -H "Host: thinkxinc.com"
```

## 注意
- `sudo systemctl restart nginx` や `. ./restart.sh` はサービスを止める。通常は reload を使う。
- proxy_pass 先の IP は移行後 192.168.x.11(web)。オンプレの 192.168.1.8 ではない。
- 変更は必ず loadbalancer リポジトリのファイルに対して行い、コミットする(手元の直編集で放置しない)。
