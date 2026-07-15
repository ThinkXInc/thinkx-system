# Runbook: 特定サイトだけ再起動

各サイトは独立した systemd サービス。他サイトに影響せず再起動できる。

## 手順
```bash
ssh ubuntu@<web_ip>
# truetechjapan は thinkx アプリ内(8005)なので thinkx 再起動
sudo systemctl restart uwsgi_thinkx.service
# transformism だけ
sudo systemctl restart uwsgi_transformism.service
# kazukiotsuka だけ
sudo systemctl restart uwsgi_kazukiotsuka.service
```

## 確認
```bash
curl -i localhost:8005                          # web 単体
curl -ik -H "Host: truetechjapan.com" https://<lb_ip>/   # LB 経由
```

## 対応表(ドメイン -> サービス/ポート)
| ドメイン | サービス | ポート |
|---|---|---|
| thinkxinc.com / truetechjapan.com / nntmapp.com / nntm.thinkxinc.com | uwsgi_thinkx | 8005 |
| transformism.art | uwsgi_transformism | 8006 |
| kazukiotsuka.com | uwsgi_kazukiotsuka | 8007 |
| quantz.thinkxinc.com | uwsgi_quantz(載せる場合) | 8000 |
