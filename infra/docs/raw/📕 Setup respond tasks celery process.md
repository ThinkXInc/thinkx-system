# 📕 Setup respond tasks celery process

_created: 20241203T033844Z / updated: 20241211T021811Z_

Run

```
cd /src/quantz/processing-server
. ./activate_venv_respond
export NLTK_DATA=/src/quantz/processing-server/tts4/nltk_data
WORKER_TYPE=respond GPU_ID=0 /src/quantz/processing-server/venv_respond/bin/celery -A tasks_server.run_respond:celery_app worker -l warning --concurrency=1 -Q respond
```

Setup

```
cd /src/quantz/processing-server
git submodule add git@github.com:ThinkXInc/tts4.git
cd tts4
git submodule init
git submodule update --remote
cd ../processing-server
deactivate
python3.9 -m venv venv_respond
. ./venv_respond/bin/activate
cd tts4/MeloTTSX
pip install -U pip
pip install -e .
cd ../tts4
python -m unidic download
```

jptextparser setup

```
cd /src/quantz/processing-server/tts4/jptextparser
git submodule sync
git submodule update --init --recursive
git lfs pull
# install mecab-python3
pip install mecab-python3 pykakasi bson bs4 pymongo mojimoji
# install system mecab
sudo apt install mecab libmecab-dev mecab-ipadic-utf8
# install ipadic
git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
cd mecab-ipadic-neologd
./bin/install-mecab-ipadic-neologd -n
```

【Summary】tts4 (MeloTTS)

jptextparser

load models

```
cd /src/quantz/processing-server/tts4/pretrained_checkpoints
git lfs install
git lfs pull
```

tts test

```
cd /src/quantz/processing-server
. ./venv_respond/bin/activate

cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py     --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_124000_v8.pth     --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_config_v8.json     --text "こんにちは！何かお聞きになりたいこ とはありますか"     --language JP     --output_dir /src/quantz/processing-server/tts4/jsut_moraspeech/out     --speaker JP-moraspeech
```

*MeloTTSがupdateされない場合

```
mv MeloTTSX MeloTTSX.bk
git rm -r --cached MeloTTSX
rm -rf MeloTTSX
git submodule add git@github.com:ThinkXInc/MeloTTSX.git MeloTTSX
```

```
cd /src/quantz/processing-server/tts4
mkdir nltk_data
export NLTK_DATA=/src/quantz/processing-server/tts4/nltk_data
python
import nltk
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')
```

test

```
cd /src/quantz/processing-server/tts4
. ./test.sh
```

or

```
cd /src/quantz/processing-server/tts4
python run_test.py
```

*Boto HTTP module error

```
pip install boto3==1.7.84 botocore==1.10.84 urllib3==2.2.3
pip install --upgrade gradio
pip install --upgrade boto3
```

upgrade 

```

cd /src/quantz/processing-server
. ./activate_venv_respond.sh
pip install --upgrade -r requirements_respond.txt
```

------------------------------

エラーがでたとき

* 以下は整合しなくなるのでrequirements.txtから除外してあるので手動でインストールする

エラーが出ても無視する

torch==2.3.1

torchaudio==2.5.1

torchvision==0.18.0

vllm==0.3.3

vllm-flash-attn==2.5.8.post2

```
pip install torchaudio==2.5.1
pip install torchvision==0.18.0
pip install vllm==0.3.3
pip install vllm-flash-attn==2.5.8.post2
pip install torch==2.3.1
```

torchaudioを入れ直す

```
pip uninstall torchaudio
pip install --no-cache-dir torchaudio==2.5.1 --force-reinstall
```

*OSError: /src/quantz/processing-server/venv_respond/lib/python3.9/site-packages/torchaudio/lib/libtorchaudio.so: undefined symbol: _ZNK3c105Error4whatEv への対処

さらにtorchvisionを入れ直す

```
pip uninstall torch torchvision -y
pip install torch torchvision
```

*
operator torchvision::nms does not existへの対処

この時点でtorchがupgradeされる

```
pip list | grep torch
pip list | grep vllm
pip list | grep triton
pip list | grep xformers
```

torch                             2.5.1

torchaudio                        2.5.1

torchvision                       0.18.0

vllm                              0.3.3

vllm-flash-attn                   2.5.8.post2

triton                            3.1.0

xformers                          0.0.23.post1

------------------------------

test tts inference

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_510000_v9.pth \
    --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_config_v9.json \
    --text "こんにちは！ABCDEFG.アルファベットが読めます" \
    --language JP \
    --output_dir /src/quantz/processing-server/tts4/infer_out/ \
    --speaker JP-moraspeech
```

-> infer_outにファイルが生成されたらdone

Others

Download checkpoints

---

```
scp -r kaz@thinkxinc.comsupercom3b:/src/quantz/processing-server/tts4/pretrained_checkpoints ~/Downloads
```
