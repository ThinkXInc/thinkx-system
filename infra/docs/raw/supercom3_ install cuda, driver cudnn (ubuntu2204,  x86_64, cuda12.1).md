# supercom3: install cuda, driver cudnn (ubuntu2204,  x86_64, cuda12.1)

_created: 20230510T020933Z / updated: 20241223T052736Z_

追記: deepspeedはcuda12に対応していないためcuda11.8を入れ直す

このノートでなく 
supercom3: install cuda, driver cudnn (ubuntu2204,  x86_64, cuda11.8)

を参照

https://docs.nvidia.com/cuda/cuda-installation-guide-linux/

Uninstall the old version

```
sudo /usr/local/cuda-X.Y/bin/cuda-uninstaller
```

or

```
sudo rm -rf /usr/local/cuda-X.Y
```

```
sudo apt-get --purge remove cuda
```

```
sudo apt-get purge nvidia-*
```

* Nvidia Driver also should be uninstall. otherwise, driver and cuda may not match.

remove all residual dependencies

```
sudo apt-get remove libnvidia-common-470 libnvidia-common
sudo apt-get autoremove
sudo apt-get autoclean
```

update and upgrade system

```
sudo apt-get update
sudo apt-get upgrade
```

Check if CUDA-capable GPU is available

```
lspci | grep -i nvidia
```

01:00.0 VGA compatible controller: NVIDIA Corporation GA102GL [RTX A5000] (rev a1)

01:00.1 Audio device: NVIDIA Corporation GA102 High Definition Audio Controller (rev a1)

25:00.0 VGA compatible controller: NVIDIA Corporation GA102GL [RTX A5000] (rev a1)

25:00.1 Audio device: NVIDIA Corporation GA102 High Definition Audio Controller (rev a1)

41:00.0 VGA compatible controller: NVIDIA Corporation GA102GL [RTX A5000] (rev a1)

41:00.1 Audio device: NVIDIA Corporation GA102 High Definition Audio Controller (rev a1)

61:00.0 VGA compatible controller: NVIDIA Corporation GA102GL [RTX A5000] (rev a1)

61:00.1 Audio device: NVIDIA Corporation GA102 High Definition Audio Controller (rev a1)

Verify a supported version of Linux

```
uname -m && cat /etc/*release
```

x86_64

DISTRIB_ID=Ubuntu

DISTRIB_RELEASE=22.04

DISTRIB_CODENAME=jammy

DISTRIB_DESCRIPTION="Ubuntu 22.04.2 LTS"

PRETTY_NAME="Ubuntu 22.04.2 LTS"

NAME="Ubuntu"

VERSION_ID="22.04"

VERSION="22.04.2 LTS (Jammy Jellyfish)"

VERSION_CODENAME=jammy

ID=ubuntu

ID_LIKE=debian

HOME_URL="https://www.ubuntu.com/"

SUPPORT_URL="https://help.ubuntu.com/"

BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"

PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"

UBUNTU_CODENAME=jammy

Verify gcc version

```
gcc --version
```

gcc (Ubuntu 11.3.0-1ubuntu1~22.04) 11.3.0

Verify the System has the Correct Kernel Headers 

```
uname -r
```

5.19.0-41-generic

Runfile インストールはパッケージの検証を行いませんが、ドライバの RPM と Deb インストールは、カーネルヘッダーと開発パッケージのバージョンが現在インストールされていない場合、これらのパッケージのインストールを試みます。しかし、これらのパッケージの最新バージョンをインストールしますが、システムが使用しているカーネルのバージョンと一致する場合もあれば、一致しない場合もあります。

CUDAドライバをインストールする前や、カーネルバージョンを変更する際には、正しいバージョンのカーネルヘッダと開発パッケージがインストールされていることを手動で確認するのが最善です。

Download NVIDIA Toolkit

NVIDIA CUDA Toolkit は、

https://developer.nvidia.com/cuda-downloads

で入手できます。

使用しているプラットフォームを選択し、NVIDIA CUDA Toolkitをダウンロードしてください。

以下はUbuntu22.04 x86_64

```
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-ubuntu2204.pin
sudo mv cuda-ubuntu2204.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.1.1/local_installers/cuda-repo-ubuntu2204-12-1-local_12.1.1-530.30.02-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2204-12-1-local_12.1.1-530.30.02-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2204-12-1-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda
```

CUDA Toolkitは、ディストリビューション固有のパッケージ（RPMおよびDebパッケージ）、またはディストリビューションに依存しないパッケージ（ランファイルパッケージ）という2つの異なるインストールメカニズムのいずれかを使用してインストールすることができる。

ディストリビューション非依存型パッケージは、より多くのLinuxディストリビューションで動作するという利点がありますが、ディストリビューションのネイティブパッケージ管理システムを更新することはありません。ディストリビューション固有パッケージは、ディストリビューションのネイティブパッケージ管理システムとのインターフェイスを提供します。可能であれば、ディストリビューション固有のパッケージを使用することが推奨されます。

If succeeded,

*****************************************************************************

*** Reboot your computer and verify that the NVIDIA graphics driver can   ***

*** be loaded.                                                            ***

*****************************************************************************

...

DKMS: install completed.

Setting up nvidia-driver-530 (530.30.02-0ubuntu1) ...

Setting up cuda-drivers-530 (530.30.02-1) ...

Setting up cuda-drivers (530.30.02-1) ...

Setting up cuda-runtime-12-1 (12.1.1-1) ...

Setting up cuda-demo-suite-12-1 (12.1.105-1) ...

Setting up cuda-12-1 (12.1.1-1) ...

Setting up cuda (12.1.1-1) ...

