# 【Summary】Podcast Speech dataset

_created: 20241213T033249Z / updated: 20241213T085626Z_

Podcast dataset download urls

podcast ignore.txt skip.txt

podcast dataset 改良プラン

【Summary】tts4 (MeloTTS)

🏃 Train tts4 (Melo)

前処理

ダウンロードするところから全部走らせる

```
cd /src/quantz/processing-server/tts4/podcast
python data.py --speaker 1
```

-> 基本使わない

分割する

```
 python data.py --step2 --step3
```

分割した /wavs内のデータから書き起こす

```
python data.py --transcribe
```

*最初に元のファイルを消すので注意

学習前処理

/disk1/podcast/speaker_1

filter 

/disk1/podcast/speaker_1/ignore.txtとskip.txtからtranscribeされたjsonデータをさらに除外する (transcribeを最初から走らせると何時間もかかる)

```
cd /src/quantz/processing-server/tts4/podcast
python filter.py
```

/disk1/podcast/speaker_1/manifest_podcast_speaker_1_filtered.json
 が作られる

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
python preprocess_text_jp.py --metadata /src/quantz/processing-server/tts4/podcast_speaker_1/metadata_podcast_speaker_1.list --pretrained-config-path /src/quantz/processing-server/tts4/pretrained_checkpoints/JP_moraspeech_config_v9.json
```

*pretrained-config-pathを指定すると適切にspeakerの数を数えてくれる

訓練

run train

```
cd /src/quantz/processing-server
. ./activate_venv_respond.sh
cd tts4/MeloTTS/melo
bash train.sh /src/quantz/processing-server/tts4/jsut_moraspeech_podcast/config.json 1
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
