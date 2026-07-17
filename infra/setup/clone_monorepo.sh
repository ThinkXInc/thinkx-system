# clone monorepo(thinkx-system) + /src/<site> symlink
#
# prerequisites:
#  - setup_user.sh(kaz ユーザー・serveradmins グループ)
#  - check_deploykey.py thinkx-system が OK(鍵配置・GitHub 認証)
#  - (原本並置分・web のみ)check_deploykey.py libcommon / simplicity が OK
#
# *prod は polyrepo 個別 clone ではなく monorepo を 1 回 clone し、staging と同じ
#  /src/<site> パスを symlink で保つ(uwsgi service / nginx include はこのパス前提)。
#  以後の setup_<site>.sh は clone せずこの symlink を前提に動く。

# working directory(setup_webserver.sh 前でも動くよう冪等に作る)

sudo mkdir -p /src
sudo chown kaz:serveradmins /src

# clone monorepo

cd /src
sudo -u kaz git clone git@github-thinkx-system:ThinkXInc/thinkx-system.git
cd /src/thinkx-system
sudo -u kaz git checkout monorepo

# symlink(staging と同一の /src/<site> レイアウトを再現)

sudo ln -sfn /src/thinkx-system/thinkx /src/thinkx
sudo ln -sfn /src/thinkx-system/kazukiotsukacom /src/kazukiotsukacom
sudo ln -sfn /src/thinkx-system/transformism /src/transformism
sudo ln -sfn /src/thinkx-system/nginx-web-root /src/nginx-web-root
sudo ln -sfn /src/thinkx-system/loadbalancer /src/loadbalancer

# libcommon / simplicity 原本の並置(B案・ARCHIVE.md の参照 SHA が正)
# *鍵が配置されていない箱(lb)では WARN してスキップ

sudo -u kaz test -f /home/kaz/.ssh/deploy_libcommon && { cd /src; sudo -u kaz git clone git@github-libcommon:ThinkXInc/libcommon.git; cd /src/libcommon; sudo -u kaz git checkout a316494ff850094b767da041f429092735fd2877; } || printf '\033[33mWARN: deploy_libcommon 無し。libcommon 原本の並置をスキップ\033[0m\n'
sudo -u kaz test -f /home/kaz/.ssh/deploy_simplicity && { cd /src; sudo -u kaz git clone git@github-simplicity:ThinkXInc/simplicity.git; cd /src/simplicity; sudo -u kaz git checkout 53f0639449a937fe79935175a867689ee4b40a87; } || printf '\033[33mWARN: deploy_simplicity 無し。simplicity 原本の並置をスキップ\033[0m\n'

# verify

ls -l /src
cd /src/thinkx-system && sudo -u kaz git log --oneline -1
