# ============================================================
# 内部 DNS(Route53 プライベートホストゾーン)
#   zone = supercom.internal(.internal 直下に自組織ラベルを 1 階層挟む定石・ICANN 予約 TLD)
#   web1.supercom.internal / lb1.supercom.internal = 「あのマシン」を指す内部ラベル
#   (公開ドメイン(5つ以上)とは独立。1 台 1 名)
#   IP と名前の紐づけは terraform が唯一の真実: EC2 を作り直して IP が変われば
#   ここの A レコードも terraform が更新する。
#   LB nginx は resolver 169.254.169.253 + 変数 proxy_pass で TTL 追従(reload 不要)。
#   DHCP オプションで search domain = supercom.internal を配るため、
#   シェルでは `ssh web1` / `curl web1:8005` の短名で済む(FQDN は設定ファイル内だけ)。
# ============================================================

resource "aws_route53_zone" "internal" {
  name = "supercom.internal"
  vpc {
    vpc_id = aws_vpc.main.id
  }
  comment = "supercom internal names (web1/lb1). public domains とは独立"
  tags    = { Name = "${local.name_prefix}-internal" }
}

resource "aws_route53_record" "web1" {
  zone_id = aws_route53_zone.internal.zone_id
  name    = "web1.supercom.internal"
  type    = "A"
  ttl     = 60
  records = [aws_instance.web.private_ip]
}

resource "aws_route53_record" "lb1" {
  zone_id = aws_route53_zone.internal.zone_id
  name    = "lb1.supercom.internal"
  type    = "A"
  ttl     = 60
  records = [aws_instance.lb.private_ip]
}

# VPC の DHCP で search domain を配布(resolv.conf の search に supercom.internal が入り、
# `curl web1:8005` のような短名が VPC 内どこでも解決できる)
resource "aws_vpc_dhcp_options" "internal" {
  domain_name         = "supercom.internal"
  domain_name_servers = ["AmazonProvidedDNS"]
  tags                = { Name = "${local.name_prefix}-dhcp" }
}

resource "aws_vpc_dhcp_options_association" "internal" {
  vpc_id          = aws_vpc.main.id
  dhcp_options_id = aws_vpc_dhcp_options.internal.id
}
