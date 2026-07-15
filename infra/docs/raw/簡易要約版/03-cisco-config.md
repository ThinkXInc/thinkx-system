# Cisco C1111-8P 設定(原本)

接続(モデム<->WAN 0/0/0、8ポートにサーバー)、コンソール(screen tty.usbserial)、
enable(pass: super)、configure terminal。

主要設定:
- Vlan1: ip address 192.168.1.1 255.255.255.0 / ip nat inside
- PPPoE(GigabitEthernet0/0/0): dial-pool-number 1
- Dialer1: OCN 認証(a6351230@one.ocn.ne.jp)/ ip nat outside / encapsulation ppp
- NAT: ip nat inside source list 1 interface Dialer1 overload
- DHCP: ip dhcp pool LAN_POOL (192.168.1.0/24)
- ポートフォワード: ip nat inside source static tcp 192.168.1.x 22 interface Dialer1 <port>
- 保存: write memory(忘れると再起動で消える)

> 移行後: 全て VPC + Security Group + EIP + route table に置換。
> terraform/main.tf, security.tf, instances.tf を参照。この原本の運用は消滅。
> 【注意】この原本には OCN 認証 ID/PW・enable パスワードが平文。移行後に無効化推奨。
