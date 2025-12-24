"""
Unitree Go2 通信クライアント

SDK2を使用してGo2との通信を管理するクライアントクラス

主な機能:
- DDS通信によるGo2との接続
- ロボット状態の受信
- 移動コマンドの送信
- カメラ映像の取得

制限事項:
- Go2 EDUエディション専用
- 同一LAN接続が必要
- SDK2がインストールされている必要がある
"""

import time
import threading
import math
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import IntEnum

from .state import RobotState, IMUState, MotorState, FootState, RobotMode


class SportModeCmd(IntEnum):
    """
    スポーツモードコマンドID

    SDK2の定義に基づく
    """
    DAMP = 0           # ダンプモード（脱力）
    BALANCE_STAND = 1  # バランススタンド
    STOP_MOVE = 2      # 移動停止
    STAND_UP = 3       # 立ち上がり
    STAND_DOWN = 4     # 伏せる
    RECOVERY_STAND = 5 # リカバリースタンド
    MOVE = 6           # 移動
    SIT = 7            # 座る
    RISE_SIT = 8       # 座りから立つ
    STRETCH = 9        # ストレッチ
    WALLOW = 10        # 転がり
    POSE = 11          # ポーズ
    SCRAPE = 12        # 引っ掻く
    FRONT_FLIP = 13    # 前方宙返り
    FRONT_JUMP = 14    # 前方ジャンプ
    FRONT_POUNCE = 15  # 前方飛びつき
    DANCE1 = 16        # ダンス1
    DANCE2 = 17        # ダンス2
    HEART = 19         # ハートジェスチャー
    HELLO = 23         # 挨拶
    STRAIGHTHAND1 = 25 # 握手1


@dataclass
class MoveCommand:
    """
    移動コマンド

    Attributes:
        vx: 前後速度 (m/s) 正:前進, 負:後退
        vy: 左右速度 (m/s) 正:左, 負:右  
        vyaw: 旋回角速度 (rad/s) 正:左旋回, 負:右旋回
    """
    vx: float = 0.0
    vy: float = 0.0
    vyaw: float = 0.0


