# ============================================================
# ネットワーク基盤 = オンプレの Cisco C1111-8P ルーターに相当
#   VPC        : LAN 全体(192.168.0.0/16)
#   subnet     : オンプレの 192.168.1.0/24 を再現(prod)
#   IGW        : インターネットへの出口(Cisco の Dialer1/PPPoE)
#   routetable : 外向きデフォルトルート(Cisco の NAT overload + default route)
#
# プロジェクトキー = supercom(local.name_prefix = supercom-{env})
# ============================================================

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.common_tags
  }
}

resource "aws_vpc" "main" {
  cidr_block           = "192.168.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = local.name_prefix }
}

resource "aws_subnet" "lan" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.subnet_cidr
  availability_zone       = var.az
  map_public_ip_on_launch = true # LB/web に一時パブリック IP を付与(ssh 用)
  tags                    = { Name = "${local.name_prefix}-lan" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name_prefix}-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "${local.name_prefix}-rt" }
}

resource "aws_route_table_association" "lan" {
  subnet_id      = aws_subnet.lan.id
  route_table_id = aws_route_table.public.id
}
