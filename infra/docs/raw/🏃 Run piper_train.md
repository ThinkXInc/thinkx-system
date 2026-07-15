# 🏃 Run piper_train

_created: 20240112T012328Z / updated: 20240210T082403Z_

概要

sample

```
python3 -m piper_train \
    --dataset-dir /path/to/training_dir/ \
    --accelerator 'gpu' \
    --devices 1 \
    --batch-size 32 \
    --validation-split 0.0 \
    --num-test-examples 0 \
    --max_epochs 10000 \
    --resume_from_checkpoint /path/to/lessac/epoch=2164-step=1355540.ckpt \
    --checkpoint-epochs 1 \
    --precision 32
```

より大きな音声モデルを学習させるには--quality highを使います（音は良くなりますが、かなり遅くなります）。

検証分割（5% = 0.05）とテスト例の数は、特定のデータセットに合わせて調整できる。微調整のために、ターゲットデータセットが非常に小さいため、これらはしばしば0に設定されます。

バッチ・サイズを正しく設定するのは難しい。GPUのvRAMサイズ、モデルの品質/サイズ、データセット中の最長文の長さに依存します。piper_trainの-max-phoneme-ids <N>引数は、N個以上の音素idを持つ文を削除します。実際には、-batch-size 32と-max-phoneme-ids 400を使用すると、24GBのvRAM（RTX 3090/4090）で動作します。

複数話者の微調整

マルチスピーカーモデルをトレーニングする場合、--resume_from_checkpointの代わりに--resume_from_single_speaker_checkpointを使います
。これは、マルチスピーカーモデルを一からトレーニングするよりもはるかに速くなります。

⭐️ Run command

In supercom3

```
cd /src/neuravoice/processing-server/tts2/piper/src/python/piper_train
```

* need to be in /piper_train

resume from kusal

```
python3 -m piper_train \
    --dataset-dir /src/neuravoice/processing-server/tts2/train_data/ \
    --accelerator 'gpu' \
    --devices 1 \
    --batch-size 64 \
    --max-phoneme-ids 400 \
    --validation-split 0.0 \
    --num-test-examples 0 \
    --max_epochs 10000 \
    --resume_from_single_speaker_checkpoint /src/neuravoice/processing-server/tts2/pretrained_model/en-us_kusal_medium_epoch=2652-step=1953828.ckpt \
    --checkpoint-epochs 1 \
    --precision 32
```

resume from any train data

```
python3 -m piper_train \
    --dataset-dir /src/neuravoice/processing-server/tts2/train_data/ \
    --accelerator 'gpu' \
    --devices 1 \
    --batch-size 64 \
    --max-phoneme-ids 400 \
    --validation-split 0.0 \
    --num-test-examples 0 \
    --max_epochs 10000 \
    --resume_from_single_speaker_checkpoint /src/neuravoice/processing-server/tts2/train_data/lightning_logs/version_3/checkpoints/epoch=2-step=2310.ckpt \
    --checkpoint-epochs 1 \
    --precision 32
```

* batch-size 32で20GB程度のRAM -> 64

*devices 2 または 0,1 ではエラー -> 1

Run Tensorboard

remote

```
sshs supercom3a
cd tts2
. ./tensorboard.sh
```

local

```
cd tts2
. ./local_tensorboard.sh
```

Test

x setup piper_phonemize 
https://github.com/rhasspy/piper-phonemize/

```
wget https://github.com/rhasspy/piper-phonemize/releases/download/v1.0.0/libpiper_phonemize-amd64.tar.gz
tar -xzvf libpiper_phonemize-amd64.tar.gz
```

-> うまくいかないので単にdataset.jsonlの適当な行をコピーし

train_data/test/test_ja.jsonl

を作成

Generate train_data/test/0.wav

```
cat /src/neuravoice/processing-server/tts2/train_data/test/test_ja.jsonl | \
    python3 -m piper_train.infer \
        --sample-rate 22050 \
        --checkpoint /src/neuravoice/processing-server/tts2/train_data/lightning_logs/version_5/checkpoints/*.ckpt \
        --output-dir /src/neuravoice/processing-server/tts2/train_data/test
```

epoch10 step 4246

epoch11 step 4632

epoch 14 step 5790

-> 訓練集合と同じテキスト 初期段階でもそれなりに聞こえる

より初期段階

epoch2-step 2310

-> epochを重ねて急速に向上しているのがわかる

epoch 38

83

135

-> 0は完成に近づいている 6もできてきている 5は以前より発話らしくなった

epoch 435

-> 収録音源に近づいている

Export

Export ONNX model

