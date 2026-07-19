┌─────────────────┬────────────────────────┬────────────────────────────────────────────┐
│       層        │          prod          │                  staging                   │
├─────────────────┼────────────────────────┼────────────────────────────────────────────┤
│ ① ssh alias     │ supercom-web1          │ supercom-web1-stg                          │
├─────────────────┼────────────────────────┼────────────────────────────────────────────┤
│ ② AWS Name タグ │ supercom-web1          │ supercom-web1-stg                          │
├─────────────────┼────────────────────────┼────────────────────────────────────────────┤
│ ③ 内部 DNS      │ web1.supercom.internal │ web1.supercom.internal(別ゾーン・変更なし) │
├─────────────────┼────────────────────────┼────────────────────────────────────────────┤
│ ④ hostname      │ web1                   │ web1-stg                                   │
└─────────────────┴────────────────────────┴────────────────────────────────────────────┘
## 変更手順

### prerequisites

```
cd ~/Sources/thinkx-system
```

### 1. ssh alias 改名(1分)

```
sed -i.bak -e 's/^Host supercom-web-stg$/Host supercom-web1-stg/' -e 's/^Host supercom-lb-stg$/Host supercom-lb1-stg/' -e 's/^Host supercom-web$/Host supercom-web1/' -e 's/^Host supercom-lb$/Host supercom-lb1/' ~/.ssh/config
grep "^Host supercom" ~/.ssh/config
```

### 2. AWS Name タグ: prod(2分)

```
bash infra/scripts/terraform_apply.sh prod
```

### 3. AWS Name タグ: staging(1分)

```
aws ec2 create-tags --resources $(aws ec2 describe-instances --filters "Name=tag:Name,Values=supercom-staging-web" --query "Reservations[].Instances[].InstanceId" --output text) --tags Key=Name,Value=supercom-web1-stg
aws ec2 create-tags --resources $(aws ec2 describe-instances --filters "Name=tag:Name,Values=supercom-staging-lb" --query "Reservations[].Instances[].InstanceId" --output text) --tags Key=Name,Value=supercom-lb1-stg
aws ec2 delete-tags --resources $(aws ec2 describe-instances --filters "Name=tag:Name,Values=supercom-web1-stg" --query "Reservations[].Instances[].InstanceId" --output text) --tags Key=Host
aws ec2 delete-tags --resources $(aws ec2 describe-instances --filters "Name=tag:Name,Values=supercom-lb1-stg" --query "Reservations[].Instances[].InstanceId" --output text) --tags Key=Host
```

### 4. hostname 4台(1分)

```
ssh supercom-web1 'sudo hostnamectl set-hostname web1; echo "preserve_hostname: true" | sudo tee /etc/cloud/cloud.cfg.d/99-hostname.cfg > /dev/null'
ssh supercom-lb1 'sudo hostnamectl set-hostname lb1; echo "preserve_hostname: true" | sudo tee /etc/cloud/cloud.cfg.d/99-hostname.cfg > /dev/null'
ssh supercom-web1-stg 'sudo hostnamectl set-hostname web1-stg; echo "preserve_hostname: true" | sudo tee /etc/cloud/cloud.cfg.d/99-hostname.cfg > /dev/null'
ssh supercom-lb1-stg 'sudo hostnamectl set-hostname lb1-stg; echo "preserve_hostname: true" | sudo tee /etc/cloud/cloud.cfg.d/99-hostname.cfg > /dev/null'
```

### 5. 確認(1分)

```
for h in supercom-web1 supercom-lb1 supercom-web1-stg supercom-lb1-stg; do printf "%-20s -> " $h; ssh -o ConnectTimeout=6 $h hostname; done
aws ec2 describe-instances --filters "Name=tag:Project,Values=supercom" "Name=instance-state-name,Values=running" --query "Reservations[].Instances[].Tags[?Key=='Name']|[]|[].Value" --output table
```

SG 等の周辺リソース名は I-STEP3(staging 再構築)で同規則へ。
