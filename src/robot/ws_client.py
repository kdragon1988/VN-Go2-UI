"""
WebSocket通信クライアント

Jetson上のブリッジサーバーとWebSocket経由で通信するクライアント

主な機能:
- WebSocketによるJetsonへの接続
- コマンドの送信
- 状態の受信
- 自動再接続

制限事項:
- Jetson側でbridge_server.pyが動作している必要がある
"""

import asyncio
import json
import threading
import time
from typing import Optional, Callable, Any
from dataclasses import dataclass
import queue

from .state import RobotState, IMUState, FootState, RobotMode


class WebSocketClient:
    """
    WebSocket通信クライアント

    Jetsonのブリッジサーバーに接続してGo2を制御

    Attributes:
        jetsonIp: JetsonのIPアドレス
        port: WebSocketポート
        connected: 接続状態
    """

    DEFAULT_PORT = 8765

    def __init__(self, jetsonIp: str = "192.168.123.18", port: int = DEFAULT_PORT):
        """
        WebSocketクライアントの初期化

        Args:
            jetsonIp: JetsonのIPアドレス
            port: WebSocketポート
        """
        self.jetsonIp = jetsonIp
        self.port = port
        self.wsUrl = f"ws://{jetsonIp}:{port}"
        
        self.connected = False
        self.simulationMode = False
        
        # WebSocket
        self._ws = None
        self._wsLock = threading.Lock()
        
        # スレッド制御
        self._running = False
        self._connectThread: Optional[threading.Thread] = None
        self._receiveThread: Optional[threading.Thread] = None
        
        # コールバック
        self._stateCallback: Optional[Callable[[RobotState], None]] = None
        self._connectionCallback: Optional[Callable[[bool], None]] = None
        
        # 状態
        self.state = RobotState()
        
        # コマンドキュー
        self._commandQueue: queue.Queue = queue.Queue()

    def connect(self) -> bool:
        """
        Jetsonに接続

        Returns:
            bool: 接続成功時True
        """
        print(f"[WebSocketClient] 接続中: {self.wsUrl}")
        
        self._running = True
        
        # 接続スレッド開始
        self._connectThread = threading.Thread(target=self._connectionLoop, daemon=True)
        self._connectThread.start()
        
        # 接続待ち（最大5秒）
        for _ in range(50):
            if self.connected:
                return True
            time.sleep(0.1)
        
        return self.connected

    def disconnect(self) -> None:
        """接続を切断"""
        print("[WebSocketClient] 切断中...")
        self._running = False
        
        if self._connectThread and self._connectThread.is_alive():
            self._connectThread.join(timeout=2.0)
        
        self.connected = False
        self.state.connected = False
        print("[WebSocketClient] 切断完了")

    def setStateCallback(self, callback: Callable[[RobotState], None]) -> None:
        """
        状態更新コールバックを設定

        Args:
            callback: ロボット状態を受け取るコールバック関数
        """
        self._stateCallback = callback

    def setConnectionCallback(self, callback: Callable[[bool], None]) -> None:
        """
        接続状態変更コールバックを設定

        Args:
            callback: 接続状態を受け取るコールバック関数
        """
        self._connectionCallback = callback

    def _connectionLoop(self) -> None:
        """接続維持ループ"""
        import asyncio
        
        while self._running:
            try:
                asyncio.run(self._asyncConnectionLoop())
            except Exception as e:
                print(f"[WebSocketClient] 接続エラー: {e}")
                self.connected = False
                self.state.connected = False
                if self._connectionCallback:
                    self._connectionCallback(False)
            
            if self._running:
                print("[WebSocketClient] 3秒後に再接続...")
                time.sleep(3)

    async def _asyncConnectionLoop(self) -> None:
        """非同期接続ループ"""
        try:
            import websockets
        except ImportError:
            print("[WebSocketClient] websocketsがインストールされていません")
            print("  pip install websockets")
            return
        
        async with websockets.connect(self.wsUrl) as ws:
            print(f"[WebSocketClient] 接続成功: {self.wsUrl}")
            self._ws = ws
            self.connected = True
            self.state.connected = True
            
            if self._connectionCallback:
                self._connectionCallback(True)
            
            # 送受信タスクを並行実行
            receiveTask = asyncio.create_task(self._receiveLoop(ws))
            sendTask = asyncio.create_task(self._sendLoop(ws))
            
            # どちらかが終了するまで待機
            done, pending = await asyncio.wait(
                [receiveTask, sendTask],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 残りのタスクをキャンセル
            for task in pending:
                task.cancel()

    async def _receiveLoop(self, ws) -> None:
        """メッセージ受信ループ"""
        try:
            async for message in ws:
                self._handleMessage(message)
        except Exception as e:
            print(f"[WebSocketClient] 受信エラー: {e}")

    async def _sendLoop(self, ws) -> None:
        """コマンド送信ループ"""
        while self._running and self.connected:
            try:
                # キューからコマンドを取得（タイムアウト付き）
                try:
                    cmd = self._commandQueue.get(timeout=0.1)
                    await ws.send(json.dumps(cmd))
                except queue.Empty:
                    pass
                
                await asyncio.sleep(0.01)
                
            except Exception as e:
                print(f"[WebSocketClient] 送信エラー: {e}")
                break

    def _handleMessage(self, message: str) -> None:
        """
        受信メッセージを処理

        Args:
            message: 受信したJSONメッセージ
        """
        try:
            data = json.loads(message)
            msgType = data.get("type", "")
            
            if msgType == "connected":
                self.simulationMode = data.get("simulationMode", False)
                print(f"[WebSocketClient] ブリッジ接続確認 (シミュレーション: {self.simulationMode})")
                
            elif msgType == "state":
                self._updateState(data.get("data", {}))
                
            elif msgType == "pong":
                pass  # Ping応答
                
        except json.JSONDecodeError:
            print(f"[WebSocketClient] 無効なJSON: {message[:100]}")
        except Exception as e:
            print(f"[WebSocketClient] メッセージ処理エラー: {e}")

    def _updateState(self, data: dict) -> None:
        """
        状態を更新

        Args:
            data: 状態データ辞書
        """
        self.state.timestamp = data.get("timestamp", time.time())
        self.state.connected = True
        
        # モード
        modeStr = data.get("mode", "UNKNOWN")
        modeMap = {
            "IDLE": RobotMode.IDLE,
            "DOWN": RobotMode.STAND_DOWN,
            "STAND": RobotMode.STAND_UP,
            "WALK": RobotMode.WALKING,
            "RUN": RobotMode.RUNNING,
        }
        self.state.mode = modeMap.get(modeStr, RobotMode.UNKNOWN)
        
        # バッテリー
        self.state.batteryLevel = data.get("batteryLevel", 0)
        self.state.batteryVoltage = data.get("batteryVoltage", 0.0)
        self.state.batteryCurrent = data.get("batteryCurrent", 0.0)
        self.state.batteryTemperature = data.get("batteryTemperature", 25.0)
        
        # IMU
        self.state.imu.rpy = [
            data.get("imuRoll", 0.0) * 0.0174533,  # deg to rad
            data.get("imuPitch", 0.0) * 0.0174533,
            data.get("imuYaw", 0.0) * 0.0174533,
        ]
        self.state.imu.gyroscope = data.get("imuGyro", [0, 0, 0])
        self.state.imu.accelerometer = data.get("imuAccel", [0, 0, 9.81])
        
        # 速度
        self.state.velocity = [
            data.get("velocityX", 0.0),
            data.get("velocityY", 0.0),
            data.get("velocityYaw", 0.0),
        ]
        
        # 足状態
        footContacts = data.get("footContacts", [False, False, False, False])
        footForces = data.get("footForces", [0, 0, 0, 0])
        for i in range(4):
            self.state.feet[i].contact = footContacts[i] if i < len(footContacts) else False
            self.state.feet[i].force = footForces[i] if i < len(footForces) else 0
        
        # コールバック呼び出し
        if self._stateCallback:
            self._stateCallback(self.state.copy())

    def _sendCommand(self, cmd: dict) -> None:
        """
        コマンドを送信キューに追加

        Args:
            cmd: コマンド辞書
        """
        self._commandQueue.put(cmd)

    # ============================================================
    # 制御コマンド
    # ============================================================

    def move(self, vx: float, vy: float, vyaw: float) -> None:
        """
        移動コマンドを送信

        Args:
            vx: 前後速度 (m/s)
            vy: 左右速度 (m/s)
            vyaw: 旋回速度 (rad/s)
        """
        self._sendCommand({
            "type": "move",
            "vx": vx,
            "vy": vy,
            "vyaw": vyaw
        })

    def standUp(self) -> None:
        """立ち上がりコマンドを送信"""
        self._sendCommand({"type": "standUp"})

    def standDown(self) -> None:
        """伏せるコマンドを送信"""
        self._sendCommand({"type": "standDown"})

    def balanceStand(self) -> None:
        """バランススタンドモードに移行"""
        self._sendCommand({"type": "balanceStand"})

    def recoveryStand(self) -> None:
        """リカバリースタンド（転倒復帰）"""
        self._sendCommand({"type": "recoveryStand"})

    def stopMove(self) -> None:
        """移動を停止"""
        self._sendCommand({"type": "stopMove"})

    def damp(self) -> None:
        """ダンプモード（脱力）"""
        self._sendCommand({"type": "damp"})

    def emergencyStop(self) -> None:
        """緊急停止"""
        self._sendCommand({"type": "emergencyStop"})

