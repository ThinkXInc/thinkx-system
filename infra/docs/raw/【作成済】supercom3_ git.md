# 【作成済】supercom3: git

_created: 20230510T033706Z / updated: 20260701T055901Z_

Install Git

```
sudo apt install git
```

set user

```
git config --global user.name "kazukiotsuka"
git config --global user.email otsuka.kazuki@googlemail.com
```

set alias

```
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage 'reset HEAD --'
git config --global alias.cancel 'restore --staged .'
git config --global alias.staged 'restore --staged'
```

Generate SSH key

```
cd ~/.ssh
ssh-keygen -t ed25519 -C "otsuka.kazuki@googlemail.com"
Generating public/private ed25519 key pair.
Enter file in which to save the key (/root/.ssh/id_ed25519): id_github
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
```

Your identification has been saved in id_github

Your public key has been saved in id_github

The key fingerprint is:

..

*don't generate the key by the root user. if did, sudo chown 

```
vim ~/.ssh/id_github.pub
```

ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGCJqJU+ovIiWSn+ayxYgkPinfKDpoh8hyes5a9eTRt1 
otsuka.kazuki@googlemail.com

Githubに登録

・Github > Settings > SSH and GPG keys

*分かりやすいようにid_github_supercom3aのように名前をつける

SSH エージェントが起動していること を確認

```
(eval "$(ssh-agent -s)")
```

install keychain

```
sudo apt-get update
sudo apt-get install keychain
```

add to keychain

```
(keychain --eval --agents ssh id_github)
```

* keychain 2.8.5 ~ http://www.funtoo.org

 * Found existing ssh-agent: 4399

SSH_AUTH_SOCK=/tmp/ssh-XXXXXXrTIJdP/agent.4398; export SSH_AUTH_SOCK;

SSH_AGENT_PID=4399; export SSH_AGENT_PID;

 * Adding 1 ssh key(s): /home/kaz/.ssh/id_github

 * ssh-add: Identities added: /home/kaz/.ssh/id_github

<-if failed, check the permission of the key

add ssh config

```
Host github.com
    IdentityFile ~/.ssh/id_github
    User git
    Port 22
```

Connect to Github

```
ssh -T git@github.com
```

Hi kazukiotsuka! You've successfully authenticated, but GitHub does not provide shell access.
