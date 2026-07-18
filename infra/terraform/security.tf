# ============================================================
# Security Group = オンプレ Cisco の NAT 静的設定 + ACL の代替
#
#   Cisco: ip nat inside source static tcp 192.168.1.6 443 ... 443
#     -> LB の SG で 443 をインターネットに開放 + Elastic IP
#   Cisco: ip nat inside source static tcp 192.168.1.8 22 ... 6666
#     -> SSH は拠点 IP からのみ(ポート変えは不要)
#   バックエンド 192.168.1.8:8005 等への内部到達
#     -> web の SG が「LB の SG からのみ」を許可(IP 参照でなく SG 参照)
#
# NOTE: 下記コメント中の thinkx/transformism/kazukiotsuka/quantz は
#       アプリ名(インフラキーの supercom とは別物)。
# ============================================================

# ---- LB(supercom3L 相当): インターネットから 443/80 を受ける ----
resource "aws_security_group" "lb" {
  name        = "${local.name_prefix}-lb-sg"
  description = "LB: TLS terminate / reverse proxy"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from anywhere (Lets Encrypt redirect)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH from office only (Cisco port-forward 6666-22 equivalent)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.my_office_ips
  }

  egress {
    description = "all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-lb-sg" }
}

# ---- web(supercom2 相当): LB からのバックエンドポートだけ受ける ----
resource "aws_security_group" "web" {
  name        = "${local.name_prefix}-web-sg"
  description = "web: nginx(static) + uwsgi backends"
  vpc_id      = aws_vpc.main.id

  # LB の SG からのみ 8000-8009 を許可
  #   8005 thinkx / 8006 transformism / 8007 kazukiotsuka / 8000 quantz(載せる場合)
  ingress {
    description     = "backend ports from LB SG only"
    from_port       = 8000
    to_port         = 8009
    protocol        = "tcp"
    security_groups = [aws_security_group.lb.id]
  }

  ingress {
    description = "SSH from office only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.my_office_ips
  }

  egress {
    description = "all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-web-sg" }
}
