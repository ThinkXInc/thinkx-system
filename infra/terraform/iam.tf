# ============================================================
# IAM = EC2 に付与する実行時権限
#   LB: certbot --dns-route53 用の Route53 最小権限(DNS-01 チャレンジの TXT 書き込み)。
#   アクセスキーを EC2 に置かず、インスタンスプロファイルで権限を渡す(CLAUDE.md #6)。
#   web は現状権限不要のためロールなし(SES 等が必要になったら追加)。
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
