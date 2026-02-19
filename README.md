# auto_tma

## Install & Setup
### Manager PC (Ubuntu)
**Install python module**
```
sudo apt install python3-vcstool
```

**Setup workspace**
```
mkdir -p auto_tma_ws/src
cd auto_tma_ws
catkin build

cd src
git clone git@github.com:yuki-asano/auto_tma.git

cd auto_tma_ws
vcs import src < src/auto_tma/repositories/auto_tma.repos

cd src/auto_tma
catkin bt
```

**Install python module (self made)**
```
cd plcpy
python3 -m pip install -e .
```

**Desktop app**
```
1. 関連ファイルのパスをマシン固有のものに変更
- bin/auto_tma_app.desktop
- bin/run_auto_tma.sh

2. 起動ファイル(.desktop)を登録
cd auto_tma/bin/
cp auto_tma_app.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```

**NEXTAGE**  
カワダより取得したapiを適切なフォルダに置く.例えば以下
```
~/auto_tma_ws/src/robot_control/robots/nextage/nextage_nxa_interface/api
```


### Measurement PC (Windows)
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
A. デスクトップアプリ起動ver
```
AutoTMAのアイコンをクリック（デスクトップショートカットに登録済み）

or  
アプリ一覧から (Superボタン)「AutoTMA」を実行
```

B. CUIから起動ver
```
[terminal1]
roscore

[terminal2]
roslaunch auto_tma auto_tma.launch  # including below

  # roslaunch rosbridge_server rosbridge_websocket.launch  # 他PCとroslibで通信する場合に必要
  # roslaunch mitsutoyo_instrumet mitsutoyo_micrometer.launch  # micrometer
  # rosrun netzsch_instrument netzsch_measurement_server_mock.py  # measurement server mock for manual measurement
  # rosrun auto_tma auto_tma_gui.py  # gui controller
```

### Measurement PC (windows)
```
[terminal1] powershell
cd \\wsl.localhost\Ubuntu\home\utokyo-user\catkin_ws\src\netzsch_instrument\scripts
python3 .\netzsch_measurement_server.py ../../../auto_tma/config/auto_tma_config.yaml


# 注意: ターミナルで直接 ```.\netzsch_measurement_server_thread.py```とすると,pythonが別端末で立ち上がりエラー確認できない
```

### GUI
- Run クリックしすると、auto_tmaが開始.
- Finish measurement -> manual測定時に、測定終了したらクリック
  
```
起動はCUIで、
./auto_tma.py # -> 内部で main(tma_auto=True, tare_force=True, do_measure=True, number_of_sample=2)           
でも良い
```

### テスト用
工程全体でなく,測定だけで良ければ,ターミナルからservice callを送る. 
```
rosservice call /netzsch_measurement_server "sample_id: 0" sample_thickness: 0.0
```

## tma402f3単体での使い方
```
cd src/auto_tma/tma402f3
./tma_control_gui.py  # control GUIの起動
```

## トラブルシューティング
- マイクロメータ測定でスイッチをスカって押せない。
  - マイクロメータ本体が定位置からずれていないか確認。定位置は壁２面に当たる位置。動作中に引っかかってずれている可能性有り。画像認識でマイクロメータ本体を基準位置として動作が作成されているため。
- デスクトップappが起動できない
  - app.desktopファイルをデスクトップに置きダブルクリックで起動するのは難しい.gnomeのセキュリティが上がっている？ようで、頑張ればできるかもしれないが、デフォルトでは難しい.
  - うまく起動できないときは、パス設定周りがうまくいっていない場合がある。絶対パスが安全。
  - .shには、.bashrcと同じように、関連pkgをexportしていく必要がある。
  - デバッグ
    ```
    単体で起動していく
    cd auto_tma/bin
    gtk-launch auto_tma_app.desktop
  
    ./run_auto_tma.sh
    など
    ```
- プログラムを実行しているのにTMAが動作しない
  - PLC本体(KV-7500)のSWがRUNになっているか確認する
    - RUN: 動作モード
    - PRG: プログラム書込モード
