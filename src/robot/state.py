"""
ロボット状態データクラス

Go2のセンサー情報やモーター状態を管理するデータクラス

主な機能:
- IMU（慣性計測装置）データの管理
- 各モーターの状態管理
- ロボット全体の状態統合

制限事項:
- SDK2からのデータ形式に依存
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import IntEnum
import time


class RobotMode(IntEnum):
    """
    ロボットの動作モード

    SDK2のモード定義に基づく
    """
    IDLE = 0          # アイドル状態
    STAND_DOWN = 1    # 伏せ状態
    STAND_UP = 2      # 立ち状態
    WALKING = 3       # 歩行中
    RUNNING = 4       # 走行中
    CLIMBING = 5      # 段差昇降
    UNKNOWN = -1      # 不明


@dataclass
class IMUState:
    """
    IMU（慣性計測装置）の状態

    Attributes:
        quaternion: クォータニオン [w, x, y, z]
        gyroscope: 角速度 [x, y, z] (rad/s)
        accelerometer: 加速度 [x, y, z] (m/s^2)
        rpy: ロール・ピッチ・ヨー角 [roll, pitch, yaw] (rad)
        temperature: センサー温度 (℃)
    """
    quaternion: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0, 0.0])
    gyroscope: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    accelerometer: List[float] = field(default_factory=lambda: [0.0, 0.0, 9.81])
    rpy: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    temperature: float = 25.0

    @property
    def rollDeg(self) -> float:
        """ロール角（度）"""
        import math
        return math.degrees(self.rpy[0])

    @property
    def pitchDeg(self) -> float:
        """ピッチ角（度）"""
        import math
        return math.degrees(self.rpy[1])

    @property
    def yawDeg(self) -> float:
        """ヨー角（度）"""
        import math
        return math.degrees(self.rpy[2])


@dataclass
class MotorState:
    """
    単一モーターの状態

    Attributes:
        motorId: モーターID (0-11)
        mode: モーターモード
        q: 関節角度 (rad)
        dq: 関節角速度 (rad/s)
        ddq: 関節角加速度 (rad/s^2)
        tauEst: 推定トルク (Nm)
        temperature: モーター温度 (℃)
        lost: 通信ロスト状態
    """
    motorId: int = 0
    mode: int = 0
    q: float = 0.0
    dq: float = 0.0
    ddq: float = 0.0
    tauEst: float = 0.0
    temperature: float = 25.0
    lost: bool = False

    @property
    def qDeg(self) -> float:
        """関節角度（度）"""
        import math
        return math.degrees(self.q)


@dataclass
class FootState:
    """
    足の状態

    Attributes:
        footId: 足ID (0: FR, 1: FL, 2: RR, 3: RL)
        contact: 接地状態
        force: 接地力 (N)
    """
    footId: int = 0
    contact: bool = False
    force: float = 0.0


@dataclass
class RobotState:
    """
    ロボット全体の状態

    Go2から受信した全センサー情報を統合管理

    Attributes:
        timestamp: データ取得時刻
        connected: 接続状態
        mode: 動作モード
        batteryLevel: バッテリー残量 (%)
        batteryCurrent: バッテリー電流 (A)
        batteryVoltage: バッテリー電圧 (V)
        imu: IMU状態
        motors: モーター状態リスト (12個)
        feet: 足状態リスト (4個)
        velocity: 現在速度 [vx, vy, vyaw]
        position: 現在位置 [x, y, z]
    """
    timestamp: float = field(default_factory=time.time)
    connected: bool = False
    mode: RobotMode = RobotMode.UNKNOWN
    
    # バッテリー情報
    batteryLevel: int = 0
    batteryCurrent: float = 0.0
    batteryVoltage: float = 0.0
    batteryTemperature: float = 25.0
    
    # IMU
    imu: IMUState = field(default_factory=IMUState)
    
    # モーター (12個: 各足3関節 × 4足)
    motors: List[MotorState] = field(default_factory=lambda: [
        MotorState(motorId=i) for i in range(12)
    ])
    
    # 足状態 (4足: FR, FL, RR, RL)
    feet: List[FootState] = field(default_factory=lambda: [
        FootState(footId=i) for i in range(4)
    ])
    
    # 速度・位置
    velocity: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    
    # エラー状態
    errorCode: int = 0
    errorMessage: str = ""

    def copy(self) -> "RobotState":
        """
        状態のディープコピーを作成

        Returns:
            RobotState: コピーされた状態オブジェクト
        """
        import copy
        return copy.deepcopy(self)

    @property
    def modeStr(self) -> str:
        """動作モードの文字列表現"""
        modeNames = {
            RobotMode.IDLE: "IDLE",
            RobotMode.STAND_DOWN: "DOWN",
            RobotMode.STAND_UP: "STAND",
            RobotMode.WALKING: "WALK",
            RobotMode.RUNNING: "RUN",
            RobotMode.CLIMBING: "CLIMB",
            RobotMode.UNKNOWN: "---",
        }
        return modeNames.get(self.mode, "UNKNOWN")

    @property
    def isHealthy(self) -> bool:
        """ロボットの健全性チェック"""
        # バッテリー低下チェック
        if self.batteryLevel < 10:
            return False
        # エラーコードチェック
        if self.errorCode != 0:
            return False
        # モーター異常チェック
        for motor in self.motors:
            if motor.temperature > 80:  # 80℃以上は異常
                return False
            if motor.lost:
                return False
        return True

