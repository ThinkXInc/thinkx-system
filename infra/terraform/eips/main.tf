# ============================================================
# EIP 台帳(唯一のマスター・D-53)
#   固定 IP の寿命を環境(envs/)の作成・破壊から分離する常設 terraform。
#   envs/<env> は EIP を作らず、ここで宣言された EIP を tag:Name で参照して
#   自分のインスタンスに紐付けるだけ。環境を destroy しても IP は残り、
#   DNS の再設定は二度と不要になる。
#
#   この台帳は原則 destroy しない(IP を手放す時のみ・オーナー判断)。
#   terraform_destroy.sh も eips を対象にできない(staging|prod のみ受ける)。
#   注: EIP は未使用期間も使用中と同額課金(約 $3.6/月/本・2024-02 以降)。
#
#   台帳(EIP ↔ サーバーの対応。役割名で envs 側と 1:1 に対応する):
#     prod_web    -> envs/prod    の web (web1)      = 57.182.151.177
#     prod_lb     -> envs/prod    の lb  (lb1)       = 52.197.179.70   本番公開 IP(apex A レコードの向き先)
#     staging_web -> envs/staging の web (web1-stg)  = 57.182.107.57
#     staging_lb  -> envs/staging の lb  (lb1-stg)   = 52.68.142.190   staging.<domain> の向き先
#   (IP 値はコメント = 人間用メモ。機械的な正は state と `terraform output`)
# ============================================================

terraform {
  required_providers {
    aws = { source = "hashicorp/aws" }
  }
}

provider "aws" {
  region = "ap-northeast-1"
}

resource "aws_eip" "prod_web" {
  domain = "vpc"
  tags   = { Name = "supercom-prod-eip-web", Env = "prod", Project = "supercom", Managed = "terraform" }
}

resource "aws_eip" "prod_lb" {
  domain = "vpc"
  tags   = { Name = "supercom-prod-eip-lb", Env = "prod", Project = "supercom", Managed = "terraform" }
}

resource "aws_eip" "staging_web" {
  domain = "vpc"
  tags   = { Name = "supercom-staging-eip-web", Env = "staging", Project = "supercom", Managed = "terraform" }
}

resource "aws_eip" "staging_lb" {
  domain = "vpc"
  tags   = { Name = "supercom-staging-eip-lb", Env = "staging", Project = "supercom", Managed = "terraform" }
}

output "eip_ledger" {
  description = "EIP 台帳(役割 -> IP)"
  value = {
    prod_web    = aws_eip.prod_web.public_ip
    prod_lb     = aws_eip.prod_lb.public_ip
    staging_web = aws_eip.staging_web.public_ip
    staging_lb  = aws_eip.staging_lb.public_ip
  }
}
