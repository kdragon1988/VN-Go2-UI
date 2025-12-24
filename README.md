# 🤖 Unitree Go2 Controller for macOS

**Mission Impossible風タクティカルHUDでGo2を操縦！**

macOSからUnitree Go2 (EDU) ロボットを操作するためのPython製コントローラーアプリケーションです。

![UI Preview](docs/preview.png)

## 🌟 特徴

- **タクティカルHUD** - Mission Impossible風の洗練されたインターフェース
- **Xbox互換コントローラー** - Bluetooth/有線コントローラーで直感的操作
- **リアルタイム表示** - バッテリー、IMU、足接地、速度をリアルタイム表示
- **3つの接続モード** - WebRTC / WebSocket / Direct SDK2
- **脱獄不要！** - WebRTCモードでそのまま使える

## 🎨 UIデザイン

**Mission Impossible風タクティカルHUD**

| 要素 | 説明 |
|------|------|
| カラー | クリムゾンレッド (#DC143C) + ピュアブラック背景 |
| フォント | モノスペース（JetBrains Mono / SF Mono） |
| エッジ | シャープな角（border-radius: 0） |
| コントラスト | 高コントラストで視認性抜群 |

```
┌─────────────────────────────────────────────────────────────────┐
│ ◆◆◆ CLASSIFIED ◆◆◆                                            │
│      UNITREE GO2                                                │
│ TACTICAL CONTROL SYSTEM v1.0                                    │
├────────────────┬────────────────────────┬───────────────────────┤
│ ● DISCONNECTED │ ● LIVE  00:00:00      │ ◆ ATTITUDE SENSOR     │
│ PROTOCOL       │ ◆ SURVEILLANCE FEED   │ ◆ FOOT STATUS         │
│ TARGET         │ ┌──────────────────┐  │ ◆ CONTROLLER          │
│ ▶ CONNECT      │ │                  │  ├───────────────────────┤
│ ■ TERMINATE    │ │   NO SIGNAL      │  │ ◆ SPECIAL PROTOCOLS   │
│                │ │                  │  │   ACROBATICS          │
│ OPERATION MODE │ └──────────────────┘  │   EMOTES              │
│     ---        │ ◆ POWER    ◆ VELOCITY │   COMMUNICATION       │
└────────────────┴────────────────────────┴───────────────────────┘
```

## 📋 システム要件

- macOS 11.0+
- Python 3.10+
- Xbox互換コントローラー（推奨）
- Unitree Go2 EDU

## 🚀 クイックスタート

### 1. セットアップ

```bash
git clone https://github.com/kdragon1988/VN-Go2-UI.git
cd VN-Go2-UI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. アプリ起動

```bash
python main.py
```

### 3. 接続

1. Go2の電源を入れる
2. MacをGo2のWiFi APに接続（SSID: Go2-XXXXXX）
3. アプリで「WEBRTC [DIRECT]」を選択
4. TARGETに「ap」と入力して [▶ CONNECT]

## 🔌 接続方式

### 方式A: WebRTC直接接続 ★推奨 🚀

**Jetson不要！** [unitree_webrtc_connect](https://github.com/legion1581/unitree_webrtc_connect) を使用してMacから直接Go2に接続。

```
┌─────────┐  WebRTC   ┌──────────┐
│  Mac    │──────────→│   Go2    │
│ (WiFi)  │  直接接続  │          │
└─────────┘           └──────────┘
```

**対応ファームウェア:** v1.1.1 - v1.1.11（最新）

**接続方法:**
- **APモード**: Go2のWiFi APに接続 → TARGET: `ap`
- **STAモード**: 同一LAN → TARGET: Go2のIPアドレス

### 方式B: WebSocket（Jetson経由）🌐

Jetson上でブリッジサーバーを動かす方式。

```
┌─────────┐  WebSocket  ┌──────────┐  SDK2/DDS  ┌──────────┐
│  Mac    │────────────→│  Jetson  │───────────→│ Go2 MCU  │
└─────────┘             └──────────┘            └──────────┘
```

**セットアップ:**
```bash
# Jetsonにssh
ssh unitree@192.168.123.18
pip install websockets
python bridge_server.py
```

### 方式C: Direct SDK2 📡

SDK2で直接MCUに接続。cycloneddsのビルドが必要（Python 3.11推奨）。

## 🎮 コントローラー操作

| 入力 | 動作 |
|------|------|
| 左スティック | 前後・左右移動 |
| 右スティック | 旋回 |
| Aボタン | 立ち上がる (DEPLOY) |
| Bボタン | 伏せる (RETRACT) |
| Xボタン | バランスモード |
| Yボタン | 脱力モード |
| START | リカバリー |
| BACK | 緊急停止 (ABORT) |
| LB/RB | 速度調整 |
| RT | ブースト（前進） |
| LT | ブースト（後退） |

**キーボードショートカット:**
| キー | 動作 |
|------|------|
| ESC | 緊急停止 (EMERGENCY ABORT) |
| SPACE | 立ち上がる (DEPLOY) |
| D | 伏せる (RETRACT) |

## 📁 ファイル構成

```
VN-Go2-UI/
├── main.py                      # エントリーポイント
├── requirements.txt             # 依存パッケージ
├── README.md
├── jetson/
│   └── bridge_server.py         # Jetson用WebSocketブリッジ
├── src/
│   ├── app.py                   # メインアプリケーション
│   ├── robot/
│   │   ├── webrtc_client.py     # WebRTC接続 ★推奨
│   │   ├── ws_client.py         # WebSocket接続
│   │   ├── go2_client.py        # SDK2直接接続
│   │   ├── go2_commands.py      # コマンド定義
│   │   └── state.py             # ロボット状態
│   ├── controller/
│   │   └── gamepad.py           # ゲームパッド入力
│   ├── ui/
│   │   ├── main_window.py       # メインウィンドウ
│   │   ├── widgets/             # UIウィジェット
│   │   │   ├── status_widget.py
│   │   │   ├── battery_widget.py
│   │   │   ├── camera_widget.py
│   │   │   ├── imu_widget.py
│   │   │   ├── speed_widget.py
│   │   │   ├── controller_widget.py
│   │   │   ├── robot_view_widget.py
│   │   │   └── actions_widget.py
│   │   └── styles/
│   │       ├── mission.qss      # タクティカルHUDスタイル ★
│   │       └── cyberpunk.qss    # サイバーパンクスタイル
│   └── utils/
│       └── logger.py            # ロギング
└── scripts/
    └── setup_network.sh         # ネットワーク設定
```

## ⚠️ 注意事項

- 初めてGo2を動かす際は、必ず広い場所で安全を確認してから行ってください
- 緊急停止（ESC / BACKボタン / ⚠ EMERGENCY ABORT）の位置を必ず確認してください
- コントローラーのデッドゾーンは自動調整されますが、微調整が必要な場合はコード内の `DEADZONE` 値を変更してください

## 📝 ライセンス

MIT License

## 🙏 謝辞

- [Unitree Robotics](https://www.unitree.com/) - Go2およびSDK
- [unitree_webrtc_connect](https://github.com/legion1581/unitree_webrtc_connect) - WebRTCドライバ
- [PySide6](https://doc.qt.io/qtforpython-6/) - GUIフレームワーク
- [pygame](https://www.pygame.org/) - コントローラー入力
