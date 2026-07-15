# ============================================================
# apply 後に表示される情報(IP・ssh コマンド)
# ============================================================

output "env" {
  value = var.env
}

output "lb_public_ip" {
  description = "LB のパブリック IP(EIP・全 env 固定)"
  value       = aws_eip.lb.public_ip
}

output "web_public_ip" {
  description = "web のパブリック IP(EIP・全 env 固定)"
  value       = aws_eip.web.public_ip
}

output "lb_private_ip" {
  value = aws_instance.lb.private_ip
}

output "web_private_ip" {
  value = aws_instance.web.private_ip
}

output "ssh_lb" {
  description = "LB への ssh コマンド"
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_eip.lb.public_ip}"
}

output "ssh_web" {
  description = "web への ssh コマンド"
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_eip.web.public_ip}"
}

# setup を流すワンライナー(Claude Code / 人間が使う。Mac から実行)
output "setup_hint" {
  value = <<-EOT
    # 中身の構築(箱ができた後・Mac から実行):
    ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_eip.web.public_ip} 'bash -s' < ../setup/setup_webserver.sh
    WEB_IP=${aws_instance.web.private_ip} ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_eip.lb.public_ip} 'bash -s' < ../setup/setup_loadbalancer.sh
  EOT
}
