# auto_tma

## Install & Setup
### Common (Manager and Measurement PCs)
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
source ~/auto_tma_ws/devel/setup.bash
```

### Manager PC (Ubuntu)
**Install python module (self made)**
```
cd plcpy
python3 -m pip install -e .
```

**Desktop app**
1. 関連ファイルのパスをマシン固有のものに変更
```
- bin/auto_tma_app.desktop
- bin/run_auto_tma.sh
```
2. 起動ファイル(.desktop)を登録
```
cd auto_tma/bin/
cp auto_tma_app.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
```
→アプリ一覧から起動可能に


**NEXTAGE**  
カワダより取得したapiを適切なフォルダに置く.例えば以下
```
~/auto_tma_ws/src/robot_control/robots/nextage/nextage_nxa_interface/api
```

### Measurement PC (Windows)
- netzsch_measurementの手順に従い環境構築
  - https://github.com/asanolab/netzsch_instrument/blob/main/netzsch_measurement/README.md


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

### Auto-measurement
**Manager PC (ubuntu)**  
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
  # rosrun netzsch_measurement netzsch_measurement_server_mock.py  # measurement server mock for manual measurement
  # rosrun auto_tma auto_tma_gui.py  # gui controller
```

**Measurement PC (windows)**
```
[terminal1] powershell
cd \\wsl.localhost\Ubuntu\home\utokyo-user\auto_tma_ws\src\netzsch_instrument\netzsch_measurement\scripts
python3 .\netzsch_measurement_server.py ../../auto_tma/config/auto_tma_config.yaml

# 注意: ターミナルで直接 ```.\netzsch_measurement_server_thread.py```とすると,pythonが別端末で立ち上がりエラー確認できない
```

**GUI**
- Run クリックしすると、auto_tmaが開始.
- Finish measurement -> manual測定時に、測定終了したらクリック
  
```
起動はCUIで、
./auto_tma.py # -> 内部で main(tma_auto=True, tare_force=True, do_measure=True, number_of_sample=2)           
でも良い
```

### テスト & デバッグ
- 工程全体でなく,測定だけで良ければ,ターミナルからservice callを送る. 
```
rosservice call /netzsch_measurement_server "sample_id: 0 sample_thickness: 0.0"
```
