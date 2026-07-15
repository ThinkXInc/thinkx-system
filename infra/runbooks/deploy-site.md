# Runbook: サイトの変更をデプロイ(ページ追加等)

## 前提
- デプロイするブランチ/タグは人間が指示(既定: 2026refactor -> master マージ後の v2.1.0)。
- master を勝手に前提にしない。

## 手順
```bash
ssh ubuntu@<web_ip>
cd /src/thinkx
sudo -u kaz git fetch --all --tags
sudo -u kaz git checkout <指示されたref>
sudo -u kaz git pull --rebase origin <指示されたref>

# フロントビルド(必要時)
cd /src/thinkx/web-server/views
sudo -u kaz npx npm-run-all --parallel \
  compile:views:js compile:views:css copy:simplicity:js copy:simplicity:css

# アプリ再起動
sudo systemctl restart uwsgi_thinkx.service
```

## 確認(ゴールデン照合)
```bash
# 追加したパスが 200 を返すか
curl -i localhost:8005/blognews/<new_id>
# ルートゴールデンがあれば全 GET を照合(受け入れ試験と同一物)
# web-server/tests/golden/ の (rule,status) 一覧を staging LB に curl 照合
```

## 注意
- libcommon は vendoring 済み。`git submodule update` は不要(playbooks submodule のみ)。
- コード修正が必要になったら、ここで直さず findings として報告し停止(デプロイは取得して流すだけ)。
