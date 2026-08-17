# auto_tma

## Install & Setup
- https://github.com/yuki-asano/auto_tma/wiki/Install-&-Setup


## Execution of AutoTMA process
### Preparation
**NEXTAGE**
- 本体
  - 電源を入れる (緑スイッチ)
  - リセット (青スイッチ) -> 肩LEDが緑
- NEXTAGE PC (NXproduction)
  - デスクトップ -> NxProduction v3.15 をダブルクリック 
  - (通常, 自動起動なので不要だが)
    - APIサーバーを起動 -> 黄色帯のExternal control mode activated
    - 「Servo」をクリック
- ロボット初期状態確認
  - 両手のツールを外して初期位置へ置く <- 「DIO」
  - ロボットを初期姿勢に戻す <- 「Initial Pose」
 
**TMA**
- 本体
  - 初期状態に戻す (furnanceを閉じる)
    - 操作が必要な場合は、後述の操作用GUIで操作
    ```
    furnance_open_full
    furnance_close_full
     など
    ```
  - 一回ソフトを起動してsetpointをonにして炉内温度を一定にしておく(通常25℃程度)

### Execute auto-measurement
**Launch programs**
- Manager PC (ubuntu)
  - デスクトップアプリ起動ver
  ```
  AutoTMAのアイコンをクリック（デスクトップショートカットに登録済み）
  
  or  
  アプリ一覧から (Superボタン)「AutoTMA」を実行
  ```

  - CUIから起動ver
  ```
  [terminal1]
  roscore
  
  [terminal2]
  roslaunch auto_tma auto_tma.launch  # including below
  
    # roslaunch rosbridge_server rosbridge_websocket.launch  # 他PCとroslibで通信する場合に必要
    # roslaunch mitsutoyo_instrumet mitsutoyo_micrometer.launch  # micrometer
    # rosrun netzsch_measurement netzsch_measurement_server_mock.py  # measurement server mock for manual measurement
    # rosrun auto_tma auto_tma_gui.py  # gui controller
  ```

- Measurement PC (windows)
  ```
  [terminal1] powershell
  cd \\wsl.localhost\Ubuntu\home\utokyo-user\auto_tma_ws\src\netzsch_instrument\netzsch_measurement\scripts
  python3 .\netzsch_measurement_server.py ../../auto_tma/config/auto_tma_config.yaml
  
  # 注意: ターミナルで直接 ```.\netzsch_measurement_server_thread.py```とすると,pythonが別端末で立ち上がりエラー確認できない
  ```

**GUI operation**
- Run をクリックすると、auto_tmaが開始.
  ```
  起動はCUIで、
  ./auto_tma.py      
  でも良い. 内部では
  main(tma_auto=True, tare_force=True, do_measure=True, number_of_sample=2)     
  ```
- Buttons
  - Finish measurement: manual測定時に、測定終了したらクリック
  


### テスト & デバッグ
- 工程全体でなく,測定だけで良ければ,ターミナルからservice callを送る. 
```
rosservice call /netzsch_measurement_server "sample_id: 0 sample_thickness: 0.0"
```


## 外部制御 (HTTP)
`auto_tma_http_server.py` は, 測定シーケンス `main()` を他PCから起動・監視するための
JSON/HTTP エンドポイントを提供する. Python 3.8 標準ライブラリのみで, 追加依存は無い.

### 起動
```
[terminal] catkin workspace を source した状態で
rosrun auto_tma auto_tma_http_server.py            # 既定ポート 8300
rosrun auto_tma auto_tma_http_server.py --port 8300

# もしくは auto_tma.launch から一緒に起動する (既定は起動しない)
roslaunch auto_tma auto_tma.launch http_server:=true
```

### エンドポイント
| Method | Path      | 説明 |
| ------ | --------- | ---- |
| GET    | `/status` | `{"state": "idle｜running｜finished｜failed", "running": bool, "params": {...}\|null, "log": [str], "last_error": str\|null, "started_at": float\|null, "finished_at": float\|null}` |
| POST   | `/start`  | body は `main()` の引数 (`tma_auto`, `tare_force`, `measure_mode`, `number_of_sample`, `motion_speed`). 全て省略可で, 既定値は `main()` と同一. 202 受理 / 400 引数不正 / 409 実行中 |

`log` には `main()` の `gui_log_cb` に流れるメッセージ (`AutoTMA started`,
`sample_id: N, thickness: X`, `AutoTMA finished`) が直近200件たまる.

### 疎通確認
```
curl http://<Manager PC>:8300/status
curl -X POST http://<Manager PC>:8300/start -H 'Content-Type: application/json' \
     -d '{"number_of_sample": 2, "measure_mode": 0}'
```

### 注意
- run スロットは1つ. 実行中の `/start` は 409 を返す.
- **`/stop` は無い**. `main()` に中断機構が無いため, 開始した測定は最後まで走る.
- 引数の検証はサーバ側で `main()` 呼び出し前に行う (`main()` は不正引数で `sys.exit(1)`
  するため, ワーカースレッド内で踏むと run が黙って消えるため).
- `tma_auto=false` は `main()` が各ステップでこの端末の Enter 入力を待つモードなので,
  リモート運用では使わない.
- run の状態はプロセス内メモリのみ. サーバを再起動すると走行中 run の状態は失われる.
