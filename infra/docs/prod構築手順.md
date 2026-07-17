# thinkx-system/infra/docs/prod構築手順.md
#
# EC2 2台(web/lb)をゼロから建てて全サイト配信・受け入れ試験 green まで。
#

## 0. 変数(新しいターミナルを開いたら必ずここから)

```
cd ~/Sources/thinkx-system
ENVX=prod
WEB=supercom-web
LB=supercom-lb
```

## 1. terraform apply(2〜3分)

```
cd ~/Sources/thinkx-system
: "${ENVX:?手順0の変数を先に貼る}"
terraform -chdir=infra/terraform apply -var="env=$ENVX"
```

## 2. ssh alias を新 IP に(1分。HostName を出力の public IP へ)

```
cd ~/Sources/thinkx-system
terraform -chdir=infra/terraform output
```

```
cd ~/Sources/thinkx-system
vim ~/.ssh/config
```

## 3. deploy key(初回のみ。表示に従い GitHub 登録)

```
cd ~/Sources/thinkx-system
bash infra/deploykeys/gen_deploy_key.sh thinkx-system libcommon simplicity
```

## 4. secrets 配布(1分)

```
cd ~/Sources/thinkx-system
: "${WEB:?手順0の変数を先に貼る}"
: "${LB:?手順0の変数を先に貼る}"
tar czf /tmp/secrets.tgz -C infra certs deploykeys
scp /tmp/secrets.tgz infra/setup/check_deploykey.py $WEB:/tmp/
scp /tmp/secrets.tgz infra/setup/check_deploykey.py $LB:/tmp/
```

## 5. web: 基盤(15〜30分)

```
cd ~/Sources/thinkx-system
: "${WEB:?手順0の変数を先に貼る}"
ssh $WEB 'bash -s' < infra/setup/setup_user.sh
ssh $WEB 'bash -s' < infra/setup/setup_webserver.sh
```

## 6. web: 鍵検証 + monorepo(1〜2分)

```
cd ~/Sources/thinkx-system
: "${WEB:?手順0の変数を先に貼る}"
ssh $WEB 'tar xzf /tmp/secrets.tgz -C /tmp; python3 /tmp/check_deploykey.py thinkx-system'
ssh $WEB 'python3 /tmp/check_deploykey.py libcommon'
ssh $WEB 'python3 /tmp/check_deploykey.py simplicity'
ssh $WEB 'bash -s' < infra/setup/clone_monorepo.sh
```

## 7. .env / assets 配布(1〜5分)

```
cd ~/Sources/thinkx-system
: "${WEB:?手順0の変数を先に貼る}"
bash infra/etc/push_env.sh $WEB thinkx kazukiotsukacom transformism
bash infra/etc/push_assets.sh $WEB thinkx
```

## 8. web: サイト + nginx(10〜20分)

```
cd ~/Sources/thinkx-system
: "${WEB:?手順0の変数を先に貼る}"
ssh $WEB 'bash -s' < infra/setup/setup_thinkx.sh
ssh $WEB 'bash -s' < infra/setup/setup_kazukiotsukacom.sh
ssh $WEB 'bash -s' < infra/setup/setup_transformism.sh
ssh $WEB 'bash -s' < infra/setup/setup_nginx-web-root.sh
```

## 9. lb(15〜30分)

```
cd ~/Sources/thinkx-system
: "${LB:?手順0の変数を先に貼る}"
ssh $LB 'bash -s' < infra/setup/setup_user.sh
ssh $LB 'tar xzf /tmp/secrets.tgz -C /tmp; python3 /tmp/check_deploykey.py thinkx-system'
ssh $LB 'bash -s' < infra/setup/clone_monorepo.sh
bash infra/etc/push_env.sh $LB loadbalancer
ssh $LB 'bash -s' < infra/setup/setup_loadbalancer.sh
```

## 10. 受け入れ試験(1〜2分。`ACCEPTANCE: 全サイト green` で完成)

```
cd ~/Sources/thinkx-system
: "${LB:?手順0の変数を先に貼る}"
LB_IP=$(terraform -chdir=infra/terraform output -raw lb_public_ip)
bash infra/scripts/acceptance-sweep.sh $LB_IP
```
