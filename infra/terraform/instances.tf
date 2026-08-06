# ============================================================
# EC2 本体
#   lb  : supercom3L 相当(nginx TLS 終端/リバプロ)  固定 IP .10
#   web : supercom2  相当(nginx 静的配信 + uwsgi)    固定 IP .11
#   eip : オンプレのグローバル IP 123.226.234.127 に相当(prod のみ)
#
# 中身(apt/git/venv/uwsgi/nginx)は user_data に埋めない。
# setup/*.sh を ssh で流す方針(AWS 非依存・ポータブル)。
#
# Name タグはホスト名の連続性を保つ(supercom3L / supercom2)。
# ============================================================

# Ubuntu 22.04 の最新 AMI を自動取得(AMI ID をハードコードしない)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "lb" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = local.lb_type
  subnet_id              = aws_subnet.lan.id
  private_ip             = local.lb_ip
  vpc_security_group_ids = [aws_security_group.lb.id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.lb.name # certbot --dns-route53 用(iam.tf)

  # AMI 差分での破壊再作成を禁止(2026-08-06 の全損事故の再発防止)。
  # data.aws_ami が新しい Ubuntu AMI を拾うたび「要再作成」差分が常に潜伏し、
  # 無関係な apply に巻き込まれて中身ごと消える。新 AMI は意図した建て直し
  # (taint / destroy)のときだけ拾う。
  lifecycle {
    ignore_changes = [ami]
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name = "supercom-lb1${local.env_suffix}" # 命名規則: infra/docs/hostname.md
    Role = "loadbalancer"
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = local.web_type
  subnet_id              = aws_subnet.lan.id
  private_ip             = local.web_ip
  vpc_security_group_ids = [aws_security_group.web.id]
  key_name               = var.key_name

  # AMI 差分での破壊再作成を禁止(理由は lb 側の同名ブロック参照)
  lifecycle {
    ignore_changes = [ami]
  }

  root_block_device {
    volume_size = local.web_disk_gb
    volume_type = "gp3"
  }

  tags = {
    Name = "supercom-web1${local.env_suffix}" # 命名規則: infra/docs/hostname.md
    Role = "web"
  }
}

# Elastic IP(lb/web とも全 env で固定。staging も頻繁にアクセスするため
# stop/start・作り直しで IP が変わると ssh config や検証手順が壊れる。
# 2024-02 以降 IPv4 は自動割当でも EIP でも同額なので稼働中のコスト増なし)
# EIP は常設台帳(../eips が唯一のマスター・D-53)が所有する。
# ここでは tag:Name で自分の環境の分を参照してインスタンスに紐付けるだけ。
# 環境を destroy しても EIP は台帳に残り、DNS 再設定は不要。
data "aws_eip" "lb" {
  filter {
    name   = "tag:Name"
    values = ["${local.name_prefix}-eip-lb"]
  }
}

data "aws_eip" "web" {
  filter {
    name   = "tag:Name"
    values = ["${local.name_prefix}-eip-web"]
  }
}

resource "aws_eip_association" "lb" {
  instance_id         = aws_instance.lb.id
  allocation_id       = data.aws_eip.lb.id
  allow_reassociation = true
}

resource "aws_eip_association" "web" {
  instance_id         = aws_instance.web.id
  allocation_id       = data.aws_eip.web.id
  allow_reassociation = true
}
