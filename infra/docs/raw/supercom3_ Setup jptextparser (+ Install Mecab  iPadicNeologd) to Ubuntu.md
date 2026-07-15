# supercom3: Setup jptextparser (+ Install Mecab  iPadicNeologd) to Ubuntu

_created: 20240119T010347Z / updated: 20240119T022803Z_

Clone jptextparser (and nlpmodel submodule)

```
git submodule add git@github.com:ThinkXInc/jptextparser.git
cd jptextparser
git submodule sync
git submodule update --init --recursive
```

Install python dependencies

```
pip install mecab-python3 pykakasi bson bs4 pymongo mojimoji
```

Install mecab ipadic necessities

```
sudo apt install mecab libmecab-dev mecab-ipadic-utf8
```

Install mecab ipadic-neologd

```
git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
cd mecab-ipadic-neologd
./bin/install-mecab-ipadic-neologd -n
```

[install-mecab-ipadic-NEologd] : Start..

[install-mecab-ipadic-NEologd] : Check the existance of libraries

[install-mecab-ipadic-NEologd] :     find => ok

[install-mecab-ipadic-NEologd] :     sort => ok

[install-mecab-ipadic-NEologd] :     head => ok

[install-mecab-ipadic-NEologd] :     cut => ok

[install-mecab-ipadic-NEologd] :     egrep => ok

[install-mecab-ipadic-NEologd] :     mecab => ok

[install-mecab-ipadic-NEologd] :     mecab-config => ok

[install-mecab-ipadic-NEologd] :     make => ok

[install-mecab-ipadic-NEologd] :     curl => ok

[install-mecab-ipadic-NEologd] :     sed => ok

[install-mecab-ipadic-NEologd] :     cat => ok

[install-mecab-ipadic-NEologd] :     diff => ok

[install-mecab-ipadic-NEologd] :     tar => ok

[install-mecab-ipadic-NEologd] :     unxz => ok

[install-mecab-ipadic-NEologd] :     xargs => ok

[install-mecab-ipadic-NEologd] :     grep => ok

[install-mecab-ipadic-NEologd] :     iconv => ok

[install-mecab-ipadic-NEologd] :     patch => ok

[install-mecab-ipadic-NEologd] :     which => ok

[install-mecab-ipadic-NEologd] :     file => ok

[install-mecab-ipadic-NEologd] :     openssl => ok

[install-mecab-ipadic-NEologd] :     awk => ok

[install-mecab-ipadic-NEologd] : mecab-ipadic-NEologd is already up-to-date

[install-mecab-ipadic-NEologd] : mecab-ipadic-NEologd will be install to /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd

[install-mecab-ipadic-NEologd] : Make mecab-ipadic-NEologd

[make-mecab-ipadic-NEologd] : Start..

[make-mecab-ipadic-NEologd] : Check local seed directory

[make-mecab-ipadic-NEologd] : Check local seed file

[make-mecab-ipadic-NEologd] : Check local build directory

[make-mecab-ipadic-NEologd] : create /src/mecab-ipadic-neologd/libexec/../build

[make-mecab-ipadic-NEologd] : Download original mecab-ipadic file

[make-mecab-ipadic-NEologd] : Try to access to https://ja.osdn.net

[make-mecab-ipadic-NEologd] : Try to download from https://ja.osdn.net/frs/g_redir.php?m=kent&f=mecab%2Fmecab-ipadic%2F2.7.0-20070801%2Fmecab-ipadic-2.7.0-20070801.tar.gz

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current

                                 Dload  Upload   Total   Spent    Left  Speed

  0     0    0     0    0     0      0      0 --:--:--  0:00:17 --:--:--     0

  9 11.6M    9 1088k    0     0  11811      0  0:17:13  0:01:34  0:15:39 16283

...

[install-mecab-ipadic-NEologd] : Do you want to install mecab-ipadic-NEologd? Type yes or no.

yes

[install-mecab-ipadic-NEologd] : Install completed.

[install-mecab-ipadic-NEologd] : When you use MeCab, you can set '/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd' as a value of '-d' option of MeCab.

[install-mecab-ipadic-NEologd] : Usage of mecab-ipadic-NEologd is here.

Usage:

    $ 
mecab -d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd ...

[install-mecab-ipadic-NEologd] : Finish..

[install-mecab-ipadic-NEologd] : Finish..