Processing triggers for gnome-menus (3.13.3-11ubuntu1.1) ...

Processing triggers for dbus (1.12.2-1ubuntu1.4) ...

Processing triggers for mime-support (3.60ubuntu1) ...

Processing triggers for desktop-file-utils (0.23-1ubuntu3.18.04.2) ...

Processing triggers for bamfdaemon (0.5.3+18.04.20180207.2-0ubuntu1) ...

Rebuilding /usr/share/applications/bamf-2.index...

Processing triggers for libc-bin (2.27-3ubuntu1.5) ...

Processing triggers for man-db (2.8.3-2ubuntu0.1) ...

Processing triggers for initramfs-tools (0.130ubuntu3.8) ...

update-initramfs: Generating /boot/initrd.img-4.15.0-209-generic

```
sudo reboot
```

Check if installed successfully

```
nvidia-smi -l
```

Wed May 10 12:14:18 2023

+---------------------------------------------------------------------------------------+

| NVIDIA-SMI 530.30.02              Driver Version: 530.30.02    CUDA Version: 12.1     |

|-----------------------------------------+----------------------+----------------------+

| GPU  Name                  Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |

| Fan  Temp  Perf            Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |

|                                         |                      |               MIG M. |

|=========================================+======================+======================|

|   0  NVIDIA RTX A5000                On | 00000000:01:00.0 Off |                  Off |

| 30%   26C    P8                7W / 230W|      5MiB / 24564MiB |      0%      Default |

|                                         |                      |                  N/A |

+-----------------------------------------+----------------------+----------------------+

|   1  NVIDIA RTX A5000                On | 00000000:25:00.0 Off |                  Off |

| 30%   25C    P8                8W / 230W|      5MiB / 24564MiB |      0%      Default |

|                                         |                      |                  N/A |

+-----------------------------------------+----------------------+----------------------+

|   2  NVIDIA RTX A5000                On | 00000000:41:00.0 Off |                  Off |

| 30%   25C    P8                9W / 230W|      5MiB / 24564MiB |      0%      Default |

|                                         |                      |                  N/A |

+-----------------------------------------+----------------------+----------------------+

|   3  NVIDIA RTX A5000                On | 00000000:61:00.0 Off |                  Off |

| 30%   25C    P8                3W / 230W|      5MiB / 24564MiB |      0%      Default |

|                                         |                      |                  N/A |

+-----------------------------------------+----------------------+----------------------+

Install CuDNN

Install Guide

https://docs.nvidia.com/deeplearning/cudnn/install-guide/index.html

Make sure

Driver is installed
CUDA Toolkit is installed
zlib1g is installed

```
sudo apt-get install zlib1g
```

Download cuDNN

https://developer.nvidia.com/rdp/cudnn-download

NVIDIA developerログイン後，Linuxバージョンとアーキテクチャに対応したcuDNNをダウンロード

*以下ubuntu2204-
8.9.1.23
, cuda12.1

lbに転送

```
scp ~/Downloads/cudnn-local-repo-ubuntu2204-8.9.1.23_1.0-1_amd64.deb kaz@supercom3L:/home/kaz/Downloads
```

3a, 3bに転送

```
scp cudnn-local-repo-ubuntu2204-8.9.1.23_1.0-1_amd64.deb  kaz@supercom3a:/home/kaz/Downloads
scp cudnn-local-repo-ubuntu2204-8.9.1.23_1.0-1_amd64.deb  kaz@supercom3b:/home/kaz/Downloads
```

install cuDNN

```
cd /path/to/downloadedfolder
sudo dpkg -i cudnn-local-repo-ubuntu2204-8.9.1.23_1.0-1_amd64.deb
sudo cp /var/cudnn-local-repo-ubuntu2204-8.9.1.23/cudnn-local-E7A7D88D-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get install libcudnn8=8.9.1.23-1+cuda12.1
```

install the developer library

```
sudo apt-get install libcudnn8-dev=8.9.1.23-1+cuda12.1
```

install the code samples

```
sudo apt-get install libcudnn8-samples=8.9.1.23-1+cuda12.1
```

Install NCCL

```
cd ~/Downloads
curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/3bf863cc.pub | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/nvidia-archive-keyring.gpg] https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/ /" | sudo tee /etc/apt/sources.list.d/nvidia-cuda.list
sudo apt-get update
```

```
sudo apt-get install -y libnccl2 libnccl-dev
```

verify

```
dpkg -l | grep nccl
```

ii  libnccl-dev                                2.23.4-1+cuda12.6                           amd64        NVIDIA Collective Communication Library (NCCL) Development Files

ii  libnccl2                                   2.23.4-1+cuda12.6                           amd64        NVIDIA Collective Communication Library (NCCL) Runtime

NCCL test

Download and build

```
cd ~/Downloads
git clone https://github.com/NVIDIA/nccl-tests.git
cd nccl-tests
make MPI=0
```

Compiling  hypercube.cu                        > /home/kaz/Downloads/nccl-tests/build/hypercube.o

Linking  /home/kaz/Downloads/nccl-tests/build/hypercube.o > /home/kaz/Downloads/nccl-tests/build/hypercube_perf

nvlink warning : Skipping incompatible '/usr/lib/x86_64-linux-gnu/librt.a' when searching for -lrt (target: sm_70)

nvlink warning : Skipping incompatible '/usr/lib/x86_64-linux-gnu/librt.a' when searching for -lrt (target: sm_80)

make[1]: Leaving directory '/home/kaz/Downloads/nccl-tests/src'

Run test

```
 ./build/all_reduce_perf -b 8 -e 128M -f 2 -g 2
```
