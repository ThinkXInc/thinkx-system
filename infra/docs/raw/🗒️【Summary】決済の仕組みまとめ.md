# 🗒️【Summary】決済の仕組みまとめ

_created: 20240418T021955Z / updated: 20241116T091157Z_

Stripe Element

前回対話システムの開発 Part 10 - Settings 2 & Account (UI実装・アカウントと決済の基礎)

＊ 料金プラン

請求額 (charge) = 単価 (unit price) x 使用回数 (usage)

＊ 決済の仕組み

まずアカウント作成時にクレジットカードを登録してもらう。Stripe ElementでUIを作れると認識している。アカウント作成から一ヶ月後にその月に使用した数を集計する。その数に応じて料金が決まる。

例えばアカウントを4月13日に作成した場合、次の支払い処理が5月13日の0時、その次は6月14日の0時、という支払いサイクルとなる。

請求額は 単価 x 使用数 で決まる。金額が決まったら請求書を発行し、その時点で登録済みのクレジットカードに引き落としをリクエストしたい。

＊ 請求サイクル

ユーザーが作成されるとその日がUser.start_billingにセットされる。その翌月の同じ日 (31日がないなどは30日などに補正される)がnext_billingにセットされる。同時にnext_billingの日に請求プロセスが走るようCeleryタスクキューが登録される。

next_billingの日の夜中のある時間になると、start_billingからnext_billingまでの使用回数を集計する。そしてそれに単価を (unit_price)を乗じた金額のStripe intentを生成し、請求をする。intentの対象はbilling_details.emailかで指定される。このときUser.free_callに値があればその分を差し引きfree_callに0をセットする。

＊ 無料

User.free_callに設定された値を次の請求サイクルで使用回数から差し引く。Userが作成されるとfree_callにConfig.FIRST_MONTH_FREE_CALLの値が付与される。

How payment works

First, we ask you to register a credit card when you create an account, recognizing that you can create a UI with Stripe Element. One month after the account is created, the number of transactions made during the month is counted. The fee is determined based on that number.

For example, if an account is created on April 13, the next payment is processed at midnight on May 13, the next at midnight on June 14, and so on.

The amount to be billed is determined by the unit price x the number of items used. Once the amount is determined, we would like to issue an invoice and request that the registered credit card be debited at that time.

Billing Cycle

When a user is created, the date is set in User.start_billing. When a user is created, that date is set in User.start_billing. The next_billing is set to the same day of the following month (if there is no 31st, the next_billing is set to the 30th, etc.). At the same time, the Celery task queue is registered to run the billing process on the next_billing day.

At some time during the night on the next_billing day, the number of times used from start_billing to next_billing is counted. The target of the intent is specified in the billing_details.email. At this time, if User.free_call has a value, the value is subtracted and free_call is set to 0.

＊ 請求サイクルのフロー

next_billing_date 時の決済と更新処理
Celeryのスケジューラー専用プロセスを用意
brokerはvectordbと共通にすべきか -> 共通
taskの記述
start_billingははじめユーザー登録時に作成されnext_billingは下記の計算のように計算しセットする．以降決済処理のたびにこれらを再計算し更新する．
start_billing, next_billingが作成または更新されたタイミングで，以下の処理をnext_billing_date時に行うようにtaskをキューに登録する
task:
start_billingからnext_billingまでの使用回数をAccessRecordから集計し (上限クレジット数以内に必ず収まっている)何クレジット分に相当するかを計算，請求金額が出る
請求金額が出たタイミングでユーザーに請求書をメール送信する 同時に実際にチャージする (stripeのAPI)

＊エラーハンドリング

a) Cardの使用不能
b) Stripeエラー
c) その他原因不明エラー (主にバグ)

の３種類

Card使用不能の場合はユーザーにカード情報を更新してもらうようメールを送り修正してもらうまで利用を停止する
か，最初に少額の決済を実行して成功するまで登録完了しないようにするか．後者の方が楽．

ロジックエラーの場合は決済を再度実行する必要があるがユーザーの使用を止めてはいけない．

再実行はどちらの場合も翌日とするのが楽．最大リトライ回数を超えても支払われなかったとき，

Card使用不能ならCard情報更新した時点でリトライする．

ロジックエラーならユーザー情報が次に更新されたときに実行する
のがいいか．

つまり
Userに最後の支払いのステータスが記録されている．その理由a, bも記録されている．aならpayment_method_idが更新されたときに再実行，bなら任意のユーザー情報が更新されたときに再実行．どちらもexecute_now=Trueで即時実行
．

どちらの場合も最後に失敗したintentidを記録とその理由(a,b)を記録しておき，同じintentidに再
実行することで重複決済を防ぎたい．

用を止めるには，Hostに使用可能か否かのフラグを持たせる必要がある．

-> まずCardエラーとStripeエラー，その他エラーをraiseしPaymentStatusとlast_payment_intentをuserに保存するようにした．

a) Card

Cardエラーではメールを飛ばした．設定へのリンク入り．
Stripe Test Credit Card
 で再現できる．

celeryからメールを飛ばすのに少し手を加える必要があった．

このケースでは

使用停止措置

Host.suspend = True

設定画面でカード情報更新を促す表示

が必要になる．

b) Stripeエラー

