# embrio 連携用 HTTP サーバ

AutoTMA の測定シーケンスを**別 PC から起動・監視する**ための HTTP サーバです。
株式会社 embrio 側のラボオーケストレータ（emalab）から AutoTMA をリモート実行する
ために追加しました。

**auto_tma 本体のファイルは一つも変更していません。** 追加物はすべてこのディレクトリ
（`3rd_party/embrio/`）に閉じており、明示的に起動しない限り何も動きません。既存の
`roslaunch auto_tma auto_tma.launch` や GUI の使い方は従来どおりです。

| ファイル | 内容 |
| --- | --- |
| `scripts/auto_tma_http_server.py` | `auto_tma.auto_tma_main.main()` を JSON/HTTP で包む ROS ノード |
| `launch/auto_tma_http_server.launch` | 上記ノードだけを起動する launch ファイル |

Python 3.8 の標準ライブラリのみで実装しており、追加の依存パッケージはありません。

## なぜ必要か

`main()` は ROS サービス / アクションとして公開されていないため、rosbridge 経由でも
起動できません。トリガは GUI の Run ボタンかローカル実行だけで、別 PC から AutoTMA を
動かす経路がありませんでした。このサーバはその入口を 1 つ足すだけのものです。

## 起動方法

デバイス系のノード（roscore / rosbridge / マイクロメータ / 測定サーバ）は**従来どおり**
起動してください。その上で、catkin workspace を source した端末から:

```bash
# 従来どおりデバイス系を起動しておく
roslaunch auto_tma auto_tma.launch

# 別端末で HTTP サーバを起動する
rosrun auto_tma auto_tma_http_server.py                 # 既定ポート 8300
rosrun auto_tma auto_tma_http_server.py --port 8300

# launch ファイルからでも可
roslaunch auto_tma auto_tma_http_server.launch
roslaunch auto_tma auto_tma_http_server.launch port:=8300
```

ノード名は `auto_tma_http` で、GUI の `auto_tma` ノードとは衝突しません。

## エンドポイント

| Method | Path | 説明 |
| --- | --- | --- |
| GET | `/status` | `state`（`idle` / `running` / `finished` / `failed`）、`running`、`params`、直近 200 件の `log`、`last_error`、`started_at` / `finished_at` を返す |
| POST | `/start` | body は `main()` の引数（`tma_auto`, `tare_force`, `measure_mode`, `number_of_sample`, `motion_speed`）。すべて省略可で、既定値は `main()` と同一。202 受理 / 400 引数不正 / 409 実行中 |

`log` には `main()` の `gui_log_cb` に流れるメッセージ（`AutoTMA started`,
`sample_id: N, thickness: X`, `AutoTMA finished`）が入ります。

疎通確認:

```bash
curl http://<Manager PC>:8300/status
curl -X POST http://<Manager PC>:8300/start -H 'Content-Type: application/json' \
     -d '{"number_of_sample": 2, "measure_mode": 0}'
```

## 設計上の判断・制約

- **run スロットは 1 つ。** 実行中の `/start` は 409 を返します。
- **`/stop` はありません。** `main()` に中断機構が無いため、開始した測定は最後まで走ります。
  中断を入れるには `main()` 側の改修が必要で、この追加物の範囲外としています。
- **引数の検証はサーバ側で `main()` 呼び出し前に行っています。** `main()` は不正引数で
  `sys.exit(1)` するため、ワーカースレッド内で踏むと run が黙って消えてしまうためです。
  例外（`SystemExit` 含む）は `state=failed` + `last_error` として記録します。
- **`tma_auto=false` はリモート運用では使えません。** このモードは `main()` が各ステップで
  サーバ側端末の Enter 入力を待つためです。
- **run の状態はプロセス内メモリのみ保持します。** サーバを再起動すると走行中 run の状態は
  失われます（シーケンス自体も `main()` スレッドごと消えます）。
- 認証はありません。ラボ内 LAN での利用を前提としています。

## 連絡先

不明点や変更のご要望は embrio（石川）までお願いします。
