# ============================================================
# IAM = EC2 に付与する実行時権限
#   LB: certbot --dns-route53 用の Route53 最小権限(DNS-01 チャレンジの TXT 書き込み)。
#   アクセスキーを EC2 に置かず、インスタンスプロファイルで権限を渡す(CLAUDE.md #6)。
#   web(prod のみ): staging の電源(describe/start/stop)だけ。KOBITO リモコンの本番入口 /remote_control/ 用
#   (P トラック・オーナー裁定 2026-09-17)。staging の web にはロールを付けない。
# ============================================================

resource "aws_iam_role" "lb" {
  name = "${local.name_prefix}-lb"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = { Name = "${local.name_prefix}-lb" }
}

# certbot-dns-route53 が要求する最小セット
resource "aws_iam_role_policy" "lb_route53" {
  name = "certbot-dns-route53"
  role = aws_iam_role.lb.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["route53:ListHostedZones", "route53:GetChange"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["route53:ChangeResourceRecordSets"]
        Resource = "arn:aws:route53:::hostedzone/*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "lb" {
  name = "${local.name_prefix}-lb"
  role = aws_iam_role.lb.name
}

# ------------------------------------------------------------
# web(prod のみ): staging の電源だけ
#   - DescribeInstances は表示用(Resource を絞れない API)
#   - Start/Stop は Project=supercom かつ Env=staging のタグを持つインスタンスに限定。
#     本番インスタンスや terminate・設定変更は構造的に不可
#   - count で prod だけに作る(staging の web にはロールを付けない・オーナー裁定 2026-09-17)
# ------------------------------------------------------------
resource "aws_iam_role" "web" {
  count = local.is_prod ? 1 : 0
  name  = "${local.name_prefix}-web"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = { Name = "${local.name_prefix}-web" }
}

resource "aws_iam_role_policy" "web_staging_power" {
  count = local.is_prod ? 1 : 0
  name  = "staging-power"
  role  = aws_iam_role.web[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ec2:DescribeInstances"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["ec2:StartInstances", "ec2:StopInstances"]
        Resource = "arn:aws:ec2:*:*:instance/*"
        Condition = {
          StringEquals = {
            "ec2:ResourceTag/Project" = "supercom"
            "ec2:ResourceTag/Env"     = "staging"
          }
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "web" {
  count = local.is_prod ? 1 : 0
  name  = "${local.name_prefix}-web"
  role  = aws_iam_role.web[0].name
}
