# 【Summary】tts4 (MeloTTS)

_created: 20241202T014003Z / updated: 20241218T015855Z_

prerequisite

```
python3.9 -c "import bz2"
python3.9 -c "import _lzma"
```

⭐️【Summary】Setup Supercom3a (Main server)

エラーが出る場合Pythonを再インストール

*MeloTTSは下記の手順でmirrorとして作られているので注意

```
cd /src/quantz/processing-server/tts4
git clone git@github.com:myshell-ai/MeloTTS.git
cd /src/quantz/processing-server/tts4/MeloTTS
git remote add MeloTTS git@github.com:ThinkXInc/MeloTTS.git
git push --mirror MeloTTS
git rm -r --cached MeloTTS
git submodule add git@github.com:ThinkXInc/MeloTTS.git MeloTTS
git commit -m "Re-added MeloTTS as a submodule"
git submodule update --init --recursive
```

これでThinkXInc/MeloTTSがprivateにつくられた

setup

```
cd /src/quantz/processing-server
git submodule add git@github.com:ThinkXInc/tts4.git
cd /src/quantz/processing-servertts4
git submodule init
git submodule update --remote
cd /src/quantz/processing-server
python3.9 -m venv venv_respond
. ./venv_respond/bin/activate
cd /src/quantz/processing-server/tts4/MeloTTS
pip install -U pip
pip install -e .
cd /src/quantz/processing-server/tts4/tts4
python -m unidic download
```

setup nltk

```
cd /src/quantz/processing-server/tts4
mkdir nltk_data
export NLTK_DATA=/src/quantz/processing-server/tts4/nltk_data
python
```

```
import nltk
```

```
nltk.download('averaged_perceptron_tagger')
```

```
nltk.download('averaged_perceptron_tagger_eng')
```

```
cd /src/quantz/processing-server/tts4/pretrained_checkpoints
git lfs install
git lfs pull
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

test run

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

models and configs are:

```
:~/.cache/huggingface/hub$ ls
models--bert-base-multilingual-uncased            models--myshell-ai--MeloTTS-French
models--bert-base-uncased                         models--myshell-ai--MeloTTS-Japanese
models--dbmdz--bert-base-french-europeana-cased   models--myshell-ai--MeloTTS-Korean
models--dccuchile--bert-base-spanish-wwm-uncased  models--myshell-ai--MeloTTS-Spanish
models--kykim--bert-kor-base                      models--togethercomputer--Pythia-Chat-Base-7B-v0.16
models--myshell-ai--MeloTTS-Chinese               models--tohoku-nlp--bert-base-japanese-v3
models--myshell-ai--MeloTTS-English               version.txt
```

run

```
cd processing-server
source venv_respond/bin/activate
export NLTK_DATA=/src/quantz/processing-server/tts4/nltk_data python --text "Hello world" --lang en --file ./o.wav
```

verify nltk

```
python
import nltk
nltk.download('averaged_perceptron_tagger')
```

check if melo cli works

```
pip list | grep melotts
```

(venv) kaz@supercom4:/src/quantz/processing-server/tts4/MeloTTS$ pip list | grep melotts

melotts                   0.1.2       /src/quantz/processing-server/tts4/MeloTTS

```
pip show melotts
```

Name: melotts

Version: 0.1.2

Summary:

Home-page:

Author:

Author-email:

License:

Location: /src/quantz/processing-server/tts4/venv/lib/python3.9/site-packages

Editable project location: /src/quantz/processing-server/tts4/MeloTTS

Requires: anyascii, cached_path, cn2an, eng_to_ipa, fugashi, g2p_en, g2pkk, gradio, gruut, inflect, jamo, jieba, langid, librosa, loguru, mecab-python3, num2words, pydub, pykakasi, pypinyin, tensorboard, torch, torchaudio, tqdm, transformers, txtsplit, unidecode, unidic, unidic_lite

Required-by:

```
melo --help
```

Usage: melo [OPTIONS] TEXT OUTPUT_PATH

Options:

  -f, --file                      Text is a file

  -l, --language [EN|ES|FR|ZH|JP|KR]

                                  Language, defaults to English

  -spk, --speaker [EN-Default|EN-US|EN-BR|EN_INDIA|EN-AU]

                                  Speaker ID, only for English, leave empty

                                  for default, ignored if not English. If

                                  English, defaults to "EN-Default"

  -s, --speed FLOAT               Speed, defaults to 1.0

  -d, --device TEXT               Device, defaults to auto

  --help                          Show this message and exit.

inference

```
cd /src/quantz/processing-server
git submodule add git@github.com:ThinkXInc/tts4.git
python3.9 -m venv venv_respond
```

train

jsut_moraspeech

generate metadata

```
cd /src/quantz/processing-server
. ./activate_venv_respond.sh
cd tts4
python generate_train_metadata --dataset {dataset}
```

preprocess

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python preprocess_text_jp.py --metadata /src/quantz/processing-server/tts4/jsut_moraspeech/metadata_jsut_moraspeech.list
```