```
python3 -m piper_train.export_onnx /src/neuravoice/processing-server/tts2/train_data/lightning_logs/version_5/checkpoints/epoch=116-step=45162.ckpt /src/neuravoice/processing-server/tts2/ja-jpspeech-medium.onnx
```

Export 

```
cp /src/neuravoice/processing-server/tts2/train_data/config.json /src/neuravoice/processing-server/tts2/ja-jpspeech-medium.onnx.json
```

Generation Test

```
/src/neuravoice/processing-server/tts2$ python scripts/synthesize.py -l ja -s 1 -t "こんやはほしぞらがかがやきおおゆきがふるでしょう"
```

epoch 90で生成

-> データ量の多いspeaker 0より品質が高いのは効率よく音素ペアを含むためか

epoch 110

-> speaker0の場合 かなり微妙やはり オリジナル音源は品質が高い！

speaker 0 (ダメな方)

```
ぱーそなりてぃとくせいのごいんしもでるのさいじゅうようふぁくたーとみられるかいほうせいによれば
そうぞうりょくげいじゅつてききょうみじょうどうせいぼうけんちせいじゆうしゅぎのむっつのそくめんいんしがありこれらのすこあがたかいほどこうふくになることがわかっています
```

epoch 142

-> まだ学習段階のためepochが上がれば必ずしもよくなるわけではない

epoch 435

speaker 0 (ダメな方)

-> 142より飛躍的に向上しているがまだイントネーションが不自然な箇所も多い

speaker 0は"から"の区切りが人間らしい

ONOMATOPEE300_091.wav

-> イントネーションが似ているので他の話者のデータを引き継いでいると思われる

```
python scripts/synthesize.py -l ja -s 1 -t "こんやはほしぞらがかがやきおおゆきがふるでしょう"
python scripts/synthesize.py -l ja -s 0 -t "こんやはほしぞらがかがやきおおゆきがふるでしょう"
python scripts/synthesize.py -l ja -s 1 -t "あれもこれもどれもほしいのだけどそしてたべたいのだけどなあ"
python scripts/synthesize.py -l ja -s 0 -t "あれもこれもどれもほしいのだけどそしてたべたいのだけどなあ"
python scripts/synthesize.py -l ja -s 1 -t "まーそのうちそれらはきっとがっぺいされるからまだちょくちょくかよっていこっかな"
python scripts/synthesize.py -l ja -s 0 -t "まーそのうちそれらはきっとがっぺいされるからまだちょくちょくかよっていこっかな"
python scripts/synthesize.py -l ja -s 0 -t "ぱーそなりてぃとくせいのごいんしもでるのさいじゅうようふぁくたーとみられるかいほうせいによれば"
python scripts/synthesize.py -l ja -s 1 -t "ぱーそなりてぃとくせいのごいんしもでるのさいじゅうようふぁくたーとみられるかいほうせいによれば"
python scripts/synthesize.py -l ja -s 0 -t "そうぞうりょくげいじゅつてききょうみじょうどうせいぼうけんちせいじゆうしゅぎのむっつのそくめんいんしがありこれらのすこあがたかいほどこうふくになることがわかっています"
python scripts/synthesize.py -l ja -s 1 -t "そうぞうりょくげいじゅつてききょうみじょうどうせいぼうけんちせいじゆうしゅぎのむっつのそくめんいんしがありこれらのすこあがたかいほどこうふくになることがわかっています"
python scripts/synthesize.py -l ja -s 0 -t "ぶっせつまかはんにゃーはーらーみったー しんぎょーかんじーざいぼーさつ ぎょうじんはんにゃーはーらーみったー じーせうけんごーおんかいくうどーいっさいくやくしゃーりーしー しゃーりーしーしきしきそくぜーくう くうそくぜーしきじゅうそうぎょうしき やくぶーにょーぜーしゃーりーしー ぜしょほうくうそうふーしょうふーめつふくふーじょうふーぞうふーげんぜこくうちゅうむーしきむーじゅうそうぎょうしき むーげんにーびーぜっしんに むーしきしょうこうみーそくほう むーげんかいないしむいーしきかい むーむみょうやくむーむーみょうじん ないしむろうしーやくむーろうしじん むくしゅうめつどうむちやくむーとく いむしょとくこぼーだいさったーえーはんにゃーはーらーみったーこ しんむーけーげーむけーげーこーむうくうふーおんりーいっさいてんどうむーそう くーきょうねーはんさんぜーしょうぶつ えーはんにゃーはーらーみったーこー とくあのくーたらさんみゃくさんぼーだい こちはんにゃーはーらーみったー ぜーだいじんしゅー ぜーだいみょうしゅ ぜむじょうしゅー ぜむじょうしゅ ぜむとうどうしゅ のうじょういっさいく しんじつふーこーこせつ はんにゃーはーらみったーしゅ そくせつしゅーわつ ぎゃーていぎゃーてい はらぎゃーてい はらそうぎゃーてい ぼーじそわかー はんにゃしんぎょう"
python scripts/synthesize.py -l ja -s 1 -t "ぶっせつまかはんにゃーはーらーみったー しんぎょーかんじーざいぼーさつ ぎょうじんはんにゃーはーらーみったー じーせうけんごーおんかいくうどーいっさいくやくしゃーりーしー しゃーりーしーしきしきそくぜーくう くうそくぜーしきじゅうそうぎょうしき やくぶーにょーぜーしゃーりーしー ぜしょほうくうそうふーしょうふーめつふくふーじょうふーぞうふーげんぜこくうちゅうむーしきむーじゅうそうぎょうしき むーげんにーびーぜっしんに むーしきしょうこうみーそくほう むーげんかいないしむいーしきかい むーむみょうやくむーむーみょうじん ないしむろうしーやくむーろうしじん むくしゅうめつどうむちやくむーとく いむしょとくこぼーだいさったーえーはんにゃーはーらーみったーこ しんむーけーげーむけーげーこーむうくうふーおんりーいっさいてんどうむーそう くーきょうねーはんさんぜーしょうぶつ えーはんにゃーはーらーみったーこー とくあのくーたらさんみゃくさんぼーだい こちはんにゃーはーらーみったー ぜーだいじんしゅー ぜーだいみょうしゅ ぜむじょうしゅー ぜむじょうしゅ ぜむとうどうしゅ のうじょういっさいく しんじつふーこーこせつ はんにゃーはーらみったーしゅ そくせつしゅーわつ ぎゃーていぎゃーてい はらぎゃーてい はらそうぎゃーてい ぼーじそわかー はんにゃしんきょう"

python scripts/synthesize.py -l ja -s 0 -t "きのーのみすぎたためふつかよいであたまががんがんした"
python scripts/synthesize.py -l ja -s 1 -t "きのーのみすぎたためふつかよいであたまががんがんした"
python scripts/synthesize.py -l ja -s 0 -t "はんざいにみがまえるおーしゅーのげんじょーをおった"
python scripts/synthesize.py -l ja -s 1 -t "はんざいにみがまえるおーしゅーのげんじょーをおった"
python scripts/synthesize.py -l ja -s 0 -t "さいしゅーのしゃとるばすわなにじですか"
python scripts/synthesize.py -l ja -s 1 -t "さいしゅーのしゃとるばすわなにじですか"
```

