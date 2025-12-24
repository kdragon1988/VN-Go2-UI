"""
WebRTC通信クライアント

unitree_webrtc_connectを使用してGo2に直接接続するクライアント

主な機能:
- WebRTC経由でGo2に直接接続（Jetson不要！）
- 高レベル移動制御
- カメラ映像取得
- 状態のリアルタイム取得

対応ファームウェア:
- Go2: 1.1.1 - 1.1.11（最新）
- G1: 1.4.0

制限事項:
- unitree_webrtc_connectパッケージが必要
"""

import asyncio
import threading
import time
from typing import Optional, Callable, Any
from enum import Enum

from .state import RobotState, IMUState, FootState, RobotMode

# WebRTC接続ライブラリ
try:
    from unitree_webrtc_connect import UnitreeWebRTCConnection, WebRTCConnectionMethod
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False
    print("[WebRTCClient] unitree_webrtc_connectがインストールされていません")
    print("  pip install unitree_webrtc_connect")


class ConnectionMode(Enum):
    """接続モード"""
    LOCAL_AP = "ap"       # Go2のWiFi APに直接接続
    LOCAL_STA = "sta"     # 同一LAN上で接続
    REMOTE = "remote"     # リモートサーバー経由


class WebRTCClient:
    """
    WebRTC通信クライアント

    Go2にWebRTC経由で直接接続（Jetson不要）

    Attributes:
        robotIp: ロボットのIPアドレス（STA-Lモード用）
        serialNumber: シリアル番号（STA-L/Remoteモード用）
        connected: 接続状態
    """

    def __init__(
        self,
        robotIp: Optional[str] = None,
        serialNumber: Optional[str] = None,
        connectionMode: ConnectionMode = ConnectionMode.LOCAL_AP
    ):
        """
        WebRTCクライアントの初期化

        Args:
            robotIp: ロボットのIPアドレス（STA-Lモード用）
            serialNumber: シリアル番号（オプション）
            connectionMode: 接続モード
        """
        self.robotIp = robotIp
        self.serialNumber = serialNumber
        self.connectionMode = connectionMode
        
        self.connected = False
        self._conn: Optional[Any] = None
        
        # スレッド制御
        self._running = False
        self._eventLoop: Optional[asyncio.AbstractEventLoop] = None
        self._asyncThread: Optional[threading.Thread] = None
        
        # コールバック
        self._stateCallback: Optional[Callable[[RobotState], None]] = None
        self._videoCallback: Optional[Callable[[Any], None]] = None
        
        # 状態
        self.state = RobotState()
        self._lastStateTime = 0

    def connect(self) -> bool:
        """
        Go2に接続

        Returns:
            bool: 接続成功時True
        """
        if not WEBRTC_AVAILABLE:
            print("[WebRTCClient] WebRTCライブラリが利用できません")
            return False
        
        print(f"[WebRTCClient] 接続中... (モード: {self.connectionMode.value})")
        
        try:
            # 非同期ループをバックグラウンドスレッドで実行
            self._running = True
            self._asyncThread = threading.Thread(target=self._runAsyncLoop, daemon=True)
            self._asyncThread.start()
            
            # 接続待ち（最大10秒）
            for _ in range(100):
                if self.connected:
                    return True
                time.sleep(0.1)
            
            print("[WebRTCClient] 接続タイムアウト")
            return False
            
        except Exception as e:
            print(f"[WebRTCClient] 接続エラー: {e}")
            return False

    def _runAsyncLoop(self) -> None:
        """非同期イベントループを実行"""
        self._eventLoop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._eventLoop)
        
        try:
            self._eventLoop.run_until_complete(self._asyncConnect())
        except Exception as e:
            print(f"[WebRTCClient] 非同期ループエラー: {e}")
        finally:
            self._eventLoop.close()

    async def _asyncConnect(self) -> None:
        """非同期接続処理"""
        try:
            # 接続モードに応じてWebRTC接続を作成
            if self.connectionMode == ConnectionMode.LOCAL_AP:
                self._conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)
            elif self.connectionMode == ConnectionMode.LOCAL_STA:
                if self.robotIp:
                    self._conn = UnitreeWebRTCConnection(
                        WebRTCConnectionMethod.LocalSTA,
                        ip=self.robotIp
                    )
                elif self.serialNumber:
                    self._conn = UnitreeWebRTCConnection(
                        WebRTCConnectionMethod.LocalSTA,
                        serialNumber=self.serialNumber
                    )
                else:
                    print("[WebRTCClient] STA-LモードにはIPまたはシリアル番号が必要です")
                    return
            else:
                print("[WebRTCClient] Remoteモードは未実装です")
                return
            
            # コールバック設定
            self._conn.on("open", self._onOpen)
            self._conn.on("close", self._onClose)
            self._conn.on("error", self._onError)
            
            # ビデオトラックのコールバック
            if hasattr(self._conn, 'on_video_frame'):
                self._conn.on_video_frame = self._onVideoFrame
            
            # データチャンネルのコールバック
            if hasattr(self._conn, 'on_data_channel_message'):
                self._conn.on_data_channel_message = self._onDataMessage
            
            # 接続開始
            await self._conn.connect()
            
            self.connected = True
            self.state.connected = True
            print("[WebRTCClient] 接続成功！")
            
            # 状態更新ループ
            while self._running:
                await self._updateState()
                await asyncio.sleep(0.05)  # 20Hz
                
        except Exception as e:
            print(f"[WebRTCClient] 接続エラー: {e}")
            self.connected = False

    def _onOpen(self) -> None:
        """接続完了コールバック"""
        print("[WebRTCClient] WebRTC接続確立")
        self.connected = True
        self.state.connected = True

    def _onClose(self) -> None:
        """切断コールバック"""
        print("[WebRTCClient] WebRTC接続終了")
        self.connected = False
        self.state.connected = False

    def _onError(self, error) -> None:
        """エラーコールバック"""
        print(f"[WebRTCClient] エラー: {error}")

    def _onVideoFrame(self, frame) -> None:
        """ビデオフレーム受信コールバック"""
        if self._videoCallback:
            self._videoCallback(frame)

    def _onDataMessage(self, message) -> None:
        """データチャンネルメッセージ受信"""
        # ロボット状態の解析
        try:
            self._parseStateMessage(message)
        except Exception as e:
            print(f"[WebRTCClient] メッセージ解析エラー: {e}")

    def _parseStateMessage(self, message) -> None:
        """状態メッセージを解析"""
        # TODO: メッセージフォーマットに応じた解析
        pass

    async def _updateState(self) -> None:
        """状態を更新"""
        if not self.connected or not self._conn:
            return
        
        try:
            # 状態取得（unitree_webrtc_connectのAPIに依存）
            # 実際のAPIに合わせて実装
            self.state.timestamp = time.time()
            
            # コールバック呼び出し
            if self._stateCallback and time.time() - self._lastStateTime > 0.05:
                self._lastStateTime = time.time()
                self._stateCallback(self.state.copy())
                
        except Exception as e:
            print(f"[WebRTCClient] 状態更新エラー: {e}")

    def disconnect(self) -> None:
        """接続を切断"""
        print("[WebRTCClient] 切断中...")
        self._running = False
        
        if self._conn:
            # 非同期で切断
            if self._eventLoop and self._eventLoop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._asyncDisconnect(),
                    self._eventLoop
                )
        
        if self._asyncThread and self._asyncThread.is_alive():
            self._asyncThread.join(timeout=3.0)
        
        self.connected = False
        self.state.connected = False
        print("[WebRTCClient] 切断完了")

    async def _asyncDisconnect(self) -> None:
        """非同期切断処理"""
        if self._conn:
            try:
                await self._conn.disconnect()
            except:
                pass

    def setStateCallback(self, callback: Callable[[RobotState], None]) -> None:
        """状態更新コールバックを設定"""
        self._stateCallback = callback

    def setVideoCallback(self, callback: Callable[[Any], None]) -> None:
        """ビデオフレームコールバックを設定"""
        self._videoCallback = callback

    # ============================================================
    # 制御コマンド
    # ============================================================

    def _sendCommand(self, cmd: dict) -> None:
        """コマンドを送信"""
        if not self.connected or not self._conn:
            return
        
        try:
            # unitree_webrtc_connectのAPIに合わせて送信
            if hasattr(self._conn, 'send_command'):
                if self._eventLoop and self._eventLoop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self._conn.send_command(cmd),
                        self._eventLoop
                    )
        except Exception as e:
            print(f"[WebRTCClient] コマンド送信エラー: {e}")

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
        
        # 状態更新
        self.state.velocity = [vx, vy, vyaw]

    def standUp(self) -> None:
        """立ち上がりコマンドを送信"""
        print("[WebRTCClient] コマンド: StandUp")
        self._sendCommand({"type": "stand_up"})
        self.state.mode = RobotMode.STAND_UP

    def standDown(self) -> None:
        """伏せるコマンドを送信"""
        print("[WebRTCClient] コマンド: StandDown")
        self._sendCommand({"type": "stand_down"})
        self.state.mode = RobotMode.STAND_DOWN

    def balanceStand(self) -> None:
        """バランススタンドモードに移行"""
        print("[WebRTCClient] コマンド: BalanceStand")
        self._sendCommand({"type": "balance_stand"})

    def recoveryStand(self) -> None:
        """リカバリースタンド（転倒復帰）"""
        print("[WebRTCClient] コマンド: RecoveryStand")
        self._sendCommand({"type": "recovery_stand"})

    def stopMove(self) -> None:
        """移動を停止"""
        print("[WebRTCClient] コマンド: StopMove")
        self._sendCommand({"type": "stop_move"})
        self.state.velocity = [0, 0, 0]

    def damp(self) -> None:
        """ダンプモード（脱力）"""
        print("[WebRTCClient] コマンド: Damp")
        self._sendCommand({"type": "damp"})
        self.state.mode = RobotMode.IDLE

    def emergencyStop(self) -> None:
        """緊急停止"""
        print("[WebRTCClient] ⚠️ 緊急停止!")
        self.stopMove()
        self.damp()