run train

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
bash train.sh /src/quantz/processing-server/tts4/jsut_moraspeech/config.json 1
```

*save and upload trained file

```
epoch=714000
version=9

cp /src/quantz/processing-server/tts4/MeloTTS/melo/logs/jsut_moraspeech_podcast/G_${epoch}.pth \
   /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_v${version}_${epoch}.pth

cp /src/quantz/processing-server/tts4/MeloTTS/melo/logs/jsut_moraspeech_podcast/config.json \
   /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_v${version}_config.json

cd /src/quantz/processing-server/tts4/pretrained_checkpoints

git lfs track JP_v${version}_${epoch}.pth
git lfs track JP_v${version}_config.json

git add -f JP_v${version}_${epoch}.pth
git add -f JP_v${version}_config.json

git add .gitattributes
git commit -m "Save JP_v${version}_${epoch}"

git push origin master
```

*pull 

```
git pull origin master
cd /src/quantz/processing-server/tts4/pretrained_checkpoints
``
```

jsut_moraspeech_podcast

logs/jsut_moraspeech_v9

を複製し logs/jsut_moraspeech_podcastに名前を変える

途中再開したいのでconfig.json でなく config_restart.json を指定する．

```
cd /src/quantz/processing-server
. ./activate_venv_respond
cd tts4/MeloTTS/melo
```

```
bash train.sh /src/quantz/processing-server/tts4/jsut_moraspeech_podcast/config_restart.json 1
```

-> JP_checkpoint.pthでなく途中のものがloadされている様子

```
2024-12-17 03:13:51,969	jsut_moraspeech_podcast	INFO	Loaded checkpoint '/home/kaz/.cache/cached_path/73ad3d5a37c82356ed81630b0a435b4b376ca49523854fe2b8302609fd71c193.133b77b9d9162e348486a0a0778fa47d726930e3ec12ea5e2684c0c919743a65' (iteration 0)
2
```

＊ 途中再開の方法 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

再開前のkeyを jsut_moraspeech とする

再開後のkeyを podcast_speaker_1 とする

再開前の 
logs/jsut_moraspeech
 フォルダをコピーし 
logs/podcast_speaker_1
 に名前だけ変える <- POINT 1

*中身のconfig.jsonは使わないので気にしない

tts4/podcast_speaker_1
/config.json

を用意する．この時
学習済みpthのパスの項目を消す
 <- POINT 2

あとは

bash train.sh /src/quantz/processing-server/tts4/podcast_speaker_1/config.json 1

を実行すればlogs/podcast_speaker_1にコピーされた最後のpthファイルをロードして再開する

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

podcast

---

/disk1/podcast/speaker_1

filter 

```
cd /src/quantz/processing-server/tts4/podcast
python filter.py
```

/disk1/podcast/speaker_1/manifest_podcast_speaker_1_filtered.json created

generate manifest

```
cd /src/quantz/processing-server
. ./activate_venv_respond.sh
cd tts4
python generate_train_metadata.py --dataset podcast_speaker_1
```

```
cp /disk1/podcast/speaker_1/metadata.list /src/quantz/processing-server/tts4/podcast_speaker_1/metadata_podcast_speaker_1.list
```

preprocess

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python preprocess_text_jp.py --metadata /src/quantz/processing-server/tts4/podcast_speaker_1/metadata_podcast_speaker_1.list --pretrained-config-path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_config_v9.json --pretrained-checkpoint-path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_714000_v9.pth
```

run train

```
cd /src/quantz/processing-server
. ./activate_venv_respond.sh
cd tts4/MeloTTS/melo
bash train.sh /src/quantz/processing-server/tts4/podcast_speaker_1/config.json 1
```

----

jsut

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python preprocess_text.py --metadata /disk1/jsut/metadata.list
```

moraspeech

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python preprocess_text.py --metadata /disk1/moraspeech/metadata.list
```

csj

