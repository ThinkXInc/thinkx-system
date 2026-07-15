# 【Summary】Supercom3b: Setup ASR tools & data

_created: 20231219T023834Z / updated: 20231222T015240Z_

・
reinstall nvidia

・
clone repo and install Nemo

・
transfer data

ssh from supercom3a to 3b
rsync fleurs en, ja
rsync voxpopuli en
rsync train_manifest

install basic tools

essential packages

```
sudo apt-get install -y python3-dev portaudio19-dev libffi-dev libssl-dev libsqlite3-dev wget
```

utilities

```
sudo apt-get install -y screen sox
```

reinstall nvidia cuda

supercom3: install cuda 12.3 2023.Dec

after removing old versions,

wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.3.1/local_installers/cuda-repo-ubuntu2204-12-3-local_12.3.1-545.23.08-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-12-3-local_12.3.1-545.23.08-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2204-12-3-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-3

```
sudo apt-get install -y cuda-drivers
```

A new initrd image has also been created. To revert, please regenerate your

initrd by running the following command after deleting the modprobe.d file:

`/usr/sbin/initramfs -u`

*****************************************************************************

*** Reboot your computer and verify that the NVIDIA graphics driver can   ***

*** be loaded.                                                            ***

*********************************************************************

$ nvidia-smi -l

clone repo and install Nemo

```
cd /src
git clone git@github.com:ThinkXInc/ASR.git
python3 -m venv venv
```

```
sudo apt-get update && sudo apt-get install -y libsndfile1 ffmpeg
pip install Cython
pip install nemo_toolkit['all']
```

*Cythonが見つからないエラー -> 一度 venvを削除し上記をやり直し

transfer data

ssh from supercom3a to 3b

```
ssh supercom3a
cd ~/.ssh
ssh-keygen -t ed25519 -C "otsuka.kazuki@googlemail.com"
vim ~/.ssh/config

Host supercom3b
    HostName 192.168.1.7
    User kaz
    Port 22
    IdentityFile /home/kaz/.ssh/id_kaz
```

```
ssh supercom3b
vim ~/.ssh/authorized_keys  # id_kaz.pubをコピ-
```

```
ssh supercom3b
```

Tokenizers

```
rsync -avz --progress /src/ASR/tokenizers/ kaz@supercom3b:/src/ASR/tokenizers/
```

Fleurs (en, jp) est 200~500GB

```
nohup rsync -avz --progress /disk1/fleurs/data/en_us/ kaz@supercom3b:/disk1/fleurs/data/en_us/

kaz@supercom3:~$ nohup rsync -avz --progress /disk1/fleurs/data/ja_jp/ kaz@supercom3b:/disk1/fleurs/data/ja_jp/
```

VoxPopuli (en) est 200~500GB

```

```

SSD 1 & 2 to Supercom3b
