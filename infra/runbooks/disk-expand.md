# EBS ルートディスク拡張(再起動なし)

対象機: `HOST=supercom-web1-stg` / 対象env: `ENVX=staging`

1. サイズ変更(web は `web_disk_gb`)

```
vi infra/terraform/variables.tf
```

2. 差分確認と適用(in-place 更新であること・destroy 0 であることを見る)

```
bash infra/scripts/terraform_apply.sh $ENVX
```

3. 機内でパーティションとファイルシステムを拡張

```
ssh $HOST 'sudo growpart /dev/nvme0n1 1 && sudo resize2fs /dev/nvme0n1p1 && df -h /'
```
