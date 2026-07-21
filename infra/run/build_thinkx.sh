# build thinkx views
#
# js/css は .gitignore の生成物なので、ソース(src/js・src/less)を配っただけでは配信に出ない。
# repo の npm タスクは --watch 常駐用しかないため、ここではワンショットで直接叩く
# (setup_thinkx.sh の front build と同一のコマンド)。
#
# 冪等なので毎回実行してよい。条件分岐で「変わったときだけ」にすると、判定を間違えたときに
# 古い css を配り続ける(2026-07-21 に本番で実際に起きた)。数秒のコストで確実性を取る。

echo "== build thinkx views =="
cd /src/thinkx/web-server/views

sudo -u kaz npx babel src/js --out-dir js
sudo -u kaz npx lessc src/less/main.less css/main.css

sudo chown -R kaz:serveradmins js css 2>/dev/null

ls -la css/main.css js/main.js

[ -s css/main.css ] && [ -s js/main.js ] && printf '\033[32mOK: build_thinkx 完了\033[0m\n' || printf '\033[31mFAIL: build_thinkx の生成物が空\033[0m\n'
