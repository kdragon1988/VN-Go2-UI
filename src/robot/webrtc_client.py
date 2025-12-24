"""
WebRTC通信クライアント

unitree_webrtc_connectを使用してGo2に直接接続するクライアント

主な機能:
- WebRTC経由でGo2に直接接続（Jetson不要！）
- 高レベル移動制御
- 障害物回避付き移動
- 特殊動作（バックフリップ等）
- カメラ映像取得
- 状態のリアルタイム取得

対応ファームウェア:
- Go2: 1.1.1 - 1.1.11（最新）
- G1: 1.4.0

MCFモード (v1.1.7+):
- AIモードとノーマルモードが統合
- SPORT_MOD トピックで制御

制限事項:
- unitree_webrtc_connectパッケージが必要
"""

import asyncio
import threading
import time
from typing import Optional, Callable, Any
from enum import Enum

from .state import RobotState, IMUState, FootState, RobotMode
from .go2_commands import (
    RtcTopic, SportCmd, ObstacleAvoidCmd, GaitType, SpeedLevel,
    move_params, euler_params, special_action_params, obstacle_avoid_params
)

# WebRTC接続ライブラリ
try:
    from unitree_webrtc_connect import Go2WebRTCConnection, WebRTCConnectionMethod
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
        obstacleAvoidEnabled: 障害物回避の状態
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
        
        # 障害物回避
        self.obstacleAvoidEnabled = False

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
                self._conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalAP)
            elif self.connectionMode == ConnectionMode.LOCAL_STA:
                if self.robotIp:
                    self._conn = Go2WebRTCConnection(
                        WebRTCConnectionMethod.LocalSTA,
                        ip=self.robotIp
                    )
                elif self.serialNumber:
                    self._conn = Go2WebRTCConnection(
                        WebRTCConnectionMethod.LocalSTA,
                        serialNumber=self.serialNumber
                    )
                else:
                    print("[WebRTCClient] STA-LモードにはIPまたはシリアル番号が必要です")
                    return
            else:
                print("[WebRTCClient] Remoteモードは未実装です")
                return
            
            # 接続開始
            await self._conn.connect()
            
            self.connected = True
            self.state.connected = True
            print("[WebRTCClient] 🚀 WebRTC接続成功！")
            
            # 状態更新ループ
            while self._running:
                await self._updateState()
                await asyncio.sleep(0.05)  # 20Hz
                
        except Exception as e:
            print(f"[WebRTCClient] 接続エラー: {e}")
            self.connected = False

    async def _updateState(self) -> None:
        """状態を更新"""
        if not self.connected or not self._conn:
            return
        
        try:
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
    # 内部コマンド送信
    # ============================================================

    def _sendSportCommand(self, apiId: int, parameter: Optional[dict] = None) -> None:
        """
        SPORT_MODトピックにコマンドを送信

        Args:
            apiId: API ID (SportCmd)
            parameter: パラメータ辞書
        """
        if not self.connected or not self._conn:
            return
        
        try:
            if self._eventLoop and self._eventLoop.is_running():
                request = {"api_id": apiId}
                if parameter:
                    request["parameter"] = parameter
                    
                asyncio.run_coroutine_threadsafe(
                    self._conn.datachannel.pub_sub.publish_request_new(
                        RtcTopic.SPORT_MOD,
                        request
                    ),
                    self._eventLoop
                )
        except Exception as e:
            print(f"[WebRTCClient] コマンド送信エラー: {e}")

    def _sendObstacleAvoidCommand(self, apiId: int, parameter: Optional[dict] = None) -> None:
        """
        OBSTACLES_AVOIDトピックにコマンドを送信

        Args:
            apiId: API ID (ObstacleAvoidCmd)
            parameter: パラメータ辞書
        """
        if not self.connected or not self._conn:
            return
        
        try:
            if self._eventLoop and self._eventLoop.is_running():
                request = {"api_id": apiId}
                if parameter:
                    request["parameter"] = parameter
                    
                asyncio.run_coroutine_threadsafe(
                    self._conn.datachannel.pub_sub.publish_request_new(
                        RtcTopic.OBSTACLES_AVOID,
                        request
                    ),
                    self._eventLoop
                )
        except Exception as e:
            print(f"[WebRTCClient] 障害物回避コマンド送信エラー: {e}")

    # ============================================================
    # 基本制御コマンド
    # ============================================================

    def move(self, vx: float, vy: float, vyaw: float) -> None:
        """
        移動コマンドを送信

        Args:
            vx: 前後速度 (m/s)
            vy: 左右速度 (m/s)
            vyaw: 旋回速度 (rad/s)
        """
        if self.obstacleAvoidEnabled:
            # 障害物回避付き移動
            self._sendObstacleAvoidCommand(
                ObstacleAvoidCmd.MOVE,
                move_params(vx, vy, vyaw)
            )
        else:
            # 通常移動
            self._sendSportCommand(
                SportCmd.MOVE,
                move_params(vx, vy, vyaw)
            )
        
        self.state.velocity = [vx, vy, vyaw]

    def standUp(self) -> None:
        """立ち上がりコマンドを送信"""
        print("[WebRTCClient] コマンド: StandUp")
        self._sendSportCommand(SportCmd.STAND_UP)
        self.state.mode = RobotMode.STAND_UP

    def standDown(self) -> None:
        """伏せるコマンドを送信"""
        print("[WebRTCClient] コマンド: StandDown")
        self._sendSportCommand(SportCmd.STAND_DOWN)
        self.state.mode = RobotMode.STAND_DOWN

    def balanceStand(self) -> None:
        """バランススタンドモードに移行"""
        print("[WebRTCClient] コマンド: BalanceStand")
        self._sendSportCommand(SportCmd.BALANCE_STAND)

    def recoveryStand(self) -> None:
        """リカバリースタンド（転倒復帰）"""
        print("[WebRTCClient] コマンド: RecoveryStand")
        self._sendSportCommand(SportCmd.RECOVERY_STAND)

    def stopMove(self) -> None:
        """移動を停止"""
        print("[WebRTCClient] コマンド: StopMove")
        self._sendSportCommand(SportCmd.STOP_MOVE)
        self.state.velocity = [0, 0, 0]

    def damp(self) -> None:
        """ダンプモード（脱力）"""
        print("[WebRTCClient] コマンド: Damp")
        self._sendSportCommand(SportCmd.DAMP)
        self.state.mode = RobotMode.IDLE

    def emergencyStop(self) -> None:
        """緊急停止"""
        print("[WebRTCClient] ⚠️ 緊急停止!")
        self.stopMove()
        self.damp()

    # ============================================================
    # 障害物回避
    # ============================================================

    def setObstacleAvoid(self, enable: bool) -> None:
        """
        障害物回避のON/OFF

        Args:
            enable: True=ON, False=OFF
        """
        print(f"[WebRTCClient] 障害物回避: {'ON' if enable else 'OFF'}")
        self._sendObstacleAvoidCommand(
            ObstacleAvoidCmd.SWITCH,
            obstacle_avoid_params(enable)
        )
        self.obstacleAvoidEnabled = enable

    def enableObstacleAvoid(self) -> None:
        """障害物回避をON"""
        self.setObstacleAvoid(True)

    def disableObstacleAvoid(self) -> None:
        """障害物回避をOFF"""
        self.setObstacleAvoid(False)

    # ============================================================
    # 姿勢制御
    # ============================================================

    def pose(self) -> None:
        """ポーズモード開始（Euler前に必要）"""
        print("[WebRTCClient] コマンド: Pose")
        self._sendSportCommand(SportCmd.POSE)

    def euler(self, roll: float, pitch: float, yaw: float) -> None:
        """
        姿勢角度を設定

        注意: 先にpose()を呼び出す必要がある

        Args:
            roll: ロール角 (rad)
            pitch: ピッチ角 (rad)
            yaw: ヨー角 (rad)
        """
        print(f"[WebRTCClient] コマンド: Euler (r:{roll:.2f}, p:{pitch:.2f}, y:{yaw:.2f})")
        self._sendSportCommand(
            SportCmd.EULER,
            euler_params(roll, pitch, yaw)
        )

    def setBodyHeight(self, height: float) -> None:
        """
        体高を設定

        Args:
            height: 体高 (m)
        """
        print(f"[WebRTCClient] コマンド: BodyHeight ({height:.2f}m)")
        self._sendSportCommand(SportCmd.BODY_HEIGHT, {"height": height})

    # ============================================================
    # 歩行モード
    # ============================================================

    def switchGait(self, gaitType: int) -> None:
        """
        歩行タイプを切り替え

        Args:
            gaitType: 歩行タイプ (GaitType)
        """
        print(f"[WebRTCClient] コマンド: SwitchGait ({gaitType})")
        self._sendSportCommand(SportCmd.SWITCH_GAIT, {"gait": gaitType})

    def setSpeedLevel(self, level: int) -> None:
        """
        速度レベルを設定

        Args:
            level: 速度レベル (SpeedLevel)
        """
        print(f"[WebRTCClient] コマンド: SpeedLevel ({level})")
        self._sendSportCommand(SportCmd.SPEED_LEVEL, {"level": level})

    # ============================================================
    # 特殊動作（バックフリップ等）
    # parameter: {"data": True} が必要
    # ============================================================

    def _doSpecialAction(self, apiId: int, actionName: str) -> None:
        """特殊動作を実行（内部用）"""
        print(f"[WebRTCClient] 🎭 特殊動作: {actionName}")
        self._sendSportCommand(apiId, special_action_params())

    def backFlip(self) -> None:
        """バック宙返り 🔥"""
        self._doSpecialAction(SportCmd.BACK_FLIP, "BackFlip")

    def frontFlip(self) -> None:
        """前方宙返り"""
        self._doSpecialAction(SportCmd.FRONT_FLIP, "FrontFlip")

    def leftFlip(self) -> None:
        """左宙返り"""
        self._doSpecialAction(SportCmd.LEFT_FLIP, "LeftFlip")

    def rightFlip(self) -> None:
        """右宙返り"""
        self._doSpecialAction(SportCmd.RIGHT_FLIP, "RightFlip")

    def handStand(self) -> None:
        """逆立ち"""
        self._doSpecialAction(SportCmd.HAND_STAND, "HandStand")

    def frontJump(self) -> None:
        """前方ジャンプ"""
        self._doSpecialAction(SportCmd.FRONT_JUMP, "FrontJump")

    def sit(self) -> None:
        """お座り"""
        self._doSpecialAction(SportCmd.SIT, "Sit")

    def stretch(self) -> None:
        """ストレッチ"""
        self._doSpecialAction(SportCmd.STRETCH, "Stretch")

    def dance1(self) -> None:
        """ダンス1"""
        self._doSpecialAction(SportCmd.DANCE_1, "Dance1")

    def dance2(self) -> None:
        """ダンス2"""
        self._doSpecialAction(SportCmd.DANCE_2, "Dance2")

    def bark(self) -> None:
        """吠える"""
        self._doSpecialAction(SportCmd.BARK, "Bark")

    def greeting(self) -> None:
        """挨拶"""
        self._doSpecialAction(SportCmd.GREETING, "Greeting")

    def shakeHand(self) -> None:
        """握手"""
        self._doSpecialAction(SportCmd.SHAKE_HAND, "ShakeHand")

    def highFive(self) -> None:
        """ハイタッチ"""
        self._doSpecialAction(SportCmd.HIGH_FIVE, "HighFive")

    def waveHand(self) -> None:
        """手を振る"""
        self._doSpecialAction(SportCmd.WAVE_HAND, "WaveHand")

    def fingerHeart(self) -> None:
        """ハートマーク"""
        self._doSpecialAction(SportCmd.FINGER_HEART, "FingerHeart")

    def nap(self) -> None:
        """昼寝"""
        self._doSpecialAction(SportCmd.NAP, "Nap")

    def wiggleHips(self) -> None:
        """お尻フリフリ"""
        self._doSpecialAction(SportCmd.WIGGLE_HIPS, "WiggleHips")