class Go2Client:
    """
    Go2通信クライアント

    unitree_sdk2を使用してGo2との通信を管理

    Attributes:
        robotIp: ロボットのIPアドレス
        connected: 接続状態
        state: 現在のロボット状態
    """

    # 速度制限
    MAX_VX = 1.5      # 最大前後速度 (m/s)
    MAX_VY = 0.5      # 最大左右速度 (m/s)
    MAX_VYAW = 1.5    # 最大旋回速度 (rad/s)

    def __init__(self, robotIp: str = "192.168.123.161"):
        """
        Go2クライアントの初期化

        Args:
            robotIp: Go2のIPアドレス（デフォルト: 192.168.123.161）
        """
        self.robotIp = robotIp
        self.connected = False
        self.state = RobotState()
        
        # SDKクライアント
        self._sportClient = None
        self._stateClient = None
        self._videoClient = None
        
        # スレッド制御
        self._running = False
        self._stateThread: Optional[threading.Thread] = None
        self._videoThread: Optional[threading.Thread] = None
        
        # コールバック
        self._stateCallback: Optional[Callable[[RobotState], None]] = None
        self._videoCallback: Optional[Callable[[Any], None]] = None
        
        # 最新のコマンド
        self._lastMoveCmd = MoveCommand()
        self._cmdLock = threading.Lock()
        
        # シミュレーションモード（SDK未インストール時）
        self._simulationMode = False

    def connect(self) -> bool:
        """
        Go2への接続を確立

        Returns:
            bool: 接続成功時True

        Raises:
            ConnectionError: 接続に失敗した場合
        """
        try:
            # unitree_sdk2_pythonのインポート試行
            try:
                from unitree_sdk2py.core.channel import ChannelFactory, ChannelType
                from unitree_sdk2py.idl.default import unitree_go2_msg_dds_
                from unitree_sdk2py.idl.unitree_go2.msg.dds_ import SportModeState_
                from unitree_sdk2py.go2.sport.sport_client import SportClient
                
                # DDS通信の初期化
                ChannelFactory.Instance().Init(0, self.robotIp)
                
                # スポーツクライアントの作成
                self._sportClient = SportClient()
                self._sportClient.SetTimeout(5.0)
                self._sportClient.Init()
                
                self._simulationMode = False
                print(f"[Go2Client] SDK2で{self.robotIp}に接続しました")
                
            except ImportError as e:
                # SDKがない場合はシミュレーションモード
                print(f"[Go2Client] SDK2が見つかりません。シミュレーションモードで起動します: {e}")
                self._simulationMode = True

            self.connected = True
            self.state.connected = True
            
            # 状態受信スレッドの開始
            self._running = True
            self._stateThread = threading.Thread(target=self._stateLoop, daemon=True)
            self._stateThread.start()
            
            return True

        except Exception as e:
            self.connected = False
            self.state.connected = False
            raise ConnectionError(f"Go2への接続に失敗しました: robotIp={self.robotIp}, error={e}")

    def disconnect(self) -> None:
        """
        Go2との接続を切断
        """
        self._running = False
        
        if self._stateThread and self._stateThread.is_alive():
            self._stateThread.join(timeout=2.0)
        
        if self._videoThread and self._videoThread.is_alive():
            self._videoThread.join(timeout=2.0)
        
        self.connected = False
        self.state.connected = False
        print("[Go2Client] 切断しました")

    def setStateCallback(self, callback: Callable[[RobotState], None]) -> None:
        """
        状態更新コールバックを設定

        Args:
            callback: ロボット状態を受け取るコールバック関数
        """
        self._stateCallback = callback

    def setVideoCallback(self, callback: Callable[[Any], None]) -> None:
        """
        映像フレームコールバックを設定

        Args:
            callback: 映像フレームを受け取るコールバック関数
        """
        self._videoCallback = callback
        
        # 映像スレッドの開始
        if self._running and not self._videoThread:
            self._videoThread = threading.Thread(target=self._videoLoop, daemon=True)
            self._videoThread.start()

    def move(self, vx: float, vy: float, vyaw: float) -> None:
        """
        移動コマンドを送信

        Args:
            vx: 前後速度 (m/s) 正:前進, 負:後退
            vy: 左右速度 (m/s) 正:左, 負:右
            vyaw: 旋回角速度 (rad/s) 正:左旋回, 負:右旋回

        Note:
            速度は自動的に制限値内にクランプされる
        """
        # 速度制限
        vx = max(-self.MAX_VX, min(self.MAX_VX, vx))
        vy = max(-self.MAX_VY, min(self.MAX_VY, vy))
        vyaw = max(-self.MAX_VYAW, min(self.MAX_VYAW, vyaw))
        
        with self._cmdLock:
            self._lastMoveCmd = MoveCommand(vx, vy, vyaw)
        
        if self._sportClient and not self._simulationMode:
            try:
                self._sportClient.Move(vx, vy, vyaw)
            except Exception as e:
                print(f"[Go2Client] 移動コマンド送信エラー: vx={vx}, vy={vy}, vyaw={vyaw}, error={e}")

    def standUp(self) -> None:
        """立ち上がりコマンドを送信"""
        self._sendSportCmd(SportModeCmd.STAND_UP)

    def standDown(self) -> None:
        """伏せるコマンドを送信"""
        self._sendSportCmd(SportModeCmd.STAND_DOWN)

    def balanceStand(self) -> None:
        """バランススタンドモードに移行"""
        self._sendSportCmd(SportModeCmd.BALANCE_STAND)

    def recoveryStand(self) -> None:
        """リカバリースタンド（転倒復帰）"""
        self._sendSportCmd(SportModeCmd.RECOVERY_STAND)

    def stopMove(self) -> None:
        """移動を停止"""
        self._sendSportCmd(SportModeCmd.STOP_MOVE)
        self.move(0, 0, 0)

    def damp(self) -> None:
        """ダンプモード（脱力）"""
        self._sendSportCmd(SportModeCmd.DAMP)

    def hello(self) -> None:
        """挨拶アクション"""
        self._sendSportCmd(SportModeCmd.HELLO)

    def stretch(self) -> None:
        """ストレッチアクション"""
        self._sendSportCmd(SportModeCmd.STRETCH)

    def emergencyStop(self) -> None:
        """
        緊急停止

        即座に全ての動作を停止し、ダンプモードに移行
        """
        self.stopMove()
        self.damp()
        print("[Go2Client] ⚠️ 緊急停止を実行しました")

    def _sendSportCmd(self, cmd: SportModeCmd) -> None:
        """
        スポーツモードコマンドを送信

        Args:
            cmd: 送信するコマンド
        """
        if self._sportClient and not self._simulationMode:
            try:
                if cmd == SportModeCmd.STAND_UP:
                    self._sportClient.StandUp()
                elif cmd == SportModeCmd.STAND_DOWN:
                    self._sportClient.StandDown()
                elif cmd == SportModeCmd.BALANCE_STAND:
                    self._sportClient.BalanceStand()
                elif cmd == SportModeCmd.RECOVERY_STAND:
                    self._sportClient.RecoveryStand()
                elif cmd == SportModeCmd.STOP_MOVE:
                    self._sportClient.StopMove()
                elif cmd == SportModeCmd.DAMP:
                    self._sportClient.Damp()
                elif cmd == SportModeCmd.HELLO:
                    self._sportClient.Hello()
                elif cmd == SportModeCmd.STRETCH:
                    self._sportClient.Stretch()
                else:
                    print(f"[Go2Client] 未実装コマンド: {cmd}")
            except Exception as e:
                print(f"[Go2Client] コマンド送信エラー: cmd={cmd}, error={e}")
        else:
            print(f"[Go2Client] シミュレーション: {cmd.name}")

    def _stateLoop(self) -> None:
        """
        状態受信ループ（別スレッドで実行）
        """
        while self._running:
            try:
                if self._simulationMode:
                    # シミュレーションモードではダミーデータを生成
                    self._updateSimulatedState()
                else:
                    # 実際のSDKから状態を取得
                    self._updateRealState()
                
                # コールバック呼び出し
                if self._stateCallback:
                    self._stateCallback(self.state.copy())
                
                time.sleep(0.02)  # 50Hz
                
            except Exception as e:
                print(f"[Go2Client] 状態受信エラー: {e}")
                time.sleep(0.1)

    def _updateSimulatedState(self) -> None:
        """
        シミュレーション用のダミー状態を生成
        """
        t = time.time()
        
        # バッテリー（徐々に減少するシミュレーション）
        self.state.batteryLevel = max(20, 100 - int((t % 1000) / 10))
        self.state.batteryVoltage = 25.0 + math.sin(t * 0.1) * 0.5
        self.state.batteryCurrent = 2.0 + math.sin(t * 0.5) * 1.0
        
        # IMU（微小な揺れをシミュレーション）
        self.state.imu.rpy = [
            math.sin(t * 2) * 0.05,  # roll
            math.sin(t * 1.5) * 0.03,  # pitch
            math.sin(t * 0.3) * 0.1,  # yaw
        ]
        self.state.imu.gyroscope = [
            math.cos(t * 2) * 0.1,
            math.cos(t * 1.5) * 0.06,
            math.cos(t * 0.3) * 0.2,
        ]
        self.state.imu.accelerometer = [
            math.sin(t) * 0.5,
            math.cos(t) * 0.3,
            9.81 + math.sin(t * 3) * 0.1,
        ]
        
        # モーター状態
        for i, motor in enumerate(self.state.motors):
            motor.q = math.sin(t + i * 0.5) * 0.3
            motor.dq = math.cos(t + i * 0.5) * 0.2
            motor.temperature = 35 + math.sin(t * 0.1 + i) * 5
            motor.tauEst = math.sin(t * 2 + i) * 2.0
        
        # 足接地状態
        for i, foot in enumerate(self.state.feet):
            foot.contact = (int(t * 2) + i) % 2 == 0
            foot.force = 50 + math.sin(t * 3 + i) * 20 if foot.contact else 0
        
        # 移動速度（コマンドを反映）
        with self._cmdLock:
            self.state.velocity = [
                self._lastMoveCmd.vx,
                self._lastMoveCmd.vy,
                self._lastMoveCmd.vyaw,
            ]
        
        # モード
        self.state.mode = RobotMode.STAND_UP
        self.state.timestamp = t

    def _updateRealState(self) -> None:
        """
        実際のSDKから状態を取得
        """
        try:
            from unitree_sdk2py.idl.unitree_go2.msg.dds_ import SportModeState_
            
            # ここでSDKから状態を取得
            # 実装はSDKのバージョンによって異なる
            pass
            
        except Exception as e:
            print(f"[Go2Client] 状態取得エラー: {e}")

    def _videoLoop(self) -> None:
        """
        映像受信ループ（別スレッドで実行）
        """
        import numpy as np
        
        while self._running:
            try:
                if self._simulationMode:
                    # シミュレーションモードではダミー映像を生成
                    frame = self._generateTestFrame()
                else:
                    # 実際のカメラから映像を取得
                    frame = self._captureRealFrame()
                
                if frame is not None and self._videoCallback:
                    self._videoCallback(frame)
                
                time.sleep(0.033)  # ~30fps
                
            except Exception as e:
                print(f"[Go2Client] 映像受信エラー: {e}")
                time.sleep(0.1)

    def _generateTestFrame(self) -> Any:
        """
        テスト用のダミー映像フレームを生成

        Returns:
            numpy.ndarray: テスト映像フレーム (640x480 RGB)
        """
        import numpy as np
        
        t = time.time()
        width, height = 640, 480
        
        # グラデーション背景
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # サイバーパンク風のグリッドパターン
        gridColor = (0, 255, 255)  # シアン
        for y in range(0, height, 30):
            alpha = int(50 + 30 * math.sin(t + y * 0.01))
            frame[y:y+1, :] = (0, alpha, alpha)
        for x in range(0, width, 30):
            alpha = int(50 + 30 * math.sin(t + x * 0.01))
            frame[:, x:x+1] = (0, alpha, alpha)
        
        # 中央に「SIMULATION」テキスト位置のボックス
        cx, cy = width // 2, height // 2
        boxW, boxH = 200, 40
        frame[cy-boxH//2:cy+boxH//2, cx-boxW//2:cx+boxW//2] = (30, 30, 50)
        
        # 走査線効果
        scanY = int((t * 100) % height)
        frame[scanY:scanY+2, :] = frame[scanY:scanY+2, :] + 50
        
        return frame

    def _captureRealFrame(self) -> Any:
        """
        実際のGo2カメラから映像を取得

        Returns:
            numpy.ndarray: カメラ映像フレーム
        """
        # 実装はSDKのビデオストリーム機能に依存
        return None

