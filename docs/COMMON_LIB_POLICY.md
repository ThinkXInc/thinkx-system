# libcommon, simplicityの運用方針

(A案) monorepo/libcommonのように配置しマスターとする．マスターのみ編集しmonorepo/thinkx/web-server/libcommonなどに適用=焼き込み=bakeする．
(B案) monorepo/内の各サービスは個別にlibcommonのあるバージョンのコピーを持つ．サービスごとのコピーを直接編集する．コピーの編集をマスターに取り込み，他のサービスにも必要があれば適用する．


### 結論

B案とする．実運用では thinkx/web-server/libcommonを直接修正する方が monorepo/libcommon修正 -> bakeを繰り返すより遥かに早い．


### 実際の運用フロー

直接変更してサービスの動作を確認する．完了したらthinkx/web-server/libcommonのバージョンを上げる．これを原本に適用する．原本は独自の.gitを持っている．つまりlibcommonレポジトリが存在し，個々のサービスで修正されたら取り込まれる．



### 構成

以下のように配置され，それぞれがgit管理下．
/src/monorepo/.git
/src/libcommon/.git
/src/simplicity/.git

個々のサービスは単にコピーをもつ．(monorepo全体でgit管理されるのみ)
/src/monorepo/thinkx/web-server/libcommon


### 他のサービスまたはマスターへの適用

```
/src/monorepo/thinkx/web-server/libcommon/bake.sh /src/monorepo/kazukiotsukacom/web-server/libcommon --version 2.0.1
```

Discussion:
docs/archive/discussion-2026-07-15-libcommon.mdに全文