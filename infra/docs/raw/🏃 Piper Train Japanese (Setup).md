# 🏃 Piper Train Japanese (Setup)

_created: 20240111T080008Z / updated: 20240112T021718Z_

Dataset / Phoneme

Espeak-NG Languages / Phonemes

次の形式のcsvを用意すれば良い

```
wavs/speaker1audio1.wav|speaker1|This is what the first speaker says.
```

トランスクリプトはひらがなまたはカタカナで良い

https://github.com/rhasspy/piper/blob/master/TRAINING.md

音素体系はEspeak がひらがなまたはカタカナから変換

Setup

```
sudo apt-get install espeak-ng
```

Linux

Supercom3a: Install Python 3.8.12

```
python3.8 -m venv venv
. ./venv/bin/activate
pip3 install --upgrade pip
pip3 install --upgrade wheel setuptools
pip3 install -e .
```

-> 3.8ではpiper-phonemizeがnot found

-> 3.9

```
python3 -m venv venv
. ./venv/bin/activate
pip3 install --upgrade pip
pip3 install --upgrade wheel setuptools
pip3 install -e .
```

```
pip install -U torchmetrics==0.11.4
```

```
python -m piper_train
```

Docker

run docker

```
cd /path/to/tts2
docker build -t piper .
docker run -v /src/neuravoice/processing-server/tts2:/tts2 -it piper
```

*pytorch-lightning 2 が入っているのでDockerfile修正必要

```
RUN pip3 install \
    'pytorch-lightning==1.7.7'
```

run build_monotonic_
align.sh
 manually

```
root@c9922e71253e:/workspace# cd /tts2
root@c9922e71253e:/tts2# cd piper/src/python
root@c9922e71253e:/tts2/piper/src/python# . ./venv/bin/activate
(venv) root@c9922e71253e:/tts2/piper/src/python# cd piper_train
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train# cd vits/
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train/vits# cd monotonic_align/
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train/vits/monotonic_align# mkdir -p monotonic_aligh
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train/vits/monotonic_align# cythonize -i core.pyx
running build_ext
building 'piper_train.vits.monotonic_align.core' extension
creating /tts2/piper/src/python/tmpc__rtsc1/tts2
creating /tts2/piper/src/python/tmpc__rtsc1/tts2/piper
creating /tts2/piper/src/python/tmpc__rtsc1/tts2/piper/src
creating /tts2/piper/src/python/tmpc__rtsc1/tts2/piper/src/python
creating /tts2/piper/src/python/tmpc__rtsc1/tts2/piper/src/python/piper_train
creating /tts2/piper/src/python/tmpc__rtsc1/tts2/piper/src/python/piper_train/vits
creating /tts2/piper/src/python/tmpc__rtsc1/tts2/piper/src/python/piper_train/vits/monotonic_align
gcc -pthread -B /opt/conda/compiler_compat -Wl,--sysroot=/ -Wsign-compare -DNDEBUG -g -fwrapv -O3 -Wall -Wstrict-prototypes -fPIC -I/opt/conda/include/python3.8 -c /tts2/piper/src/python/piper_train/vits/monotonic_align/core.c -o /tts2/piper/src/python/tmpc__rtsc1/tts2/piper/src/python/piper_train/vits/monotonic_align/core.o
gcc -pthread -shared -B /opt/conda/compiler_compat -L/opt/conda/lib -Wl,-rpath=/opt/conda/lib -Wl,--no-as-needed -Wl,--sysroot=/ /tts2/piper/src/python/tmpc__rtsc1/tts2/piper/src/python/piper_train/vits/monotonic_align/core.o -o /tts2/piper/src/python/piper_train/vits/monotonic_align/core.cpython-38-x86_64-linux-gnu.so
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train/vits/monotonic_align# mv core*.so monotonic_align/
mv: cannot move 'core.cpython-38-x86_64-linux-gnu.so' to 'monotonic_align/': Not a directory
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train/vits/monotonic_align# cd ..
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train/vits# cd ..
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train# mv core*.so monotonic_align/
mv: cannot stat 'core*.so': No such file or directory
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train# cd ..
(venv) root@c9922e71253e:/tts2/piper/src/python# mv core*.so monotonic_align/
mv: cannot stat 'core*.so': No such file or directory
(venv) root@c9922e71253e:/tts2/piper/src/python# cd piper_train/vits/monotonic_align/
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train/vits/monotonic_align# ls
Makefile     core.c                               core.pyx         setup.py
__init__.py  core.cpython-38-x86_64-linux-gnu.so  monotonic_aligh
(venv) root@c9922e71253e:/tts2/piper/src/python/piper_train/vits/monotonic_align#
```

-> align aligh typo 注意

```
cd piper/src/python
python3.9 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade pip
pip3 install --upgrade wheel setuptools
pip3 install -e .
```

fix: ImportError: cannot import name '_compare_version' from 'torchmetrics.utilities.imports'

```
pip3 install pytorch-lightning==1.7.7
pip3 install torchmetrics==0.11.4
```

Run

Run piper_train

```
$ docker run -v /src/neuravoice/processing-server/tts2:/tts2 -it piper
# cd /tts2/piper/src/python/
# . ./venv/bin/activate
```

```
(venv) root@7013a9f63727:/tts2/piper/src/python# python -m piper_train
```
