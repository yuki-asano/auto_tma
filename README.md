# auto_tma

## Install
### Manager PC (Ubuntu)
```
cd auto_tma
python3 -m pip install -e .
```

### Measurement GUI PC (Windows)
Environment should be built on powershell
```
cd \\wsl.localhost\Ubuntu\home\utokyo-user\catkin_ws\src\auto_tma
python3 -m pip install -e .  # including netzsch_instrument install
```

## 実験準備
### NEXTAGE
- 本体
  - 電源を入れる (緑スイッチ)
  - リセット -> 肩LEDが緑 (青スイッチ)
- NXproduction
  - 「Servo」をクリック
  - APIサーバーを起動(通常、自動起動) -> 黄色帯のExternal control mode activated
- 初期状態確認
  - 左手のツールを外して初期位置へ置く <- 「DIO」
  - ロボットを初期姿勢に戻す <- 「Initial Pose」
 
### TMA
- 本体
  - 初期状態に戻す (furnanceを閉じる)
- 操作用GUIを起動(PCからの操作が必要な場合)
  ```
  cd netzsch_instrument/netzsch_instrument/tma402f3
  ./tma_control_gui.py
  ```

## 自動TMA工程 実行
### Manager PC (ubuntu)
```
[terminal1]
roscore

[terminal2]
roslaunch rosbridge_server rosbridge_websocket.launch  # 他PCとroslibで通信する場合に必要

[terminal3]
roslaunch mitsutoyo_instrumet_ros1 mitsutoyo_micrometer.launch
```

### Measurement GUI PC (windows)
```
[terminal1] powershell
cd \\wsl.localhost\Ubuntu\home\utokyo-user\catkin_ws\src\netzsch_instrument\ros1\scripts
python3 .\netzsch_measurement_server.py ../../../auto_tma/config/auto_tma_config.yaml


# 注意: ターミナルで直接 ```.\netzsch_measurement_server_thread.py```とすると,pythonが別端末で立ち上がりエラー確認できない
```

### Manager PC (ubuntu) 再び
```
[terminal4]
roscd auto_tma/scripts
./auto_tma_gui.py -> GUIが起動。Runをクリックして実行.

CUIで、
./auto_tma.py # -> 内部で main(tma_auto=True, tare_force=True, do_measure=True, number_of_sample=2)           
でも良い
```

### テスト用
工程全体でなく,測定だけで良ければ,ターミナルからservice callを送る. 
```
rosservice call /netzsch_measurement_server "sample_id: 0" sample_thickness: 0.0" 
```

## トラブルシューティング
- マイクロメータ測定でスイッチをスカって押せない。
  - マイクロメータ本体が定位置からずれていないか確認。定位置は壁２面に当たる位置。動作中に引っかかってずれている可能性有り。画像認識でマイクロメータ本体を基準位置として動作が作成されているため。
