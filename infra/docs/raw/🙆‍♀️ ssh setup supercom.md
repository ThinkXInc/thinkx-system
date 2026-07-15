# 🙆‍♀️ ssh setup supercom

_created: 20240407T092746Z / updated: 20240925T092401Z_

mkdir .ssh

chmod 700 .ssh

touch .ssh/authorized_keys

chmod 600 .ssh/authorized_keys

vim .ssh/authorized_keys

```
# supercom3L
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAhxrxBDbXDnlOe6Q0TntgQVGAsQ3JQytQrgSrW/W/te otsuka.kazuki@googlemail.com
# K00TSUKA@MacBook-Pr
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILSeBj9oNBpr/PqEUFwV+jzR6/8Czd9vUt9nmo9ngDoK otsuka.kazuki@googlemail.com
# supercom3b
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINJ2e5lYXhQZ4Is+mt39AnbIeuAnRm90Mh+Dfv38shOZ otsuka.kazuki@googlemail.com
# supercom3a
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEU7QfTgC9IefWPnyOde+ce/oABFgNXbGSFw4AEPiRyT otsuka.kazuki@googlemail.com
```

# install ssh

sudo apt update

sudo apt install openssh-client

ssh -v

sudo apt install openssh-server

sudo systemctl status ssh

sudo service ssh status
