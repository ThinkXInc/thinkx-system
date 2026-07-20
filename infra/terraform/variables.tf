# ============================================================
# 環境切り替え変数
#   apply 例:
#     terraform apply -var="env=staging"
#     terraform apply -var="env=prod"
#
# プロジェクトキー = supercom(確定)
#   - インフラのリソース接頭辞・タグ・キーペア・バケットに使う
#   - アプリ/ドメイン名の thinkx(thinkxinc.com, uwsgi_thinkx 等)とは別物。混同しない
# ============================================================

variable "project" {
  description = "プロジェクトキー(リソース接頭辞・タグ)。確定値: supercom"
  type        = string
  default     = "supercom"
}

variable "env" {
  description = "prod または staging。デフォルトは事故防止のため staging"
  type        = string
  default     = "staging"
  validation {
    condition     = contains(["prod", "staging"], var.env)
    error_message = "env は prod か staging のいずれか。"
  }
}

variable "region" {
  description = "AWS リージョン"
  type        = string
  default     = "ap-northeast-1" # 東京
}

variable "az" {
  description = "アベイラビリティゾーン"
  type        = string
  default     = "ap-northeast-1a"
}

variable "key_name" {
  description = "EC2 に紐付ける既存キーペア名(事前に AWS で作成しておく)"
  type        = string
  default     = "supercom"
}

variable "my_office_ips" {
  description = "SSH(22)を許可する拠点グローバル IP のリスト。各要素は必ず /32。0.0.0.0/0 は禁止。通常は terraform.tfvars が供給する — この入力を対話で聞かれたら tfvars 欠落が原因。現在の IP は curl -s https://checkip.amazonaws.com で分かる(追加は scripts/add_current_office_ip.sh)"
  type        = list(string)
  # 例: ["203.0.113.5/32", "198.51.100.7/32"]。terraform.tfvars で指定(tfvars はコミットしない)
  # 追加は scripts/add_current_office_ip.sh(現在地の IP を追記して apply)
}

# ------------------------------------------------------------
# 環境ごとの派生値
#   - name_prefix: supercom-prod / supercom-staging
#   - サイズ: prod は本番相当、staging は最小
#   - サブネット: prod=192.168.1.0/24, staging=192.168.2.0/24
#   - 固定 IP: LB=.10, web=.11(オンプレの supercom3L/2 の役割に対応)
# ------------------------------------------------------------
locals {
  is_prod = var.env == "prod"

  # 命名規則(infra/docs/hostname.md): 基本名 {role}{n}、env は接尾辞 -stg(prod は無印)
  env_suffix = local.is_prod ? "" : "-stg"

  # 全リソース共通の接頭辞
  name_prefix = "${var.project}-${var.env}"

  # 全リソース共通タグ
  common_tags = {
    Project = var.project
    Env     = var.env
    Managed = "terraform"
  }

  # サイズは env ごとに独立(D-57)。配信専用の prod は小さく、開発(Claude Code+ビルド)する
  # staging web は RAM 余裕のため大きく = 従来の prod>staging を web で反転。lb は両 env とも micro
  web_type = local.is_prod ? "t3.small" : "t3.medium"
  lb_type  = "t3.micro"

  subnet_cidr = local.is_prod ? "192.168.1.0/24" : "192.168.2.0/24"
  lb_ip       = local.is_prod ? "192.168.1.10" : "192.168.2.10"
  web_ip      = local.is_prod ? "192.168.1.11" : "192.168.2.11"

  web_disk_gb = local.is_prod ? 50 : 20
}
