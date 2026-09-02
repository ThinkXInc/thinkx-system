# podcast(LB 側) — LB 機で実行する。Basic 認証ファイルを作る
#
# prerequisites:
#  - setup_loadbalancer.sh 済み + デプロイ済みで loadbalancer/conf.d/direct.conf が配られていること
#    (conf の反映・nginx reload はデプロイ側が行う。ここでは認証ファイルだけ作る)
#
# 使い方: bash setup_podcast_lb.sh
#   最後の1行が対話(パスワード入力)。作業者に渡すユーザー名を変えるときは editor を書き換える

sudo apt-get install -y apache2-utils

# 対話: パスワードを2回入力する。このファイルが http://{EIP}/podcast/ の鍵になる
sudo htpasswd -c /etc/nginx/.htpasswd_podcast editor