```
cd /src/quantz/processing-server
. ./activate_venv_respond.sh
python tts4/generate_train_metadata_csj.py
```

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python preprocess_text.py --metadata /disk1/csj/metadata.list
```

/disk1/csj/wavs/noncore/A01F0001_0.wav|JP-csj-72|JP|マズハッピョウハサイショニカンタンニエコーロケーションキノウニツイテセツメイイタシマスソノノチコレマデオコナッテキマシタコウモリノセイシジョウタイニオケルエコーロケーションサウンドニセツメイシ|_ m a z u h a q p i y o u h a s a i sh o n i k a N t a N n i e k o r o k e sh o N k i n o u n i ts u i t e s e ts u m e i i t a sh i m a s u s o n o n o ch i k o r e m a d e o k o n a q t e k i m a sh i t a k o u m o r i n o s e i sh i j o u t a i n i o k e r u e k o r o k e sh o N s a u N d o n i s e ts u m e i sh i _|0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0|1 2 2 3 2 2 1 2 3 2 2 3 3 2 4 3 3 4 2 1 3 2 2 2 3 3 4 2 2 2 2 2 4 2 2 1 2 2 2 1 2 4 2 7 2 3 2 2 1 3 3 3 3 3 3 3 3 3 2 2 2 2 2 1

/disk1/jsut/metadata.list.cleaned

/disk1/moraspeech/metadata.list.cleaned

/disk1/jsut/val.list

/disk1/moraspeech/val.list

/disk1/jsut/train.list

/disk1/moraspeech/train.list

/disk1/jsut/config.json

/disk1/moraspeech/config.json

generated

Combined DATA (CSJ, JSUT, Moraspeech)

試行錯誤した結果，まず全部合わせたデータで事前学習をするとともにspeaker idの割り当てを適切に行い，その後特定のspeaker, 特に JP_jsut, JP_moraspeechで

    
"n_speakers"
: 
257
,

    
"cleaned_text"
: 
true
,

    
"spk2id"
: {

      
"JP"
: 
0
,

      
"JP-csj-72"
: 
256

    }

注意点:

JP_checkpointは256名の既存のspeakersで学習されている．JP: 0のみがconfigには表示されているが，既存の学習を壊さないために256番から新たにspeakerを追加する必要がある．例えば上の設定はJP-csj-72がtrain.listに含まれていて対応するデータさえあれば動く．

このようにするために preprocess_text_
jp.pyを特別に用意した
．これはJP_checkpoint.jsonまたは指定した学習済みデータの設定から既存のspeakerを考慮してcsj_jsut_moraspeech/config.jsonを生成する．

combine

```
cd /src/quantz/processing-server/tts4
python combine_jp_metadata.py
```

preprocess

```
cd /src/quantz/processing-server/tts4/MeloTTSX/melo
python preprocess_text_jp.py --metadata  /src/quantz/processing-server/tts4/csj_jsut_moraspeech/metadata_csj_jsut_moraspeech.list
```

* またはmetadata_csj_jsut_moraspeech.cleanが生成されている場合は 
--no-clean
 をつけると飛ばしてconfigだけ作る 付けないと14分かかる

train (pretrain with all)

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
bash train.sh /src/quantz/processing-server/tts4/csj_jsut_moraspeech/config.json 1
```

train (jsut speaker only)

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
bash train.sh /src/quantz/processing-server/tts4/csj_jsut_moraspeech/config_jsut.json 1
```

train (moraspeech speaker only)

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
bash train.sh /src/quantz/processing-server/tts4/csj_jsut_moraspeech/config_moraspeech.json 1
```

copy trained pth file

```
cp /src/quantz/processing-server/tts4/MeloTTS/melo/logs/csj_jsut_moraspeech/G_.pth 
/src/quantz/processing-server/tts4/pretrained_checkpoints/JP_all_v4_.pth
```

infer while training

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/MeloTTS/melo/logs/csj_jsut_moraspeech/G_0.pth \
    --config_path /src/quantz/processing-server/tts4/csj_jsut_moraspeech/config.json \
    --text "今夜は星空が輝き大雪が降るでしょうね" \
    --language JP \
    --speaker JP-moraspeech \
    --output_dir /src/quantz/processing-server/tts4/csj_jsut_moraspeech/out
```

infer (all)

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_all_v4_.pth \
    --config_path /src/quantz/processing-server/tts4/csj_jsut_moraspeech/config.json \
    --text "今夜は星空が輝き大雪が降るでしょうね" \
    --language JP \
    --speaker JP-moraspeech
    --output_dir /src/quantz/processing-server/tts4/csj_jsut_moraspeech/out
```