-> self.retry()でリトライが走る．MAX_RETRYまで試してもだめなときは，以下．しかしかなり細かいケースなので後回しにしたい．

このときintent id 不明なのでintentを新規に作る必要がある．next_billingは更新されていないことが保証されているのでそのままrun_paymentをexecute_now=Trueで実行すればいい．

何かのトリガーでこのステータスを確認したら決済リトライ実行．

ログイン時点かユーザー情報更新時か．

c) その他原因不明エラー

-> プログラムのバグなのでどこで起きたかわからない．決済完了した後かもしれないので不用意にretryできない．
intent.idが得られた後のエラーならlast_intent_idがセットされている
．エラー内容はlatest_payment_errorにセットされている．つまり追跡して対応できる．

これも基本的には起こらず，細かいケースなので後回しにしたい．

使えるカード 2024 Apr

https://docs.stripe.com/payments/cards

```
アメリカン・エキスプレス
中国銀聯 (CUP)
ディスカバーとダイナースクラブ
eftpos オーストラリア
JCB
Mastercard
Visa
```

24 Nov 15

＊ 決済再考

現在一回の対話で0.05ドル (7.5円)

最大10応答，平均5応答とすれば1応答あたり 0.05/5 = 0.01USD

1レスポンスあたり1クレジットにすると

または1クエリあたりにすると処理しやすいが応答あたりとした方が自然

-> server.goでこれを実装するのは難しい

-> 
tasks.pyでincrementHostUsageを実行したい

超過していたら特別なメッセージを返す

1インタビュー1ドル程度にするには

1インタビューあたり最低5回は応答する

平均して8回または10回とする

1USD/5回 = 0.2USD (30円) /response

これは元の価格よりかなり高い

1USD/8回 = 0.125USD (18.75円) /response

1クレジット0.05USDとすれば2.5クレジット分 

-> 切りが良くないので3クレジット分とすれば

１クレジット := 0.05USD
通常サービス1応答あたり価格 = 1 [クレジット] = 0.05USD
インタビュー1応答あたり価格 = 3 [クレジット] = 0.15USD
インタビュー１回あたりの価格目安 = 0.15USD * 8応答 = 1.2USD / インタビュー
インタビュー1応答あたり価格 = 2 [クレジット] = 0.1USD
インタビュー１回あたりの価格目安 = 0.1USD * 8応答 = 0.8USD / インタビュー

**コードベースにおける月額課金の説明：**

提供されたコードベースにおける月額課金システムは、予定された課金サイクルにおけるユーザーの利用状況に基づいて課金するように設計されています。以下に、その仕組みを段階的に説明します。

1. **ユーザーの作成と最初の請求日：**

  - 新しいユーザーが `/v1/users/create` または `/v1/users/create/googleoauth` エンドポイントのいずれかを使用して作成されると、システムは `start_billing` と `next_billing` の日付を割り当てます。

   - これらの日付は、`User.get_billing_dates()` メソッドを使用して計算されます。このメソッドは、内部的に `User.get_start_billing_date()` と `User.calculate_next_billing_date(start_date)` を呼び出します。

   ```python

   start_billing, next_billing = User.get_billing_dates(is_debug=is_debug)

   user = User.create_new(

       suspended_email=email, password=password,

       free_call=FIRST_MONTH_FREE_CREDIT,

       lang=lang,

       start_billing=start_billing, next_billing=next_billing)

   ```

2. **初期支払タスクのスケジュール：**

   - ユーザーを作成するとすぐに、システムは `user.schedule_payment(lang)` を呼び出して最初の支払タスクをスケジュールします。

   - `schedule_payment` メソッドは、ユーザーの `next_billing` 日付で `run_payment` タスクをスケジュールするために、Celery の `apply_async` 関数を使用します。

   ```python

   def schedule_payment(self, lang, execute_now=False):

       ...

       task = run_payment.apply_async(

           args=[str(self.id), lang],

           eta=self.next_billing

       )

   ```

3. **支払いタスクの実行:**

   - スケジュールされた時刻が到来すると、`run_payment` タスクが実行されます。

   - このタスクは以下のアクションを実行します。

     - 課金期間におけるユーザーの利用データを取得します。

     - 利用状況と無料クレジットに基づいて請求額を計算します。

     - `user.execute_billing_charge(...)` を使用して Stripe 経由で支払い処理を行います。

     - 支払い結果に基づいて、ユーザーの `last_payment_status`、`last_payment_date`、および `last_payment_error` フィールドを更新します。

    - `User.calculate_next_billing_date(user.start_billing)` を呼び出して、ユーザーの `start_billing` および `next_billing` 日付を次の課金期間に更新します。

     - ユーザーの `free_call` を毎月の無料通話分にリセットします。

   ```python

   def run_payment(user_id, lang):

       ...

       # 無料通話と次回の請求を更新

       user.free_call = MONTHLY_FREE_CREDIT

       user.start_billing = User.ensure_utc(user.next_billing)

       user.next_billing = User.ensure_utc(user.calculate_next_billing_date(user.start_billing))

       user.last_payment_status = PaymentStatus.SUCCESS.value

       user.last_payment_error = 「」

       user.last_payment_date = datetime.now(pytz.utc)

       user.save()

   ```
