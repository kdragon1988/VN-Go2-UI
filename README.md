# 🤖 Unitree Go2 Controller for macOS

**サイバーパンク風UIでGo2を操縦！**

macOSからUnitree Go2 (EDU) ロボットを操作するためのPython製コントローラーアプリケーションです。

## 🌟 特徴

- **サイバーパンクUI** - ネオンが光るダッシュボード
- **Xbox互換コントローラー** - Bluetooth/有線コントローラーで直感的操作
- **リアルタイム表示** - バッテリー、IMU、足接地、速度をリアルタイム表示
- **2つの接続モード** - WebSocket経由 or Direct SDK2

## 📋 システム要件

- macOS 11.0+
- Python 3.10+ (3.11推奨)
- Xbox互換コントローラー（推奨）
- Unitree Go2 EDU

## 🚀 クイックスタート

### 1. セットアップ

```bash
cd VN_Unitree
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. アプリ起動

```bash
python main.py
```

## 🔌 接続方式

### 方式A: WebSocket経由（推奨）🌐

Jetson上でブリッジサーバーを動かし、Mac→Jetson→Go2 MCUの経路で制御。

```
┌─────────┐  WebSocket  ┌──────────┐  SDK2/DDS  ┌──────────┐
│  Mac    │────────────→│  Jetson  │───────────→│ Go2 MCU  │
│ (WiFi)  │  Port 8765  │(Ubuntu)  │ (loopback) │          │
└─────────┘             └──────────┘            └──────────┘
```

**セットアップ手順:**

1. **ネットワーク接続**
   - Mac/PCをGo2のWiFi APに接続（SSID: Go2-XXXXXX）
   - または同一LANに接続

2. **Jetson側でブリッジサーバー起動**
   ```bash
   # Jetsonにssh接続
   ssh unitree@192.168.123.18
   
   # ブリッジサーバーを起動
   pip install websockets
   python /path/to/bridge_server.py
   ```

3. **Mac側で接続**
   - モード: "WebSocket (Jetson経由)" を選択
   - IP: `192.168.123.18`
   - [CONNECT] をクリック

### 方式B: Direct SDK2（要Python 3.11）📡

Mac上で直接SDK2を使用してGo2 MCUと通信。cycloneddsのビルドが必要。

> ⚠️ Python 3.13ではcycloneddsのビルドエラーが発生します。Python 3.11を使用してください。

## 🎮 コントローラー操作

| 入力 | 動作 |
|------|------|
| 左スティック | 前後・左右移動 |
| 右スティック | 旋回 |
| Aボタン | 立ち上がる |
| Bボタン | 伏せる |
| Xボタン | バランスモード |
| Yボタン | 脱力モード |
| START | リカバリー |
| BACK | 緊急停止 |
| LB/RB | 速度調整 |
| RT | ブースト（前進） |
| LT | ブースト（後退） |

## 📁 ファイル構成

```
VN_Unitree/
├── main.py                      # エントリーポイント
├── requirements.txt             # 依存パッケージ
├── README.md
├── jetson/
│   └── bridge_server.py         # Jetson用WebSocketブリッジ
├── src/
│   ├── app.py                   # メインアプリケーション
│   ├── robot/
│   │   ├── go2_client.py        # SDK2直接通信
│   │   ├── ws_client.py         # WebSocket通信
│   │   └── state.py             # ロボット状態
│   ├── controller/
│   │   └── gamepad.py           # ゲームパッド入力
│   ├── ui/
│   │   ├── main_window.py       # メインウィンドウ
│   │   ├── widgets/             # UIウィジェット
│   │   └── styles/              # スタイルシート
│   └── utils/
│       └── logger.py            # ロギング
└── scripts/
    └── setup_network.sh         # ネットワーク設定スクリプト
```

## 🔧 Jetson側セットアップ

`jetson/bridge_server.py` をJetsonにコピーして使用します。

```bash
# Jetsonにファイルをコピー
scp jetson/bridge_server.py unitree@192.168.123.18:~/

# Jetsonでインストール
ssh unitree@192.168.123.18
pip install websockets

# サーバー起動（バックグラウンド実行）
nohup python bridge_server.py > bridge.log 2>&1 &
```

## ⚠️ 注意事項

- 初めてGo2を動かす際は、必ず広い場所で安全を確認してから行ってください
- 緊急停止（BACK/⛔ボタン）の位置を必ず確認してください
- コントローラーのデッドゾーンは自動調整されますが、微調整が必要な場合はコード内の `DEADZONE` 値を変更してください

## 📝 ライセンス

MIT License

## 🙏 謝辞

- [Unitree Robotics](https://www.unitree.com/) - Go2およびSDK
- [PySide6](https://doc.qt.io/qtforpython-6/) - GUIフレームワーク
- [pygame](https://www.pygame.org/) - コントローラー入力