---

test

JP_checkpoint.pth

```
python infer.py     --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_checkpoint.pth     --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_config.json     --text "今夜は星空が輝き大雪が降るでしょうね"     --language JP     --speaker JP     --output_dir /src/quantz/processing-server/tts4/JP_checkpoint/out
```

と同じように

csj_jsut_moraspeech

```
python infer.py     --ckpt_path /src/quantz/processing-server/tts4/MeloTTS/melo/logs/csj_jsut_moraspeech/G_0.pth     --config_path /src/quantz/processing-server/tts4/csj_jsut_moraspeech/config.json     --text "今夜は星空が輝き大雪が降るでしょうね"     --language JP     --speaker JP     --output_dir /src/quantz/processing-server/tts4/csj_jsut_moraspeech/out
```

-> JP:0 を維持して学習しているのでちゃんと聞こえれば話者を分離して学習できている

----

Train

moraspeech v2 (starts from JP_checkpoint)

```
bash train.sh /disk1/moraspeech/config_v2_from_JP_checkpoint.json 1
```

moraspeech v1 (starts from general pretrained checkpoint)

```
bash train.sh /disk1/moraspeech/config_v1.json 1
```

jsut

```
cd tts4/MeloTTS/melo
bash train.sh /disk1/jsut/config.json 1
```

*1 is num of gpu

=> adjust batch size  in config.json utilizing GPU RAM

[v3]  csj -> jsut -> moraspeech

1

csj (on JP_checkpoint.pth)

```
cd tts4/MeloTTS/melo
bash train.sh /disk1/csj/config_v3_on_JP_checkpoint.json 1
```

2

jsut (on csj)

```
cd tts4/MeloTTS/melo
bash train.sh /disk1/jsut/config_v3_on_csj.json 1
```

3

moraspeech (on jsut v3)

```
cd tts4/MeloTTS/melo
bash train.sh /disk1/jsut/config_v3_on_csj_jsut.json 1
```

*    
"pretrained_checkpoint_path"
: 
"/src/quantz/processing-server/tts4/pretrained_checkpoints/JP_jsut_v3_pth"

melo/logs/jsut/

config.json

D_36000.pth

DUR_36000.pth

G_36000.pth

```
export NLTK_DATA=/src/quantz/processing-server/tts4/nltk_data
```

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py --text "こんにちは赤ちゃん" -l JP -m /src/quantz/processing-server/tts4/MeloTTS/melo/logs/jsut/G_37000.pth -o /src/quantz/processing-server/tts4/infer_out -c /src/quantz/processing-server/tts4/MeloTTS/melo/logs/jsut/config.json
```

JP_checkpoint

```
cd /src/quantz/processing-server/
. ./venv_respond/bin/activate
cd tts4/MeloTTS/melo
python infer.py --text "今夜は星空が輝き大雪が降るでしょう" -l JP -m /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_checkpoint.pth -c /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_config.json -o /src/quantz/processing-server/tts4/infer_out
```

moraspeech

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py --text "今夜は星空が輝き大雪が降るでしょう" -l JP -m /src/quantz/processing-server/tts4/MeloTTS/melo/logs/moraspeech/G_177000.pth -o /src/quantz/processing-server/tts4/infer_out -c /src/quantz/processing-server/tts4/MeloTTS/melo/logs/moraspeech/config.json
```

csj

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py --text "今夜は星空が輝き大雪が降るでしょう" -l JP -m /src/quantz/processing-server/tts4/MeloTTS/melo/logs/csj/G_30000.pth -o /src/quantz/processing-server/tts4/infer_out -c /src/quantz/processing-server/tts4/MeloTTS/melo/logs/csj/config.json
```

moraspeech v1 90000

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_90000_v1.pth \
    --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_config_v1.json \
    --text "今夜は星空が輝き大雪が降るでしょうね" \
    --language JP \
    --output_dir /src/quantz/processing-server/tts4/infer_out
```

moraspeech v2 185000

*JP_checkpointで開始していなかった可能性が高い

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_182000_v2.pth \
    --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_config_v2.json \
    --text "今夜は星空が輝き大雪が降るでしょうね" \
    --language JP \
    --output_dir /src/quantz/processing-server/tts4/infer_out
```

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_182000_v2.pth \
    --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_config_v2.json \
    --text "私の名前はRelaです。" \
    --language JP \
    --output_dir /src/quantz/processing-server/tts4/infer_out
```