epoch 873

jsut

epoch 1103 (873 + 230)

-> 5,6の微妙な違いが改善され全体にほぼ原音と遜色ない

-> イントネーションが全体にさらに自然になり音質も良くなっている

epoch1560 (1103+457)

-> lossはほとんど下がっていないように見えるがイントネーションがさらに自然になっている

はんにゃしんぎょうの最後の"は"もなくなった

学習データの語彙を増やせばより自然になる

epoch 2068 (1560+508)

約4日学習

-> やや音が太くなり細部のノイズが減っている

-> ぱーそなりてぃとくせいが読めている

単語の間に、や半角スペースを入れると最後の「わかっています」が読める

イントネーションもより自然になる

ほぼ使用できるレベルに達している

自社収録 音声合成データセット MoraSpeech MEMO

750音源程度(JSUT5000 600 + Moraspeech 150)が使用されていない (全体の1.2%だがMoraspeechに限れば18%)

さらにスクリプト記述の間違いやそもそもスクリプトがないもの(全体の1~3%程度と思われる)を直せばさらに向上が見込まれる

epoch  2877 (2068 +809)

-> 昨日のバージョンとやや異なるがよくなっているかと言えばなんとも言いがたい

epoch2000あたりから向上というよりバージョンの変化と

じょんほんぷきんすだいがくのねげぶきょうじゅのぷろぐらむははなふだひゃくにんいっしゅぱずるげーむとうにもおうようできる

In docker * not used

```
docker run -v /src/neuravoice/processing-server/tts2:/tts2 -v /disk1/jpspeech:/disk1/jpspeech -it piper
# cd /tts2/piper/src/python/
# . ./venv/bin/activate
```

```
python3 -m piper_train \
    --dataset-dir /tts2/train_data/ \
    --accelerator 'gpu' \
    --devices 1 \
    --batch-size 32 \
    --max-phoneme-ids 400 \
    --validation-split 0.0 \
    --num-test-examples 0 \
    --max_epochs 10000 \
    --resume_from_single_speaker_checkpoint /tts2/pretrained_model/en-us_kusal_medium_epoch=2652-step=1953828.ckpt \
    --checkpoint-epochs 1 \
    --precision 32
```