**EN_hf (The default latest model highest quality)

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/EN_hf_checkpoint.pth \
    --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/EN_hf_config.json \
    --text "Did you ever hear a folk tale about a giant turtle?" \
    --language EN \
    --output_dir /src/quantz/processing-server/tts4/infer_out \
    --speaker EN-US
```

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/EN_hf_checkpoint.pth \
    --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/EN_hf_config.json \
    --text "Hi. My name is Rela." \
    --language EN \
    --output_dir /src/quantz/processing-server/tts4/infer_out \
    --speaker EN-US
```

EN_NEWEST

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/EN_NEWEST_checkpoint.pth \
    --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/EN_NEWEST_config.json \
    --text "Did you ever hear a folk tale about a giant turtle?" \
    --language EN \
    --output_dir /src/quantz/processing-server/tts4/infer_out
```

EN_V2 (speaker: EN-US)

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/EN_V2_checkpoint.pth \
    --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/EN_V2_config.json \
    --text "Did you ever hear a folk tale about a giant turtle?" \
    --language EN \
    --output_dir /src/quantz/processing-server/tts4/infer_out \
    --speaker EN-US
```

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --text "Did you ever hear a folk tale about a giant turtle?" \
    --language EN \
    --output_dir /src/quantz/processing-server/tts4/infer_out \
    --speaker EN-US
```

EN

```
cd /src/quantz/processing-server/tts4/MeloTTS/melo
python infer.py \
    --ckpt_path /src/quantz/processing-server/tts4/pretrained_checkpoints/EN_checkpoint.pth \
    --config_path /src/quantz/processing-server/tts4/pretrained_checkpoints/EN_config.json \
    --text "Did you ever hear a folk tale about a giant turtle?" \
    --language EN \
    --output_dir /src/quantz/processing-server/tts4/infer_out
```

*
infer.pyを下記のように変更が必要

```
@click.command()
@click.option('--ckpt_path', '-m', type=str, default=None, help="Path to the checkpoint file")
@click.option('--config_path', '-c', type=str, default=None, help="Path to the config file")
@click.option('--text', '-t', type=str, default=None, help="Text to speak")
@click.option('--language', '-l', type=str, default="EN", help="Language of the model")
@click.option('--output_dir', '-o', type=str, default="outputs", help="Path to the output")
def main(ckpt_path, config_path, text, language, output_dir):
    if ckpt_path is None:
        raise ValueError("The model_path must be specified")
    
    if config_path is None:
        raise ValueError("The config_path must be specified")
    #config_path = os.path.join(os.path.dirname(ckpt_path), 'config.json')
    model = TTS(language=language, config_path=config_path, ckpt_path=ckpt_path)
    
    for spk_name, spk_id in model.hps.data.spk2id.items():
        save_path = f'{output_dir}/{spk_name}/output.wav'
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        model.tts_to_file(text, spk_id, save_path)
```

Pretrained model

config.jsonに含めたトレーニングスクリプトを実行すると、ゼロからトレーニングを開始するのではなく、事前学習済みのモデルをベースとして使用することになります。

説明：

train.pyscriptには、事前学習済みのモデルの読み込みを処理するセクションがあります。

```

python

コードをコピー

pretrain_G, pretrain_D, pretrain_dur = load_pretrain_model() hps.pretrain_G = hps.pretrain_G or pretrain_G hps.pretrain_D = hps.pretrain_D or pretrain_D hps.pretrain_dur = hps.pretrain_dur or pretrain_dur if hps.pret rain_G: utils.load_checkpoint(hps.pretrain_G, net_g, None, skip_optimizer=True) if hps.pretrain_D: utils.load_checkpoint(hps.pretrain_D, net_d, None, skip_optimizer=True) if net_ net_dur_disc is not None: net_dur_disc = DDP(net_dur_disc, device_ids=[rank], find_unused_parameters=True) if hps.pretrain_dur: utils.load_checkpoint(hps.pretrain_dur, net_dur_disc, None, skip_optimizer=True)

```

以下がその処理内容です。

1. デフォルトの事前学習済みモデルの読み込み：

 - 関数load_pretrain_model()は、指定されたURLからデフォルトの事前学習済みモデル（G.pth、D.pth、DUR.pth）をダウンロードします。

```

PRETRAINED_MODELS = {
    'G.pth': 'https://myshell-public-repo-host.s3.amazonaws.com/openvoice/basespeakers/pretrained/G.pth',
    'D.pth': 'https://myshell-public-repo-host.s3.amazonaws.com/openvoice/basespeakers/pretrained/D.pth',
    'DUR.pth': 'https://myshell-public-repo-host.s3.amazonaws.com/openvoice/basespeakers/pretrained/DUR.pth',
}
```

 - これらのモデルは言語に依存せず、トレーニングのデフォルトの開始点として使用されます。

2. 事前学習済みモデルのハイパーパラメータへの割り当て：

 - スクリプトは、hps.pretrain_G、hps.pretrain_D、hps.pretrain_durがハイパーパラメータに設定されているかどうかを確認します（config.jsonから読み込まれます）。

 - 設定されていない場合（config.jsonの場合）、load_pretrain_model()によって読み込まれたモデルがデフォルトで使用されます。

3. 事前学習済みモデルの読み込み：

スクリプトは、トレーニングを開始する前に、これらの事前学習済みモデル（net_g、net_d、net_dur_disc）をネットワークに読み込みます。

JPモデルのトレーニング時に使用される事前学習済みモデルは？

JP（日本語）モデルをトレーニングする際には、デフォルトで用意されている事前学習済みモデルを使用します。これらのモデルは、特定の言語に特化していないモデルです。これらのモデルは、異なる言語間のトレーニングにおける一般的な出発点となります。

特定の事前学習済みモデルを出発点として使用する方法

特定の事前学習済みモデルを出発点として使用したい場合（例えば、日本語に特化した事前学習済みモデルを使用したい場合）、以下の手順に従います。

1. config.jsonで事前学習済みモデルのパスを指定します。

 config.jsonファイルに、ルートレベルのpretrain_G、pretrain_D、pretrain_duratキーを含めることで、特定の事前学習済みモデルのパスを追加します。 例：

  「/path/to/your/specific/*.pth」を特定の事前学習済みモデルの実際のファイルパスに置き換えてください。

```
{
  "pretrain_G": "/path/to/your/specific/G.pth",
  "pretrain_D": "/path/to/your/specific/D.pth",
  "pretrain_dur": "/path/to/your/specific/DUR.pth",
  ...
}
```

2. スクリプトがこれらのモデルを使用していることを確認する：

  config.jsonでこれらのパスを指定すると、論理和のため、スクリプトはデフォルトの事前学習済みモデルではなく、それらを使用します。

  hps.pretrain_Gisが設定されている場合（つまり、Noneまたは空ではない場合）、指定されたモデルパスが使用されます。それ以外の場合、pretrain_Gfrom load_pretrain_model()がデフォルトになります。

3. 必要に応じてスクリプトを修正する：

   ゼロからトレーニングを開始したい場合は、これらのハイパーパラメータを None に設定するか、不要な場合は事前学習済みモデルの読み込みを回避するようにスクリプトを修正することで、事前学習済みモデルの読み込みをスクリプトから防止することができます。

   例えば、代入を修正して None を明示的に確認することができます。

   その後、config.json で明示的に設定することができます。

   この方法により、スクリプトは事前学習済みのモデルを使用しないことを認識し、ゼロから学習を開始します。

まとめ：

- デフォルトでは、トレーニングスクリプトは事前学習済みのモデル（G.pth、D.pth、DUR.pth）を起点として使用します。

- これらのモデルは言語固有のものではなく、一般的な事前学習済みモデルです。

- 特定の事前学習済みモデル（日本語固有のモデルなど）を使用するには、config.jsonでpretrain_G、pretrain_D、pretrain_durのキーを使用して、これらのモデルへのパスを指定します。

- ゼロから学習を開始するには、config.jsonでこれらのキーをnullに設定し、必要に応じてスクリプトを調整して、デフォルトの事前学習済みモデルが読み込まれないようにします。

追加の注意事項：

- 事前学習済みモデルと言語：日本語やその他の言語に特化した事前学習済みモデルをお持ちの場合は、それらを使用することで学習効率とモデルのパフォーマンスが大幅に向上します。

- スクリプトの修正：学習スクリプトを修正する際は注意が必要です。予期せぬエラーを防ぐため、変更した部分が他のコードベースと互換性があることを確認してください。

- チェックポイントとトレーニングの再開：スクリプトは、モデルディレクトリ（hps.model_dir）内の既存のチェックポイントからトレーニングを再開しようとします。新たにトレーニングを開始する場合は、このディレクトリが適切に管理されていることを確認してください。

これらの手順に従うことで、トレーニングを最初から行うか、特定の事前トレーニング済みのモデルを起点として使用するかを制御することができます。
